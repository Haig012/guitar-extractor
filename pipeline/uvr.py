"""
UVR post-processing — De-Reverb / De-Crowd via the audio-separator package.

Why a separate module: audio-separator pulls in heavy onnxruntime/torch import
machinery that we want to lazy-load only when the user actually checks one of
the post-process boxes. A single Separator instance is reused across operations
in one pipeline run.

Model discovery: we look for weights in both ``resources/`` (legacy) and
``resources/models/`` (current). The first match wins.
"""
from __future__ import annotations

import os
import traceback
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).parent.parent
MODEL_SEARCH_DIRS = (
    PROJECT_ROOT / "resources" / "models",
    PROJECT_ROOT / "resources",
)

# Filenames audio-separator expects (must match its model_data.json registry).
DEREVERB_MODEL = "UVR-DeEcho-DeReverb.pth"
CROWD_MODEL = "UVR-MDX-NET_Crowd_HQ_1.onnx"


def is_available() -> bool:
    """True if audio-separator can be imported in this environment."""
    try:
        import audio_separator  # noqa: F401
        return True
    except Exception:
        return False


def find_model(model_filename: str) -> Path | None:
    """Return the first existing model path across the search dirs."""
    for d in MODEL_SEARCH_DIRS:
        p = d / model_filename
        if p.is_file():
            return p
    return None


def model_present(model_filename: str) -> bool:
    return find_model(model_filename) is not None


def ensure_ffmpeg_on_path(ffmpeg_path: str | None, log: Callable[[str], None] = lambda _msg: None):
    """
    audio-separator (via librosa.audioread / pydub-like helpers) uses subprocess
    to invoke ffprobe/ffmpeg. If they're not on PATH, every call fails with
    WinError 2 ("system cannot find the file specified"). On Windows the WinGet
    install of FFmpeg lands under a deep package directory that isn't on the
    user's PATH by default, so we splice it in here before the separator runs.
    """
    if not ffmpeg_path or ffmpeg_path == "ffmpeg":
        return
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    if not ffmpeg_dir:
        return
    current = os.environ.get("PATH", "")
    if ffmpeg_dir.lower() in current.lower():
        return
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + current
    log(f"PATH augmented with: {ffmpeg_dir}")

    # Some libraries (pydub) cache ffmpeg location at import time. If pydub is
    # already loaded, point it at the explicit path too — harmless if not.
    try:
        from pydub import AudioSegment  # type: ignore
        ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe.exe")
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
        if os.path.isfile(ffprobe_path):
            AudioSegment.ffprobe = ffprobe_path
    except Exception:
        pass


class UVRProcessor:
    """
    Thin wrapper around audio_separator.separator.Separator.

    Usage:
        uvr = UVRProcessor(use_gpu=True, log=print, ffmpeg_path=...)
        clean, residual = uvr.dereverb("guitar.wav", "out_dir")
    """

    def __init__(
        self,
        use_gpu: bool = True,
        log: Callable[[str], None] | None = None,
        ffmpeg_path: str | None = None,
    ):
        self._use_gpu = use_gpu
        self._log = log or (lambda _msg: None)
        self._separator = None  # built on first use
        self._loaded_model: str | None = None
        ensure_ffmpeg_on_path(ffmpeg_path, self._log)

    # ── Lifecycle ─────────────────────────────────────────────────────────
    def _ensure_separator(self, output_dir: str):
        if self._separator is not None:
            self._separator.output_dir = output_dir
            return
        from audio_separator.separator import Separator
        # Use the deepest existing search dir (so freshly-downloaded weights
        # land in resources/models/ if the user has that layout).
        model_dir = next(
            (str(d) for d in MODEL_SEARCH_DIRS if d.is_dir()),
            str(MODEL_SEARCH_DIRS[0]),
        )
        os.makedirs(model_dir, exist_ok=True)
        self._separator = Separator(
            model_file_dir=model_dir,
            output_dir=output_dir,
            log_level=30,  # WARNING — keep our log clean
            output_format="wav",
        )

    def _load(self, model_filename: str):
        if self._loaded_model == model_filename:
            return
        # If the file lives in a different search dir than the one we set on
        # Separator, copy/symlink isn't necessary — audio-separator searches its
        # own dir, so we point it explicitly at the discovered file when needed.
        located = find_model(model_filename)
        if located is None:
            raise FileNotFoundError(f"Model not found in any search dir: {model_filename}")
        # Configure model_file_dir to where the file actually lives so the
        # registry lookup succeeds without re-downloading.
        if self._separator is not None:
            self._separator.model_file_dir = str(located.parent)
        self._log(f"Loading UVR model: {located}")
        self._separator.load_model(model_filename=model_filename)
        self._loaded_model = model_filename

    # ── Public ops ────────────────────────────────────────────────────────
    def dereverb(self, input_path: str, output_dir: str) -> tuple[str | None, str | None]:
        """Returns (dry_path, reverb_echo_path)."""
        return self._run(
            input_path, output_dir, DEREVERB_MODEL,
            primary_keywords=("no reverb", "noreverb", "no_reverb", "dry"),
            secondary_keywords=("reverb", "echo"),
        )

    def decrowd(self, input_path: str, output_dir: str) -> tuple[str | None, str | None]:
        """Returns (clean_path, crowd_path)."""
        return self._run(
            input_path, output_dir, CROWD_MODEL,
            primary_keywords=("no crowd", "nocrowd", "no_crowd", "other", "instrumental"),
            secondary_keywords=("crowd",),
        )

    # ── Internals ─────────────────────────────────────────────────────────
    def _run(
        self,
        input_path: str,
        output_dir: str,
        model_filename: str,
        primary_keywords: tuple[str, ...],
        secondary_keywords: tuple[str, ...],
    ) -> tuple[str | None, str | None]:
        if not model_present(model_filename):
            self._log(f"⚠ UVR model missing: {model_filename}")
            return None, None
        if not is_available():
            self._log("⚠ audio-separator not installed; run `pip install audio-separator[gpu]`")
            return None, None

        os.makedirs(output_dir, exist_ok=True)
        try:
            self._ensure_separator(output_dir)
            self._load(model_filename)
            outputs = self._separator.separate(input_path)
        except Exception as e:
            # Full traceback so transient bugs (PATH, model registry, CUDA) are
            # diagnosable from the GUI log alone.
            tb = traceback.format_exc()
            self._log(f"⚠ UVR ({model_filename}) failed: {e}")
            for line in tb.rstrip().splitlines():
                self._log(f"    {line}")
            return None, None

        # `outputs` is a list of basenames; resolve to full paths.
        full = [
            p if os.path.isabs(p) else os.path.join(output_dir, os.path.basename(p))
            for p in outputs
        ]
        return _split_outputs(full, primary_keywords, secondary_keywords)


def _split_outputs(
    paths: list[str],
    primary_kw: tuple[str, ...],
    secondary_kw: tuple[str, ...],
) -> tuple[str | None, str | None]:
    """
    Disambiguate two stems: ``"No Reverb"`` contains ``"reverb"``, so naive
    substring matching collapses primary and secondary onto the same file.

    Strategy:
        1. Primary = first path matching any primary_kw.
        2. If exactly 2 outputs, the *other* one is the secondary (regardless
           of keyword match — UVR sometimes labels the residual cryptically).
        3. Otherwise: secondary = first path matching secondary_kw and NOT
           primary_kw.
    """
    def matches(name: str, kws: tuple[str, ...]) -> bool:
        return any(kw.lower() in name for kw in kws)

    lowered = [(p, os.path.basename(p).lower()) for p in paths]

    primary = next((p for p, n in lowered if matches(n, primary_kw)), None)

    if primary and len(paths) == 2:
        secondary = next((p for p in paths if p != primary), None)
        return primary, secondary

    secondary = next(
        (
            p for p, n in lowered
            if p != primary and matches(n, secondary_kw) and not matches(n, primary_kw)
        ),
        None,
    )
    return primary, secondary

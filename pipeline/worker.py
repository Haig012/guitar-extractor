"""
Pipeline worker — runs the guitar-extraction job on a background thread.

Pipeline:
    1. Download (yt-dlp) or copy the local file
    2. Convert to 44.1 kHz stereo WAV
    3. Optional time-range trim
    4. Demucs htdemucs_6s — separates into drums / bass / vocals / piano / other / guitar
    5. Export:
         <song>_guitar.wav      (isolated guitar)
         <song>_no_guitar.wav   (everything else, summed)
       Solo-Time mode: produces one <song>_solo_mix.wav where the guitar is
       only present during the user-chosen segments.
"""
from __future__ import annotations

import glob
import os
import re
import sys
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import librosa
from PySide6.QtCore import QThread, Signal

from utils.helpers import (
    sanitize_cli_filename,
    detect_gpu,
    ensure_dir,
    clean_temp_files,
)
from utils.solo_mask import create_fade_mask, apply_solo_mask
from .uvr import UVRProcessor, is_available as uvr_available, model_present, DEREVERB_MODEL, CROWD_MODEL


SAMPLE_RATE = 44100
STEM_NAMES = ("drums", "bass", "vocals", "piano", "other", "guitar")


class PipelineWorker(QThread):
    progress = Signal(int)           # 0-100
    eta_update = Signal(str)
    log = Signal(str)
    status = Signal(str)
    step_changed = Signal(int, int)  # current_step, total_steps
    pipeline_finished = Signal(dict) # see _build_result for keys
    error = Signal(str, str)         # message, suggested fix

    TOTAL_STEPS = 5

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._cancelled = False
        self._start_time = 0.0
        self._ffmpeg_path: str | None = None  # cached on first lookup

    def cancel(self):
        self._cancelled = True

    # ── Main entry ────────────────────────────────────────────────────────
    def run(self):
        self._start_time = time.time()
        temp_files: list[str] = []

        try:
            cfg = self.config
            export_folder = cfg["export_folder"]
            input_type = cfg["input_type"]          # "youtube" | "file"
            input_value = cfg["input_value"]
            fmt = cfg.get("format", "wav")
            use_gpu = detect_gpu()

            ensure_dir(export_folder)
            final_dir = os.path.join(export_folder, "final_result")
            ensure_dir(final_dir)
            tmp_dir = os.path.join(export_folder, "_tmp")
            ensure_dir(tmp_dir)

            self.log.emit("🚀 GPU detected — using CUDA" if use_gpu else "💻 No GPU — running on CPU")

            # ── Step 1 — get source audio ────────────────────────────
            self._emit_step(1, "Preparing audio…")
            self.progress.emit(5)

            if input_type == "youtube":
                audio_path = self._download_youtube(input_value, tmp_dir, fmt)
            else:
                src = Path(input_value)
                dst = Path(tmp_dir) / sanitize_cli_filename(src.name)
                shutil.copy2(src, dst)
                audio_path = str(dst)
                self.log.emit(f"Using local file: {src.name}")

            temp_files.append(audio_path)
            song_name = sanitize_cli_filename(Path(audio_path).stem)
            self.progress.emit(20)
            if self._cancelled:
                return

            # ── Step 2 — convert / trim ──────────────────────────────
            wav_path = audio_path
            if not audio_path.lower().endswith(".wav"):
                self._emit_step(2, "Converting to WAV…")
                wav_path = os.path.join(tmp_dir, song_name + ".wav")
                self._ffmpeg_convert(audio_path, wav_path)
                temp_files.append(wav_path)

            time_range = cfg.get("time_range")
            if time_range is not None:
                start_s, end_s = time_range
                if start_s > 0 or end_s is not None:
                    self.log.emit(f"Trimming to {start_s:.2f}s → {end_s if end_s else 'end'}")
                    seg_path = os.path.join(tmp_dir, song_name + "_segment.wav")
                    self._ffmpeg_trim(wav_path, seg_path, start_s, end_s)
                    wav_path = seg_path
                    temp_files.append(wav_path)

            self.progress.emit(28)
            if self._cancelled:
                return

            # ── Step 3 — Demucs ──────────────────────────────────────
            self._emit_step(3, "Separating stems with htdemucs_6s…")
            self.eta_update.emit("~5–15 min depending on length")
            demucs_out = os.path.join(tmp_dir, "demucs")
            ensure_dir(demucs_out)
            self._run_demucs(wav_path, demucs_out, use_gpu)

            stems = {name: self._find_stem(demucs_out, name) for name in STEM_NAMES}
            missing = [n for n, p in stems.items() if not p]
            if missing:
                self.error.emit(
                    f"Demucs did not produce stem(s): {', '.join(missing)}.",
                    "Run `pip install -U demucs` and retry.",
                )
                return
            temp_files.append(demucs_out)
            self.progress.emit(65)
            if self._cancelled:
                return

            # ── Step 4 — export ──────────────────────────────────────
            self._emit_step(4, "Mixing and exporting…")

            solo_enabled = cfg.get("solo_time_enabled", False)
            solo_segments = cfg.get("solo_time_segments", []) or []
            result: dict[str, str | None] = {
                "folder": final_dir,
                "guitar": None,
                "no_guitar": None,
                "solo": None,
            }

            if solo_enabled and solo_segments:
                result["solo"] = self._export_solo_mix(
                    stems, solo_segments, time_range, song_name, final_dir,
                )
            else:
                guitar_path = os.path.join(final_dir, f"{song_name}_guitar.wav")
                shutil.copy2(stems["guitar"], guitar_path)
                self.log.emit(f"✅ Guitar stem saved: {guitar_path}")
                result["guitar"] = guitar_path

                no_guitar_path = os.path.join(final_dir, f"{song_name}_no_guitar.wav")
                self.log.emit("Mixing no-guitar backing track…")
                if self._ffmpeg_sum_stems(
                    [stems[n] for n in ("drums", "bass", "vocals", "piano", "other")],
                    no_guitar_path,
                ):
                    self.log.emit(f"✅ Backing track saved: {no_guitar_path}")
                    result["no_guitar"] = no_guitar_path
                else:
                    self.log.emit("⚠ Could not build backing track")

            self.progress.emit(80)
            if self._cancelled:
                return

            # ── Step 5 — optional UVR post-processing ────────────────
            self._run_uvr_post(cfg, result, song_name, final_dir, tmp_dir, use_gpu)

            self.progress.emit(95)

            # ── Cleanup ──────────────────────────────────────────────
            if cfg.get("clean_temp", True):
                self.log.emit("Cleaning temp files…")
                clean_temp_files(temp_files)
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception:
                    pass

            elapsed = int(time.time() - self._start_time)
            self.log.emit(f"⏱  Total time: {_fmt_time(elapsed)}")
            self.progress.emit(100)
            self.eta_update.emit("Done!")
            self.pipeline_finished.emit(result)

        except Exception as e:
            import traceback
            self.log.emit(f"❌ Unexpected error:\n{traceback.format_exc()}")
            self.error.emit(str(e), "Check the log for full details.")

    # ── UVR post-processing ───────────────────────────────────────────────
    def _run_uvr_post(
        self,
        cfg: dict,
        result: dict,
        song_name: str,
        final_dir: str,
        tmp_dir: str,
        use_gpu: bool,
    ):
        do_dereverb = bool(cfg.get("remove_reverb", False))
        do_decrowd = bool(cfg.get("remove_crowd", False))
        if not (do_dereverb or do_decrowd):
            return

        if not uvr_available():
            self.log.emit("⚠ UVR options enabled but `audio-separator` is not installed")
            self.log.emit("   → Install with: pip install audio-separator[gpu]")
            return

        self._emit_step(5, "UVR post-processing…")
        uvr_tmp = os.path.join(tmp_dir, "uvr")
        ensure_dir(uvr_tmp)

        # Hand UVR the ffmpeg path so its subprocess calls (ffprobe via
        # librosa/audioread) can find the binary even when WinGet's deep
        # install dir isn't on the user's PATH.
        ffmpeg_path = self._get_ffmpeg()
        uvr = UVRProcessor(
            use_gpu=use_gpu,
            log=self.log.emit,
            ffmpeg_path=ffmpeg_path if ffmpeg_path != "ffmpeg" else None,
        )

        # Process each output track that exists.
        track_specs = [
            ("guitar",    "guitar"),
            ("no_guitar", "backing"),
            ("solo",      "solo"),
        ]

        for key, label in track_specs:
            src = result.get(key)
            if not src:
                continue

            if do_dereverb and model_present(DEREVERB_MODEL):
                self.log.emit(f"De-reverb on {label}…")
                dry, reverb = uvr.dereverb(src, uvr_tmp)
                if dry:
                    dst = os.path.join(final_dir, f"{song_name}_{label}_dry.wav")
                    shutil.copy2(dry, dst)
                    result[f"{key}_dry"] = dst
                    self.log.emit(f"✅ {dst}")
                if reverb:
                    dst = os.path.join(final_dir, f"{song_name}_{label}_reverb_echo.wav")
                    shutil.copy2(reverb, dst)
                    result[f"{key}_reverb_echo"] = dst
                    self.log.emit(f"✅ {dst}")
            elif do_dereverb:
                self.log.emit(f"⚠ De-reverb requested but {DEREVERB_MODEL} is missing")

            if do_decrowd and model_present(CROWD_MODEL):
                self.log.emit(f"De-crowd on {label}…")
                clean, crowd = uvr.decrowd(src, uvr_tmp)
                if clean:
                    dst = os.path.join(final_dir, f"{song_name}_{label}_clean.wav")
                    shutil.copy2(clean, dst)
                    result[f"{key}_clean"] = dst
                    self.log.emit(f"✅ {dst}")
                if crowd:
                    dst = os.path.join(final_dir, f"{song_name}_{label}_crowd.wav")
                    shutil.copy2(crowd, dst)
                    result[f"{key}_crowd"] = dst
                    self.log.emit(f"✅ {dst}")
            elif do_decrowd:
                self.log.emit(f"⚠ De-crowd requested but {CROWD_MODEL} is missing")

    # ── Solo-time export ──────────────────────────────────────────────────
    def _export_solo_mix(
        self,
        stems: dict[str, str],
        solo_segments: list[tuple[float, float]],
        time_range,
        song_name: str,
        final_dir: str,
    ) -> str:
        """Build a single mix where the guitar is audible only inside the solo windows."""
        self.log.emit("🎸 Solo-Time mode — building masked mix")

        # Convert absolute (original-file) times into relative (trimmed-file) times.
        global_start = time_range[0] if time_range else 0.0
        duration = librosa.get_duration(path=stems["guitar"])
        relative: list[tuple[float, float]] = []
        for s, e in solo_segments:
            rs = max(0.0, s - global_start)
            re_ = min(duration, e - global_start)
            if re_ > rs:
                relative.append((rs, re_))
        self.log.emit(f"Segments (relative): {relative}")

        # Load all six stems as stereo float32.
        loaded = {
            n: librosa.load(stems[n], sr=SAMPLE_RATE, mono=False)[0].astype(np.float32)
            for n in STEM_NAMES
        }
        backing = sum(loaded[n] for n in ("drums", "bass", "vocals", "piano", "other"))
        guitar = loaded["guitar"]

        total_samples = backing.shape[1]
        mask = create_fade_mask(total_samples, relative, sr=SAMPLE_RATE, fade_ms=150)
        output = apply_solo_mask(backing, guitar, mask)

        # Peak-normalise to -1 dB.
        peak = float(np.max(np.abs(output)))
        if peak > 0:
            output = output * (10 ** (-1 / 20)) / peak

        out_path = os.path.join(final_dir, f"{song_name}_solo_mix.wav")
        sf.write(out_path, output.T, SAMPLE_RATE)
        self.log.emit(f"✅ Solo mix saved: {out_path}")
        return out_path

    # ── Subprocess helpers ────────────────────────────────────────────────
    def _emit_step(self, step: int, message: str):
        self.step_changed.emit(step, self.TOTAL_STEPS)
        self.status.emit(message)
        self.log.emit(f"[{step}/{self.TOTAL_STEPS}] {message}")

    def _run_cmd(self, cmd: list, label: str = "") -> subprocess.CompletedProcess:
        self.log.emit(f"$ {' '.join(str(c) for c in cmd)}")
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        lines: list[str] = []
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            lines.append(line)
            self.log.emit(line)
            if "[download]" in line and "%" in line:
                self._parse_ytdlp_progress(line)
        proc.wait()
        return subprocess.CompletedProcess(cmd, proc.returncode, "\n".join(lines), "")

    def _parse_ytdlp_progress(self, line: str):
        eta = re.search(r"ETA\s+([\d:]+)", line)
        pct = re.search(r"(\d+\.?\d*)%", line)
        if eta:
            self.eta_update.emit(eta.group(1))
        if pct:
            try:
                mapped = int(5 + float(pct.group(1)) * 0.15)
                self.progress.emit(min(mapped, 19))
            except ValueError:
                pass

    def _get_ffmpeg(self) -> str:
        """Return absolute ffmpeg.exe path if we can find it, else literal "ffmpeg"."""
        if self._ffmpeg_path is not None:
            return self._ffmpeg_path

        resolved = _find_ffmpeg()
        if resolved:
            self.log.emit(f"✅ FFmpeg: {resolved}")
            self._ffmpeg_path = resolved
        else:
            self.log.emit("⚠ FFmpeg not located on disk — relying on PATH")
            self._ffmpeg_path = "ffmpeg"
        return self._ffmpeg_path

    def _ffmpeg_dir(self) -> str | None:
        """Directory containing ffmpeg.exe (so yt-dlp can find ffprobe alongside)."""
        path = self._get_ffmpeg()
        if path and path != "ffmpeg" and os.path.isfile(path):
            return os.path.dirname(path)
        return None

    def _download_youtube(self, url: str, out_dir: str, fmt: str) -> str:
        template = os.path.join(out_dir, "%(title).200B.%(ext)s")
        fallback = os.path.join(out_dir, "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp", "-f", "bestaudio", "-x",
            "--audio-format", "wav" if fmt == "wav" else fmt,
            "--audio-quality", "0",
            "-o", template,
            "--restrict-filenames", "--no-playlist", "--no-warnings",
        ]
        ffmpeg_dir = self._ffmpeg_dir()
        if ffmpeg_dir:
            # yt-dlp accepts a directory for --ffmpeg-location and finds ffprobe in it too.
            cmd += ["--ffmpeg-location", ffmpeg_dir]
        cmd.append(url)

        r = self._run_cmd(cmd, "yt-dlp")
        if r.returncode != 0:
            self.log.emit("Retrying with fallback filename template…")
            for i, a in enumerate(cmd):
                if a == "-o":
                    cmd[i + 1] = fallback
                    break
            r = self._run_cmd(cmd, "yt-dlp fallback")
            if r.returncode != 0:
                if "ffprobe and ffmpeg not found" in r.stdout:
                    self.error.emit(
                        "FFmpeg is missing.",
                        "Install via `winget install Gyan.FFmpeg` or download from ffmpeg.org",
                    )
                else:
                    self.error.emit(
                        "yt-dlp failed to download the audio.",
                        "Check your internet connection; try `pip install -U yt-dlp`.",
                    )
                raise RuntimeError("yt-dlp failed")

        target_ext = "wav" if fmt == "wav" else fmt
        for f in Path(out_dir).iterdir():
            if f.suffix.lstrip(".").lower() in (target_ext, "wav", "webm", "m4a", "opus", "mp3"):
                safe = sanitize_cli_filename(f.name)
                safe_path = f.parent / safe
                if f.name != safe:
                    try:
                        f.rename(safe_path)
                        f = safe_path
                    except Exception:
                        pass
                return str(f)
        raise FileNotFoundError("Downloaded file not found in output directory")

    def _ffmpeg_convert(self, src: str, dst: str):
        cmd = [self._get_ffmpeg(), "-y", "-i", src, "-ar", str(SAMPLE_RATE), "-ac", "2", dst]
        if self._run_cmd(cmd, "ffmpeg convert").returncode != 0:
            self.error.emit("ffmpeg conversion failed.", "Ensure ffmpeg is on PATH.")
            raise RuntimeError("ffmpeg convert failed")

    def _ffmpeg_trim(self, src: str, dst: str, start_s: float, end_s: float | None):
        cmd = [self._get_ffmpeg(), "-y", "-i", src, "-ss", str(start_s)]
        if end_s is not None:
            cmd += ["-t", str(end_s - start_s)]
        cmd += ["-ar", str(SAMPLE_RATE), "-ac", "2", dst]
        if self._run_cmd(cmd, "ffmpeg trim").returncode != 0:
            self.error.emit("ffmpeg trim failed.", "Check that the time range is valid.")
            raise RuntimeError("ffmpeg trim failed")

    def _run_demucs(self, input_wav: str, out_dir: str, use_gpu: bool):
        cmd = [sys.executable, "-m", "demucs", "-n", "htdemucs_6s", "--out", out_dir]
        if not use_gpu:
            cmd += ["-d", "cpu"]
        cmd.append(input_wav)

        r = self._run_cmd(cmd, "demucs")
        if r.returncode != 0:
            self.log.emit("Retrying demucs…")
            r = self._run_cmd(cmd, "demucs retry")
            if r.returncode != 0:
                self.error.emit(
                    "Demucs stem separation failed.",
                    "Run `pip install -U demucs soundfile` and retry.",
                )
                raise RuntimeError("demucs failed")

    def _ffmpeg_sum_stems(self, input_paths: list[str], output_path: str) -> bool:
        """Sum multiple stems 1:1 (not averaged) — reconstructs full-level mix."""
        if not input_paths:
            return False
        if len(input_paths) == 1:
            shutil.copy2(input_paths[0], output_path)
            return True
        cmd = [self._get_ffmpeg(), "-y"]
        for p in input_paths:
            cmd += ["-i", p]
        n = len(input_paths)
        # weights=1*n gives unity-gain sum (not averaged); normalize=0 keeps amplitudes honest.
        ins = "".join(f"[{i}:a]" for i in range(n))
        weights = " ".join(["1"] * n)
        filt = f"{ins}amix=inputs={n}:duration=longest:normalize=0:weights={weights}[aout]"
        cmd += [
            "-filter_complex", filt,
            "-map", "[aout]",
            "-ar", str(SAMPLE_RATE),
            "-ac", "2",
            output_path,
        ]
        return self._run_cmd(cmd, "ffmpeg mix").returncode == 0

    def _find_stem(self, search_dir: str, stem_name: str) -> str | None:
        pat = re.compile(rf"(^|_){re.escape(stem_name)}\.(wav|mp3|flac)$", re.IGNORECASE)
        for root, _d, files in os.walk(search_dir):
            for f in sorted(files):
                fl = f.lower()
                if stem_name == "vocals" and "no_vocals" in fl:
                    continue
                if stem_name == "other" and "not_other" in fl:
                    continue
                if pat.search(fl):
                    return os.path.join(root, f)
        return None


def _find_ffmpeg() -> str | None:
    """
    Locate ffmpeg.exe robustly on Windows.

    Searches (in order): PATH, common static install locations, WinGet's
    Gyan.FFmpeg package directory, WinGet's Links shim folder, and Chocolatey.
    Returns the absolute path or None.
    """
    # 1. Whatever the current process can see on PATH.
    found = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if found:
        return os.path.abspath(found)

    # 2. Hardcoded common install locations.
    static_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
    ]
    for p in static_paths:
        if os.path.isfile(p):
            return p

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        # 3. WinGet "Links" shim (newer winget aliases).
        link = os.path.join(local_appdata, "Microsoft", "WinGet", "Links", "ffmpeg.exe")
        if os.path.isfile(link):
            return link

        # 4. Direct WinGet package install — Gyan.FFmpeg drops ffmpeg.exe deep
        #    inside Packages\Gyan.FFmpeg_*\ffmpeg-<ver>\bin\ffmpeg.exe.
        pkg_glob = os.path.join(
            local_appdata, "Microsoft", "WinGet", "Packages",
            "Gyan.FFmpeg*", "**", "bin", "ffmpeg.exe",
        )
        matches = glob.glob(pkg_glob, recursive=True)
        if matches:
            # Prefer the highest-versioned match.
            return sorted(matches)[-1]

    # 5. Last resort: ask the OS.
    try:
        out = subprocess.check_output(
            ["where.exe", "ffmpeg.exe"], text=True, stderr=subprocess.DEVNULL,
        ).strip().splitlines()
        if out:
            return out[0]
    except Exception:
        pass

    return None


def _fmt_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m {s:02d}s"

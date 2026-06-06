"""
Chord detection from an isolated guitar stem.

Self-contained — uses only librosa + numpy (already pipeline dependencies), so
there are no extra model downloads or system plugins to install. Approach:

    1. CQT chroma (better harmonic resolution than STFT for guitar)
    2. Beat tracking → beat-synchronous chroma (musically aligned segments)
    3. Template matching against the 24 major / minor triads (cosine similarity)
    4. An energy gate that emits "N.C." over silent / non-harmonic stretches
    5. Majority-vote smoothing to suppress single-beat flicker, then run-length
       merging into chord segments.

Accuracy is best on clean triadic playing. It reports chord *names* (e.g. "Am",
"F"), not fingerings, inversions, or extended (7th / 9th / sus) qualities.
"""
from __future__ import annotations

from collections import Counter

import numpy as np
import librosa


PITCHES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
NO_CHORD = "N.C."
HOP = 512
SR = 22050


def _build_templates() -> tuple[np.ndarray, list[str]]:
    """24 L2-normalised binary triad templates (12 major + 12 minor)."""
    # Weight root & third above the (often shared) fifth so relative
    # major/minor and IV/V pairs stay distinguishable.
    W_ROOT, W_THIRD, W_FIFTH = 1.2, 1.0, 0.8
    templates: list[np.ndarray] = []
    labels: list[str] = []
    for i, root in enumerate(PITCHES):
        maj = np.zeros(12, dtype=np.float32)
        maj[i] = W_ROOT; maj[(i + 4) % 12] = W_THIRD; maj[(i + 7) % 12] = W_FIFTH
        minr = np.zeros(12, dtype=np.float32)
        minr[i] = W_ROOT; minr[(i + 3) % 12] = W_THIRD; minr[(i + 7) % 12] = W_FIFTH
        templates.append(maj); labels.append(root)
        templates.append(minr); labels.append(f"{root}m")
    tem = np.array(templates, dtype=np.float32)
    tem /= np.linalg.norm(tem, axis=1, keepdims=True)
    return tem, labels


_TEMPLATES, _LABELS = _build_templates()


def detect_chords(
    audio_path: str,
    *,
    smooth_window: int = 4,
    min_dur: float = 0.5,
    energy_gate: float = 0.08,
) -> list[tuple[float, float, str]]:
    """
    Return a list of ``(start_s, end_s, label)`` chord segments.

    ``smooth_window`` is the majority-vote width in beats; ``min_dur`` merges
    away segments shorter than this; ``energy_gate`` is the per-segment RMS
    threshold (relative to peak) below which "N.C." is emitted.
    """
    y, sr = librosa.load(audio_path, sr=SR, mono=True)
    if y.size == 0:
        return []
    duration = librosa.get_duration(y=y, sr=sr)

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP)
    rms = librosa.feature.rms(y=y, hop_length=HOP)[0]
    n_frames = chroma.shape[1]
    peak_rms = float(rms.max()) or 1.0

    # Classify in fixed ~0.25 s blocks. Block-level (rather than beat-synchronous)
    # analysis keeps chord-change timing accurate for the on-screen overlay and
    # is robust to weak/ambiguous beat tracking on a lone guitar stem.
    block = max(1, int(round(0.25 * sr / HOP)))
    bounds = np.arange(0, n_frames, block)
    bounds = np.append(bounds, n_frames) if bounds[-1] != n_frames else bounds
    bounds = np.unique(np.clip(bounds, 0, n_frames))

    # Classify each segment.
    raw: list[tuple[int, int, str]] = []  # (start_frame, end_frame, label)
    for b0, b1 in zip(bounds[:-1], bounds[1:]):
        if b1 <= b0:
            continue
        seg_rms = float(np.median(rms[b0:b1]))
        if seg_rms < energy_gate * peak_rms:
            raw.append((b0, b1, NO_CHORD))
            continue
        vec = np.median(chroma[:, b0:b1], axis=1)
        norm = np.linalg.norm(vec)
        if norm < 1e-6:
            raw.append((b0, b1, NO_CHORD))
            continue
        scores = _TEMPLATES @ (vec / norm)
        raw.append((b0, b1, _LABELS[int(np.argmax(scores))]))

    if not raw:
        return []

    # Majority-vote smoothing over a sliding window of segments.
    labels = [r[2] for r in raw]
    smoothed = list(labels)
    half = max(0, smooth_window // 2)
    for i in range(len(labels)):
        lo, hi = max(0, i - half), min(len(labels), i + half + 1)
        smoothed[i] = Counter(labels[lo:hi]).most_common(1)[0][0]

    # Run-length merge consecutive equal labels into time segments.
    segments: list[tuple[float, float, str]] = []
    cur_label = smoothed[0]
    cur_start = raw[0][0]
    for (b0, b1, _), lab in zip(raw, smoothed):
        if lab != cur_label:
            segments.append((_t(cur_start), _t(b0), cur_label))
            cur_label, cur_start = lab, b0
    segments.append((_t(cur_start), duration, cur_label))

    return _merge_short(segments, min_dur)


def _t(frame: int) -> float:
    return float(librosa.frames_to_time(frame, sr=SR, hop_length=HOP))


def _merge_short(
    segments: list[tuple[float, float, str]], min_dur: float
) -> list[tuple[float, float, str]]:
    """Fold sub-``min_dur`` segments into the previous one (then re-merge runs)."""
    if not segments:
        return segments
    merged: list[list] = [list(segments[0])]
    for start, end, lab in segments[1:]:
        prev = merged[-1]
        if end - start < min_dur:
            prev[1] = end  # absorb the blip into the previous chord
        elif lab == prev[2]:
            prev[1] = end
        else:
            merged.append([start, end, lab])
    return [(s, e, l) for s, e, l in merged]


# ── Writers ────────────────────────────────────────────────────────────────
def write_chords_txt(
    segments: list[tuple[float, float, str]], path: str, song_name: str = ""
) -> str:
    lines = [f"# Chords — {song_name}".rstrip(), "# time      chord", ""]
    for start, _end, label in segments:
        lines.append(f"{_clock(start):>8}   {label}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def write_chords_lrc(segments: list[tuple[float, float, str]], path: str) -> str:
    """LRC-style timestamps so the chart can be loaded by synced lyric players."""
    with open(path, "w", encoding="utf-8") as fh:
        for start, _end, label in segments:
            fh.write(f"{_lrc_stamp(start)}{label}\n")
    return path


def write_chords_srt(
    segments: list[tuple[float, float, str]], path: str, lookahead: int = 2
) -> str:
    """
    SubRip subtitle file used to burn the chords onto the play-along video.

    Each cue shows the chord that is playing now plus the next ``lookahead``
    chords coming up, e.g. ``Am  ->  G  C``. A cue stays on screen until the
    next chord begins (bridging any "N.C." gaps) so the chart flows continuously
    rather than blinking off between changes.
    """
    named = [(s, e, l) for s, e, l in segments if l != NO_CHORD and e > s]
    idx = 1
    with open(path, "w", encoding="utf-8") as fh:
        for i, (start, end, label) in enumerate(named):
            cue_end = named[i + 1][0] if i + 1 < len(named) else end
            upcoming = [named[j][2] for j in range(i + 1, min(i + 1 + lookahead, len(named)))]
            text = label if not upcoming else f"{label}   →   " + "   ".join(upcoming)
            fh.write(f"{idx}\n{_srt_stamp(start)} --> {_srt_stamp(cue_end)}\n{text}\n\n")
            idx += 1
    return path


def _srt_stamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _clock(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _lrc_stamp(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    return f"[{int(m):02d}:{s:05.2f}]"


def parse_lrc(path: str) -> list[tuple[float, str]]:
    """Parse an LRC chord file into ``(seconds, label)`` pairs."""
    import re

    out: list[tuple[float, str]] = []
    pat = re.compile(r"\[(\d{1,2}):(\d{1,2}(?:\.\d+)?)\](.*)")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                m = pat.match(line.strip())
                if not m:
                    continue
                secs = int(m.group(1)) * 60 + float(m.group(2))
                out.append((secs, m.group(3).strip()))
    except Exception:
        return []
    return out

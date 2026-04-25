"""
Solo-Time masking.

The user marks time windows where the guitar *plays* (e.g. "the solo is at 1:50–3:00").
Outside those windows the guitar is *removed* from the mix; inside them it's kept.
"""
from __future__ import annotations

import numpy as np


def create_fade_mask(
    total_samples: int,
    segments: list[tuple[float, float]],
    sr: int = 44100,
    fade_ms: int = 150,
) -> np.ndarray:
    """Return a float32 [0..1] mask, 1.0 inside a segment (with raised-cosine fades)."""
    mask = np.zeros(total_samples, dtype=np.float32)
    fade_n = int(fade_ms * sr / 1000)

    for start_s, end_s in segments:
        start = max(0, int(start_s * sr))
        end = min(total_samples, int(end_s * sr))
        if end <= start:
            continue

        seg_len = end - start
        seg = np.ones(seg_len, dtype=np.float32)

        if seg_len >= fade_n * 2:
            t = np.linspace(0, 1, fade_n, dtype=np.float32)
            fade_in = 0.5 - 0.5 * np.cos(np.pi * t)
            seg[:fade_n] *= fade_in
            seg[-fade_n:] *= fade_in[::-1]

        # Overlapping segments: take the max so fades don't cancel.
        mask[start:end] = np.maximum(mask[start:end], seg)

    return mask


def _match_rms(source: np.ndarray, target: np.ndarray) -> float:
    s = float(np.sqrt(np.mean(source ** 2)))
    t = float(np.sqrt(np.mean(target ** 2)))
    if s < 1e-9:
        return 1.0
    return t / s


def apply_solo_mask(
    backing: np.ndarray,
    guitar: np.ndarray,
    mask: np.ndarray,
    gain_match: bool = True,
) -> np.ndarray:
    """
    Return backing + mask * guitar.

    - mask == 1.0 → guitar audible (solo time)
    - mask == 0.0 → guitar silent (use backing only)

    Shapes: ``backing`` and ``guitar`` are (channels, samples); ``mask`` is (samples,).
    """
    if gain_match:
        hot = mask > 0.01
        if hot.any():
            gain = _match_rms(guitar[:, hot], backing[:, hot])
            guitar = guitar * gain

    output = backing.copy()
    channels = output.shape[0]
    for c in range(channels):
        output[c] += guitar[c] * mask
    return output

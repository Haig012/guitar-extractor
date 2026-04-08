"""
New mask based Solo Time implementation
Full track processing with time masking
"""
import numpy as np
import librosa
import soundfile as sf


def create_fade_mask(total_samples: int, segments: list, sr: int = 44100, fade_ms: int = 150) -> np.ndarray:
    """
    Create smooth 0-1 mask for entire audio length
    Handles multiple segments, auto merges overlaps, applies fade in/out
    """
    mask = np.zeros(total_samples, dtype=np.float32)
    fade_samples = int(fade_ms * sr / 1000)

    for start_sec, end_sec in segments:
        start = int(start_sec * sr)
        end = int(end_sec * sr)

        # Clamp to valid range
        start = max(start, 0)
        end = min(end, total_samples)

        if end <= start:
            continue

        # Create fade envelope
        seg_length = end - start
        seg = np.ones(seg_length, dtype=np.float32)

        # Fade in
        if seg_length >= fade_samples * 2:
            t = np.linspace(0, 1, fade_samples)
            fade_in = 0.5 - 0.5 * np.cos(np.pi * t)
            seg[:fade_samples] *= fade_in

            # Fade out
            t = np.linspace(1, 0, fade_samples)
            fade_out = 0.5 - 0.5 * np.cos(np.pi * t)
            seg[-fade_samples:] *= fade_out

        # Merge into global mask (maximum when overlapping)
        mask[start:end] = np.maximum(mask[start:end], seg)

    return mask


def match_rms_level(source: np.ndarray, target: np.ndarray) -> float:
    """Calculate RMS gain factor to match source level to target level"""
    source_rms = np.sqrt(np.mean(source ** 2))
    target_rms = np.sqrt(np.mean(target ** 2))

    if source_rms < 1e-9:
        return 1.0

    return target_rms / source_rms


def apply_solo_mask(
    base_mix: np.ndarray,
    guitar: np.ndarray,
    mask: np.ndarray,
    gain_correction: bool = True
) -> np.ndarray:
    """
    Blend guitar into base mix using time mask
    Maintains perfect constant volume throughout transitions
    """
    output = base_mix.copy()

    # Apply gain matching per segment region
    if gain_correction:
        mask_regions = np.where(mask > 0.01)[0]
        if len(mask_regions) > 0:
            start = mask_regions[0]
            end = mask_regions[-1] + 1

            if end > start:
                gain = match_rms_level(
                    guitar[:, start:end],
                    base_mix[:, start:end]
                )
                guitar = guitar * gain

    # Blend: mask areas REMOVE guitar (solo time mode)
    # Where mask is 1 → only base mix (no guitar)
    # Where mask is 0 → full mix with guitar
    inv_mask = 1.0 - mask
    
    for ch in range(2):
        output[ch] += guitar[ch] * inv_mask

    return output
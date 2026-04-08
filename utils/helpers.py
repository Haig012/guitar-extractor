"""
Utility helpers: filename sanitization, GPU detection, path helpers
"""
import re
import os
import subprocess
import sys
import shutil
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Remove illegal characters from filename."""
    # Remove characters not allowed in Windows filenames
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    # Limit length
    if len(name) > 200:
        name = name[:200]
    return name or "output"

def sanitize_cli_filename(name: str) -> str:
    """Create ASCII-safe filename for subprocess tools on Windows consoles."""
    base = sanitize_filename(name)
    base = base.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"\s+", " ", base).strip()
    base = base.replace(" ", "_")
    if len(base) > 200:
        base = base[:200]
    return base or "audio"


def detect_gpu() -> bool:
    """Check if CUDA GPU is available via torch."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        pass
    # Fallback: check nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def is_valid_youtube_url(url: str) -> bool:
    """Validate YouTube URL format."""
    url = url.strip()
    patterns = [
        r'(https?://)?(www\.)?(youtube\.com/watch\?v=[\w-]+)',
        r'(https?://)?(youtu\.be/[\w-]+)',
        r'(https?://)?(www\.)?(youtube\.com/shorts/[\w-]+)',
        r'(https?://)?(music\.youtube\.com/watch\?v=[\w-]+)',
    ]
    for pattern in patterns:
        if re.match(pattern, url):
            return True
    return False


def check_dependency(name: str) -> tuple[bool, str]:
    """
    Check if a dependency is available.
    Returns (found: bool, version_or_path: str)
    """
    checks = {
        "yt-dlp": _check_ytdlp,
        "demucs": _check_demucs,
        "deepfilternet": _check_deepfilter,
        "soundfile": _check_soundfile,
        "ffmpeg": _check_ffmpeg,
    }
    fn = checks.get(name)
    if fn:
        return fn()
    return False, ""


def _check_ytdlp():
    try:
        result = subprocess.run(
            ["yt-dlp", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    # Try as python module
    try:
        import yt_dlp
        return True, getattr(yt_dlp, '__version__', 'installed')
    except ImportError:
        pass
    return False, ""


def _check_demucs():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "demucs", "--help"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return True, "installed"
    except Exception:
        pass
    try:
        import demucs
        return True, getattr(demucs, '__version__', 'installed')
    except ImportError:
        pass
    return False, ""


def _check_deepfilter():
    try:
        result = subprocess.run(
            ["deep-filter", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    except Exception:
        pass

    for module_name in ["df", "deepfilternet", "deepfilternet.cli"]:
        try:
            __import__(module_name)
            return True, "installed"
        except ImportError:
            continue

    return False, ""


def _check_soundfile():
    try:
        import soundfile
        return True, getattr(soundfile, '__version__', 'installed')
    except ImportError:
        return False, ""


def _check_ffmpeg():
    if shutil.which("ffmpeg"):
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True, text=True, timeout=10
            )
            # Extract version from first line
            first_line = result.stdout.split('\n')[0]
            return True, first_line[:60]
        except Exception:
            return True, "found"
    return False, ""

def ensure_dir(path: str) -> str:
    """Create directory if it doesn't exist, return path."""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def clean_temp_files(paths: list):
    """Remove a list of temporary files/directories."""
    for p in paths:
        try:
            p = Path(p)
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                import shutil
                shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass


def split_audio_segments(input_wav: str, segments: list, tmp_dir: str) -> list:
    """
    Split audio file into multiple segments.
    Returns list of segment paths with type indicator.
    """
    import librosa
    import soundfile as sf
    import numpy as np
    
    audio, sr = librosa.load(input_wav, sr=44100, mono=False)
    duration = audio.shape[1] / sr
    
    # Add margin for crossfades (300ms each side) so transitions don't cut off
    CROSSFADE_MARGIN = 0.300
    
    # Sort segments by start time
    sorted_segments = sorted(segments, key=lambda x: x[0])
    
    output_segments = []
    last_end = 0.0
    
    # Add original segments and solo segments
    for start, end in sorted_segments:
        if start > last_end:
            # Add original segment WITH extra margin at end for crossfade
            orig_end = min(start + CROSSFADE_MARGIN, duration)
            orig_samples = audio[:, int(last_end * sr):int(orig_end * sr)]
            orig_path = os.path.join(tmp_dir, f"orig_{last_end:.2f}_{start:.2f}.wav")
            sf.write(orig_path, orig_samples.T, sr)
            output_segments.append({
                "type": "original",
                "path": orig_path,
                "start": last_end,
                "end": start,
                "actual_end": orig_end
            })
        
        # Add solo segment WITH extra margin on BOTH sides for crossfade
        solo_start = max(0.0, start - CROSSFADE_MARGIN)
        solo_end = min(end + CROSSFADE_MARGIN, duration)
        solo_samples = audio[:, int(solo_start * sr):int(solo_end * sr)]
        solo_path = os.path.join(tmp_dir, f"solo_{start:.2f}_{end:.2f}.wav")
        sf.write(solo_path, solo_samples.T, sr)
        output_segments.append({
            "type": "solo",
            "path": solo_path,
            "start": start,
            "end": end,
            "actual_start": solo_start,
            "actual_end": solo_end
        })
        
        last_end = end
    
    # Add final original segment if needed
    if last_end < duration:
        # Add margin at start for crossfade
        orig_start = max(0.0, last_end - CROSSFADE_MARGIN)
        orig_samples = audio[:, int(orig_start * sr):]
        orig_path = os.path.join(tmp_dir, f"orig_{last_end:.2f}_end.wav")
        sf.write(orig_path, orig_samples.T, sr)
        output_segments.append({
            "type": "original",
            "path": orig_path,
            "start": last_end,
            "end": duration,
            "actual_start": orig_start
        })
    
    return output_segments


def apply_gain_match(source_wav: str, target_wav: str, output_wav: str = None) -> str:
    """Match RMS level of source to target."""
    import librosa
    import soundfile as sf
    import numpy as np
    
    if output_wav is None:
        output_wav = source_wav
    
    source, sr = librosa.load(source_wav, sr=44100, mono=False)
    target, _ = librosa.load(target_wav, sr=44100, mono=False)
    
    # Calculate RMS
    source_rms = np.sqrt(np.mean(source ** 2))
    target_rms = np.sqrt(np.mean(target ** 2))
    
    # Apply gain
    if source_rms > 0:
        gain = target_rms / source_rms
        source = source * gain
    
    sf.write(output_wav, source.T, sr)
    return output_wav


def smart_blend(segments: list, output_wav: str, fade_ms: int = 300) -> str:
    """
    Merge segments with smooth equal power crossfade transitions.
    Crossfade is perfectly centered on the user's selected boundary point.
    Uses cosine square root crossfade for constant equal loudness.
    """
    import soundfile as sf
    import numpy as np
    
    sr = 44100
    fade_samples = int(fade_ms * sr / 1000)
    half_fade = fade_samples // 2
    
    # Calculate total length from logical segment boundaries
    total_samples = int(segments[-1]["end"] * sr)
    
    full_audio = np.zeros((2, total_samples), dtype=np.float32)
    
    for seg in segments:
        audio, _ = sf.read(seg["path"])
        audio = audio.T
        
        # Calculate exact boundary position - this is the exact time user selected
        boundary_samples = int(seg["start"] * sr)
        
        # Small gentle 80ms pre-lead so solo starts slightly before boundary
        PRE_OFFSET = int(0.080 * sr)
        boundary_samples = max(boundary_samples - PRE_OFFSET, 0)
        
        # Crossfade starts HALF before the boundary, ends HALF after the boundary
        crossfade_start = boundary_samples - half_fade
        
        # Place segment so crossfade perfectly centers on boundary
        if "actual_start" in seg:
            offset = int((seg["start"] - seg["actual_start"]) * sr)
            pos_samples = crossfade_start - offset
        else:
            pos_samples = crossfade_start
        
        seg_len = audio.shape[1]
        # Clamp position to valid array bounds to prevent negative indices
        pos_samples = max(pos_samples, 0)
        end_pos = min(pos_samples + seg_len, total_samples)
        
        # Only apply crossfade if not first segment
        if fade_samples > 0 and pos_samples > 0:
            # Clamp crossfade window to valid array bounds
            cf_start = max(crossfade_start, 0)
            cf_end = min(crossfade_start + fade_samples, total_samples)
            actual_fade = cf_end - cf_start
            
            if actual_fade > 0:
                # Optimized raised cosine crossfade - perfectly smooth constant volume
                t = np.linspace(0, 1, actual_fade)
                fade_in = 0.5 - 0.5 * np.cos(np.pi * t)
                fade_out = 1.0 - fade_in
                
                # Fade in the NEW segment
                audio[:, :actual_fade] *= fade_in
                
                # Fade out the EXISTING audio over exact crossfade window
                full_audio[:, cf_start:cf_end] *= fade_out
                
                # Overlap add at the exact crossfade position
                full_audio[:, cf_start:cf_end] += audio[:, :actual_fade]
            
            # Write remaining audio after crossfade
            remaining_start = max(crossfade_start + fade_samples, 0)
            if remaining_start < end_pos:
                src_offset = max(fade_samples - max(0, crossfade_start), 0)
                dst_len = end_pos - remaining_start
                full_audio[:, remaining_start:end_pos] = audio[:, src_offset:src_offset + dst_len]
        else:
            # First segment: write directly
            write_len = end_pos - pos_samples
            if write_len > 0:
                full_audio[:, pos_samples:end_pos] = audio[:, :write_len]
    
    # Normalize final audio to -1dB peak
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        max_peak = 10 ** (-1 / 20)  # -1 dB
        full_audio = full_audio * max_peak / peak
    
    sf.write(output_wav, full_audio.T, sr)
    return output_wav

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

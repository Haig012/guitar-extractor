"""
Shared helpers: filename safety, GPU probe, path utilities.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path


# ── Filenames ────────────────────────────────────────────────────────────
def sanitize_filename(name: str) -> str:
    """Remove characters illegal in Windows filenames."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip(". ")
    if len(name) > 200:
        name = name[:200]
    return name or "output"


def sanitize_cli_filename(name: str) -> str:
    """ASCII-safe filename for subprocess tools on Windows consoles."""
    base = sanitize_filename(name)
    base = base.encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"\s+", " ", base).strip().replace(" ", "_")
    if len(base) > 200:
        base = base[:200]
    return base or "audio"


# ── GPU ──────────────────────────────────────────────────────────────────
def detect_gpu() -> bool:
    """True if a CUDA-capable GPU is available via torch, with nvidia-smi fallback."""
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        pass
    try:
        return subprocess.run(["nvidia-smi"], capture_output=True, timeout=5).returncode == 0
    except Exception:
        return False


# ── URL validation ───────────────────────────────────────────────────────
_YT_PATTERNS = (
    r"(https?://)?(www\.)?(youtube\.com/watch\?v=[\w-]+)",
    r"(https?://)?(youtu\.be/[\w-]+)",
    r"(https?://)?(www\.)?(youtube\.com/shorts/[\w-]+)",
    r"(https?://)?(music\.youtube\.com/watch\?v=[\w-]+)",
)


def is_valid_youtube_url(url: str) -> bool:
    url = (url or "").strip()
    return any(re.match(p, url) for p in _YT_PATTERNS)


# ── Paths ────────────────────────────────────────────────────────────────
def ensure_dir(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def clean_temp_files(paths: list):
    for p in paths:
        try:
            pp = Path(p)
            if pp.is_file():
                pp.unlink()
            elif pp.is_dir():
                shutil.rmtree(pp, ignore_errors=True)
        except Exception:
            pass

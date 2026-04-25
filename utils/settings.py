"""
JSON-backed user settings.
"""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS_FILE = Path.home() / ".guitar_extractor" / "settings.json"

DEFAULTS: dict = {
    "language": "en",
    "export_folder": str(Path.home() / "Desktop" / "exported_files"),
    "format": "wav",
    "last_input": "",
    "last_input_type": "youtube",
    "auto_open_output": True,
    "clean_temp": True,
    "last_time_range_start": "",
    "last_time_range_end": "",
    "remove_reverb": False,
    "remove_crowd": False,
}


def _ensure_dir():
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    _ensure_dir()
    data = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data.update(json.load(f))
        except Exception:
            pass
    return data


def save_settings(settings: dict):
    _ensure_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

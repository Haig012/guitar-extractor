"""
Settings and recent files management (JSON-backed)
"""
import json
import os
from datetime import datetime
from pathlib import Path

SETTINGS_FILE = Path.home() / ".guitar_extractor" / "settings.json"
RECENT_FILE = Path.home() / ".guitar_extractor" / "recent.json"
MAX_RECENT = 7


def _ensure_dir():
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    _ensure_dir()
    defaults = {
        "language": "en",
        "export_folder": str(Path.home() / "Desktop" / "exported_files"),
        "format": "wav",
        "last_input": "",
        "last_input_type": "youtube",
        "auto_open_output": True,
        "clean_temp": True,
        "theme": "dark",
        "last_time_range": "",
        "remove_crowd": False,
        "remove_reverb": False,
        "crowd_mode": "remove",
    }
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_settings(settings: dict):
    _ensure_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def load_recent() -> list:
    _ensure_dir()
    if RECENT_FILE.exists():
        try:
            with open(RECENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_recent(items: list):
    _ensure_dir()
    with open(RECENT_FILE, "w", encoding="utf-8") as f:
        json.dump(items[:MAX_RECENT], f, indent=2, ensure_ascii=False)


def add_recent(filepath: str):
    items = load_recent()
    # Remove if already exists
    items = [i for i in items if i.get("path") != filepath]
    items.insert(0, {
        "path": filepath,
        "name": os.path.basename(filepath),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_recent(items[:MAX_RECENT])


def clear_recent():
    save_recent([])

"""
Dependency check worker — runs in a background thread
"""
import subprocess
import sys
from PySide6.QtCore import QThread, Signal
from utils.helpers import check_dependency

DEPENDENCIES = ["yt-dlp", "demucs", "soundfile", "ffmpeg"]

INSTALL_COMMANDS = {
    "yt-dlp": "pip install yt-dlp",
    "demucs": "pip install demucs",
    "soundfile": "pip install soundfile",
    "ffmpeg": "winget install Gyan.FFmpeg",
}


class DepCheckWorker(QThread):
    result = Signal(str, bool, str)   # dep_name, found, version
    all_done = Signal(list)           # list of (name, found, version)

    def run(self):
        results = []
        for dep in DEPENDENCIES:
            found, version = check_dependency(dep)
            self.result.emit(dep, found, version)
            results.append((dep, found, version))
        self.all_done.emit(results)


class AutoInstallWorker(QThread):
    log = Signal(str)
    finished = Signal()

    def __init__(self, missing: list):
        super().__init__()
        self.missing = missing

    def run(self):
        for dep in self.missing:
            cmd = INSTALL_COMMANDS.get(dep)
            if not cmd or dep == "ffmpeg":
                self.log.emit(f"⚠ Cannot auto-install {dep}. Please install manually.")
                if dep == "ffmpeg":
                    self.log.emit("  → Download from: https://ffmpeg.org/download.html")
                continue

            self.log.emit(f"Installing {dep}...")
            try:
                pip_cmd = [sys.executable, "-m"] + cmd.split()[1:]  # pip install ...
                result = subprocess.run(
                    pip_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    self.log.emit(f"✅ {dep} installed successfully")
                else:
                    self.log.emit(f"❌ Failed to install {dep}:\n{result.stderr[:300]}")
            except Exception as e:
                self.log.emit(f"❌ Error installing {dep}: {e}")

        self.finished.emit()

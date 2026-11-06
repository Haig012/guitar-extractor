"""
Guitar Extractor — entry point.
Made by Hai Guriel.
"""
from __future__ import annotations

import ctypes
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from gui.icons import LOGO_ICO
from gui.main_window import MainWindow


def main():
    if sys.platform == "win32":
        # Without this the taskbar groups the app under python.exe and its icon.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "HaiGuriel.GuitarExtractor"
        )
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Guitar Extractor")
    app.setOrganizationName("Hai Guriel")
    app.setApplicationVersion("2.0.0")
    app.setFont(QFont("Segoe UI", 10))
    app.setWindowIcon(QIcon(str(LOGO_ICO)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""Regenerate the raster logo assets from gui/assets/*.svg.

Run with the app's Python:  .venv\Scripts\python.exe tools\build_logo.py
Sizes of 32px and below use the simplified logo_small.svg, which stays legible
in the taskbar and title bar; larger sizes use the full logo.svg.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).resolve().parent.parent / "gui" / "assets"
ICO_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def render(size: int) -> Image.Image:
    svg = "logo_small.svg" if size <= 32 else "logo.svg"
    # Draw at 4x and let Pillow downsample: QtSvg's own AA is rough at icon sizes.
    scale = 4
    img = QImage(size * scale, size * scale, QImage.Format_RGBA8888)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(str(ASSETS / svg)).render(painter)
    painter.end()
    raw = bytes(img.constBits())
    big = Image.frombytes("RGBA", (img.width(), img.height()), raw)
    return big.resize((size, size), Image.LANCZOS)


def main() -> None:
    app = QGuiApplication(sys.argv)  # noqa: F841 - QtSvg needs a GUI app
    frames = [render(s) for s in ICO_SIZES]
    frames[-1].save(ASSETS / "logo.png")
    frames[-1].save(
        ASSETS / "app.ico",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=frames[:-1],
    )
    print("wrote", ASSETS / "logo.png", "and", ASSETS / "app.ico")


if __name__ == "__main__":
    main()

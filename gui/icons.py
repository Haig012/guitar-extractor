"""
Vector UI icons and the app logo, tinted and rasterised on demand.

Emoji render differently per machine (and flags not at all on Windows), so every
glyph in the UI comes from here.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QLabel
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_ICO = ASSETS / "app.ico"
LOGO_SVG = ASSETS / "logo.svg"

_STROKE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
    'stroke-linejoin="round">{body}</svg>'
)
_FILL = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="{color}">{body}</svg>'
)

_ICONS = {
    "folder": (_STROKE, '<path d="M3 7a2 2 0 0 1 2-2h4l2 2.5h8a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>'),
    "file": (_STROKE, '<path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/>'),
    "close": (_STROKE, '<path d="M6 6l12 12M18 6L6 18"/>'),
    "plus": (_STROKE, '<path d="M12 5v14M5 12h14"/>'),
    "log": (_STROKE, '<path d="M4 6h16M4 12h16M4 18h10"/>'),
    "volume": (_STROKE, '<path d="M4 10v4h3.5L12 18V6L7.5 10Z"/><path d="M16 9a4 4 0 0 1 0 6"/>'),
    "play": (_FILL, '<path d="M7 4.6v14.8c0 .8.9 1.3 1.6.9l11.7-7.4c.6-.4.6-1.3 0-1.7L8.6 3.7C7.9 3.3 7 3.8 7 4.6Z"/>'),
    "pause": (_FILL, '<rect x="6" y="4" width="4.5" height="16" rx="1.4"/><rect x="13.5" y="4" width="4.5" height="16" rx="1.4"/>'),
}


def align_to_language(lang: str, *labels: QLabel) -> None:
    """Align labels with the UI language, whatever script their text is in.

    Qt picks a label's side from its text, so a Latin song name or file name
    would otherwise sit on the far side of a Hebrew layout.
    """
    side = Qt.AlignRight if lang == "he" else Qt.AlignLeft
    for label in labels:
        label.setAlignment(side | Qt.AlignAbsolute | Qt.AlignVCenter)


def _render(svg: bytes, px: int) -> QPixmap:
    pixmap = QPixmap(QSize(px, px))
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(svg)).render(painter)
    painter.end()
    return pixmap


def icon(name: str, color: str) -> QIcon:
    """A tinted icon. Rendered large so it stays crisp at any display scale."""
    template, body = _ICONS[name]
    return QIcon(_render(template.format(color=color, body=body).encode(), 96))


def logo_pixmap(size: int, ratio: float = 2.0) -> QPixmap:
    """The full logo at ``size`` logical pixels."""
    pixmap = _render(LOGO_SVG.read_bytes(), round(size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    return pixmap

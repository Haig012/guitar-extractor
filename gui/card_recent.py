"""
Card 2: Recent Files — shows last 7 processed files
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from utils.translations import get_text
from utils import settings as settings_mgr


class RecentFileItem(QWidget):
    """Single recent file entry."""
    clicked = Signal(str)  # file path

    def __init__(self, name: str, date: str, path: str, lang: str = "en", parent=None):
        super().__init__(parent)
        self.path = path
        self.lang = lang
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setObjectName("recentItem")
        self.setProperty("class", "recentItem")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        direction = Qt.RightToLeft if lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)

        name_label = QLabel(name)
        name_label.setObjectName("recentName")
        name_label.setWordWrap(False)

        date_label = QLabel(date)
        date_label.setObjectName("recentDate")

        layout.addWidget(name_label)
        layout.addWidget(date_label)

        self.setStyleSheet("""
            #recentItem {
                background-color: #111520;
                border: 1px solid #1A1D2E;
                border-radius: 8px;
            }
            #recentItem:hover {
                background-color: #161B2E;
                border-color: #5865F2;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.path)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace(
            "background-color: #111520", "background-color: #161B2E"
        ))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace(
            "background-color: #161B2E", "background-color: #111520"
        ))
        super().leaveEvent(event)


class RecentFilesCard(QWidget):
    """Card 2: Recent Files."""

    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self._build_ui()
        self.refresh()

    def _t(self, key: str, **kw) -> str:
        return get_text(self.lang, key, **kw)

    def _build_ui(self):
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 24)

        # Header row
        header_row = QHBoxLayout()
        self.titleLabel = QLabel(self._t("card_recent"))
        self.titleLabel.setObjectName("cardTitle")

        self.clearBtn = QPushButton(self._t("clear_recent"))
        self.clearBtn.setObjectName("smallButton")
        self.clearBtn.setFixedHeight(26)
        self.clearBtn.clicked.connect(self._clear_recent)

        header_row.addWidget(self.titleLabel)
        header_row.addStretch()
        header_row.addWidget(self.clearBtn)
        layout.addLayout(header_row)

        # Hint label
        self.hintLabel = QLabel(self._t("recent_open"))
        self.hintLabel.setObjectName("stepLabel")
        layout.addWidget(self.hintLabel)

        # Scrollable list
        self.listWidget = QWidget()
        self.listLayout = QVBoxLayout(self.listWidget)
        self.listLayout.setSpacing(4)
        self.listLayout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.listWidget)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMaximumHeight(360)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(scroll)

        self.emptyLabel = QLabel(self._t("recent_empty"))
        self.emptyLabel.setObjectName("stepLabel")
        self.emptyLabel.setAlignment(Qt.AlignCenter)
        self.emptyLabel.setVisible(False)
        layout.addWidget(self.emptyLabel)

    def refresh(self):
        """Reload recent files from storage."""
        # Clear list
        while self.listLayout.count():
            item = self.listLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = settings_mgr.load_recent()
        direction = Qt.RightToLeft if self.lang == "he" else Qt.LeftToRight

        if items:
            self.emptyLabel.setVisible(False)
            for entry in items:
                widget = RecentFileItem(
                    entry.get("name", ""),
                    entry.get("date", ""),
                    entry.get("path", ""),
                    self.lang
                )
                widget.clicked.connect(self._open_file)
                widget.setLayoutDirection(direction)
                self.listLayout.addWidget(widget)
            self.listLayout.addStretch()
        else:
            self.emptyLabel.setVisible(True)

    def _open_file(self, path: str):
        if os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(
                self, "File Not Found",
                f"The file no longer exists:\n{path}"
            )

    def _clear_recent(self):
        reply = QMessageBox.question(
            self,
            self._t("clear_recent"),
            self._t("confirm_clear"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            settings_mgr.clear_recent()
            self.refresh()

    def add_file(self, path: str):
        """Add a new file to the recent list."""
        settings_mgr.add_recent(path)
        self.refresh()

    def retranslate(self, lang: str):
        self.lang = lang
        self.titleLabel.setText(self._t("card_recent"))
        self.clearBtn.setText(self._t("clear_recent"))
        self.hintLabel.setText(self._t("recent_open"))
        self.emptyLabel.setText(self._t("recent_empty"))
        direction = Qt.RightToLeft if lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)
        self.refresh()

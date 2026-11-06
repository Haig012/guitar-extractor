"""
Progress page: percentage, step, status, ETA, and a log that stays out of the way
until asked for. Failures are shown here too, with the suggested fix.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)

from gui.icons import align_to_language
from gui.styles import COLORS
from utils.translations import get_text


class DebugCard(QWidget):
    cancel_clicked = Signal()
    back_clicked = Signal()

    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self._export_folder = ""
        self._log_expanded = False
        self._build_ui()
        self.retranslate(lang)

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(8)

        self.topSpace = QWidget()
        root.addWidget(self.topSpace, 1)

        top = QHBoxLayout()
        self.pctLabel = QLabel("0%")
        self.pctLabel.setObjectName("pctValue")
        self.stepLabel = QLabel("")
        self.stepLabel.setObjectName("stepValue")
        top.addWidget(self.pctLabel)
        top.addStretch(1)
        top.addWidget(self.stepLabel, 0, Qt.AlignBottom)
        root.addLayout(top)

        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(False)
        root.addWidget(self.progressBar)

        self.statusLabel = QLabel()
        self.statusLabel.setObjectName("statusValue")
        self.statusLabel.setWordWrap(True)
        root.addWidget(self.statusLabel)
        self.etaLabel = QLabel()
        self.etaLabel.setObjectName("etaValue")
        self.etaLabel.setWordWrap(True)
        root.addWidget(self.etaLabel)

        buttons = QHBoxLayout()
        buttons.setSpacing(4)
        self.cancelBtn = QPushButton()
        self.cancelBtn.setObjectName("cancelButton")
        self.cancelBtn.setVisible(False)
        self.cancelBtn.clicked.connect(self.cancel_clicked.emit)
        self.backBtn = QPushButton()
        self.backBtn.setVisible(False)
        self.backBtn.clicked.connect(self.back_clicked.emit)
        self.toggleLogBtn = QPushButton()
        self.saveLogBtn = QPushButton()
        self.clearLogBtn = QPushButton()
        for btn in (self.toggleLogBtn, self.saveLogBtn, self.clearLogBtn):
            btn.setObjectName("ghost")
        self.toggleLogBtn.clicked.connect(lambda: self._set_log_expanded(not self._log_expanded))
        self.saveLogBtn.clicked.connect(self._save_log)
        self.clearLogBtn.clicked.connect(self._clear_log)
        buttons.addWidget(self.cancelBtn)
        buttons.addWidget(self.backBtn)
        buttons.addStretch(1)
        buttons.addWidget(self.saveLogBtn)
        buttons.addWidget(self.clearLogBtn)
        buttons.addWidget(self.toggleLogBtn)
        root.addSpacing(4)
        root.addLayout(buttons)

        self.logEdit = QPlainTextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMaximumBlockCount(5000)
        root.addWidget(self.logEdit, 6)

        self.bottomSpace = QWidget()
        root.addWidget(self.bottomSpace, 1)
        self._set_log_expanded(False)

    def _set_log_expanded(self, expanded: bool):
        self._log_expanded = expanded
        self.logEdit.setVisible(expanded)
        self.saveLogBtn.setVisible(expanded)
        self.clearLogBtn.setVisible(expanded)
        # Collapsed, the readout sits centred; expanded, the log takes the room.
        self.topSpace.setVisible(not expanded)
        self.bottomSpace.setVisible(not expanded)
        self.toggleLogBtn.setText(get_text(self.lang, "hide_log" if expanded else "show_log"))

    # ── API ──────────────────────────────────────────────────────────────
    def set_progress(self, v: int):
        self.progressBar.setValue(v)
        self.pctLabel.setText(f"{v}%")

    def set_eta(self, text: str):
        self.etaLabel.setText(text)

    def set_status(self, text: str):
        self._set_status_state("")
        self.statusLabel.setText(text)

    def set_step(self, step: int, total: int):
        self.stepLabel.setText(f"{step} / {total}")

    def set_export_folder(self, folder: str):
        self._export_folder = folder

    def set_processing(self, processing: bool, export_folder: str = ""):
        self.cancelBtn.setVisible(processing)
        self.cancelBtn.setEnabled(True)
        if export_folder:
            self._export_folder = export_folder

    def set_cancelling(self):
        self.cancelBtn.setEnabled(False)
        self.set_status(get_text(self.lang, "cancelling"))

    def set_back_visible(self, visible: bool):
        self.backBtn.setVisible(visible)

    def show_error(self, message: str, fix: str):
        self._set_status_state("err")
        self.statusLabel.setText(message)
        self.etaLabel.setText(fix)
        self._set_log_expanded(True)

    def reset(self):
        self.set_progress(0)
        self.set_eta("")
        self.set_status(get_text(self.lang, "status_starting"))
        self.stepLabel.setText("")
        self.logEdit.clear()
        self._set_log_expanded(False)

    def append_log(self, text: str):
        cursor = self.logEdit.textCursor()
        cursor.movePosition(QTextCursor.End)

        low = text.lower()
        if text.startswith("❌") or "error" in low or "failed" in low:
            color = COLORS["err"]
        elif text.startswith("✅") or "done" in low:
            color = COLORS["ok"]
        elif text.startswith("⚠") or "warning" in low or "skipped" in low:
            color = COLORS["warn"]
        elif text.startswith("$"):
            color = COLORS["text_mute"]
        elif text.startswith("[") and "/" in text[:8]:
            color = COLORS["accent_hi"]
        else:
            color = COLORS["text_dim"]

        ts = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<span style="color:{color}; font-family:Consolas,monospace; font-size:11px;">'
            f'[{ts}] {_html_escape(text)}</span>'
        )
        self.logEdit.appendHtml(html)
        self.logEdit.verticalScrollBar().setValue(self.logEdit.verticalScrollBar().maximum())

    # ── Private ──────────────────────────────────────────────────────────
    def _set_status_state(self, state: str):
        self.statusLabel.setProperty("state", state)
        self.statusLabel.style().unpolish(self.statusLabel)
        self.statusLabel.style().polish(self.statusLabel)

    def _save_log(self):
        text = self.logEdit.toPlainText()
        if not text.strip():
            return
        folder = self._export_folder or str(Path.home() / "Desktop")
        os.makedirs(folder, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(folder, f"guitar_extractor_{ts}.log")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        self.append_log(f"✅ Log saved: {path}")

    def _clear_log(self):
        self.logEdit.clear()

    def retranslate(self, lang: str):
        self.lang = lang
        t = lambda k: get_text(lang, k)
        align_to_language(lang, self.statusLabel, self.etaLabel)
        self.cancelBtn.setText(t("cancel"))
        self.backBtn.setText(t("back_to_player"))
        self.saveLogBtn.setText(t("save_log"))
        self.clearLogBtn.setText(t("clear_log"))
        self.toggleLogBtn.setText(t("hide_log") if self._log_expanded else t("show_log"))


def _html_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

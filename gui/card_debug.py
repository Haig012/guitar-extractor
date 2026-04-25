"""
Card 3 — progress bar + status + collapsible log.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QPlainTextEdit, QSizePolicy,
)

from utils.translations import get_text


class DebugCard(QWidget):
    cancel_clicked = Signal()

    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self._export_folder = ""
        self._log_expanded = False
        self._build_ui()
        self.retranslate(lang)

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setProperty("class", "card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 20)
        root.setSpacing(12)

        # Title + step
        title_row = QHBoxLayout()
        self.titleLabel = QLabel()
        self.titleLabel.setObjectName("cardTitle")
        self.stepLabel = QLabel("")
        self.stepLabel.setObjectName("stepLabel")
        self.stepLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_row.addWidget(self.titleLabel)
        title_row.addStretch()
        title_row.addWidget(self.stepLabel)
        root.addLayout(title_row)

        # Progress bar + pct label
        prog_row = QHBoxLayout()
        prog_row.setSpacing(10)
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(False)
        self.pctLabel = QLabel("0%")
        self.pctLabel.setObjectName("etaLabel")
        self.pctLabel.setFixedWidth(40)
        self.pctLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        prog_row.addWidget(self.progressBar, 1)
        prog_row.addWidget(self.pctLabel)
        root.addLayout(prog_row)

        # Status line + ETA
        status_row = QHBoxLayout()
        self.statusLabel = QLabel()
        self.statusLabel.setObjectName("statusLabel")
        self.etaLabel = QLabel()
        self.etaLabel.setObjectName("etaLabel")
        self.etaLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_row.addWidget(self.statusLabel, 1)
        status_row.addWidget(self.etaLabel)
        root.addLayout(status_row)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.cancelBtn = QPushButton()
        self.cancelBtn.setObjectName("cancelButton")
        self.cancelBtn.setVisible(False)
        self.cancelBtn.clicked.connect(self.cancel_clicked.emit)
        btn_row.addWidget(self.cancelBtn)
        btn_row.addStretch()

        self.toggleLogBtn = QPushButton()
        self.toggleLogBtn.setObjectName("smallButton")
        self.toggleLogBtn.clicked.connect(self._toggle_log)
        self.saveLogBtn = QPushButton()
        self.saveLogBtn.setObjectName("smallButton")
        self.saveLogBtn.clicked.connect(self._save_log)
        self.clearLogBtn = QPushButton()
        self.clearLogBtn.setObjectName("smallButton")
        self.clearLogBtn.clicked.connect(self._clear_log)
        btn_row.addWidget(self.toggleLogBtn)
        btn_row.addWidget(self.saveLogBtn)
        btn_row.addWidget(self.clearLogBtn)
        root.addLayout(btn_row)

        # Log (hidden by default)
        self.logEdit = QPlainTextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMaximumBlockCount(5000)
        self.logEdit.setMinimumHeight(180)
        self.logEdit.setVisible(False)
        root.addWidget(self.logEdit)

    # ── API ──────────────────────────────────────────────────────────────
    def set_progress(self, v: int):
        self.progressBar.setValue(v)
        self.pctLabel.setText(f"{v}%")

    def set_eta(self, text: str):
        self.etaLabel.setText(get_text(self.lang, "eta") + f": {text}")

    def set_status(self, text: str):
        self.statusLabel.setText(get_text(self.lang, "status") + f": {text}")

    def set_step(self, step: int, total: int):
        self.stepLabel.setText(f"{step} / {total}")

    def set_export_folder(self, folder: str):
        self._export_folder = folder

    def set_processing(self, processing: bool, export_folder: str = ""):
        self.cancelBtn.setVisible(processing)
        if export_folder:
            self._export_folder = export_folder

    def reset(self):
        self.set_progress(0)
        self.set_eta("—")
        self.set_status("—")
        self.stepLabel.setText("")

    def append_log(self, text: str):
        cursor = self.logEdit.textCursor()
        cursor.movePosition(QTextCursor.End)

        low = text.lower()
        if text.startswith("❌") or "error" in low or "failed" in low:
            color = "#F47272"
        elif text.startswith("✅") or "done" in low:
            color = "#32D583"
        elif text.startswith("⚠") or "warning" in low or "skipped" in low:
            color = "#FBBF4D"
        elif text.startswith("$"):
            color = "#6B7085"
        elif text.startswith("[") and "/" in text[:8]:
            color = "#FF8C3D"
        else:
            color = "#9AA0B0"

        ts = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<span style="color:{color}; font-family:Consolas,monospace; font-size:11px;">'
            f'[{ts}] {_html_escape(text)}</span>'
        )
        self.logEdit.appendHtml(html)
        self.logEdit.verticalScrollBar().setValue(self.logEdit.verticalScrollBar().maximum())

    # ── Private ──────────────────────────────────────────────────────────
    def _toggle_log(self):
        self._log_expanded = not self._log_expanded
        self.logEdit.setVisible(self._log_expanded)
        self.toggleLogBtn.setText(
            get_text(self.lang, "hide_log") if self._log_expanded
            else get_text(self.lang, "show_log")
        )

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
        self.titleLabel.setText("📊  " + t("section_progress"))
        self.cancelBtn.setText("⏹  " + t("cancel"))
        self.saveLogBtn.setText(t("save_log"))
        self.clearLogBtn.setText(t("clear_log"))
        self.toggleLogBtn.setText(t("hide_log") if self._log_expanded else t("show_log"))
        self.statusLabel.setText(t("status") + ": —")
        self.etaLabel.setText(t("eta") + ": —")
        self.setLayoutDirection(Qt.RightToLeft if lang == "he" else Qt.LeftToRight)


def _html_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

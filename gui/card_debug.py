"""
Card 3: Debugging & Status — progress bar, ETA, logs, step indicators
"""
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QPlainTextEdit, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QColor

from utils.translations import get_text


class DebugCard(QWidget):
    """Card 3: Debugging & Status."""

    cancel_clicked = Signal()

    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self._export_folder = ""
        self._build_ui()

    def _t(self, key: str, **kw) -> str:
        return get_text(self.lang, key, **kw)

    def _build_ui(self):
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 24)

        # ── Title ──
        title_row = QHBoxLayout()
        self.titleLabel = QLabel(self._t("card_debug"))
        self.titleLabel.setObjectName("cardTitle")
        self.expandBtn = QPushButton(self._t("show_details"))
        self.expandBtn.setObjectName("smallButton")
        self.expandBtn.setFixedHeight(30)
        self.expandBtn.clicked.connect(self._toggle_details)
        title_row.addWidget(self.titleLabel)
        title_row.addStretch()
        title_row.addWidget(self.expandBtn)
        layout.addLayout(title_row)

        # ── Progress bar + percentage ──
        prog_row = QHBoxLayout()
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFixedHeight(10)

        self.progressPctLabel = QLabel("0%")
        self.progressPctLabel.setObjectName("etaLabel")
        self.progressPctLabel.setFixedWidth(35)
        self.progressPctLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        prog_row.addWidget(self.progressBar)
        prog_row.addWidget(self.progressPctLabel)
        layout.addLayout(prog_row)

        self.detailsWidget = QWidget()
        details_layout = QVBoxLayout(self.detailsWidget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(10)

        # ── Step indicator ──
        self.stepLabel = QLabel("")
        self.stepLabel.setObjectName("stepLabel")
        details_layout.addWidget(self.stepLabel)

        # ── Status + ETA row ──
        status_row = QHBoxLayout()
        self.statusLabel = QLabel(self._t("status") + ": —")
        self.statusLabel.setObjectName("statusLabel")

        self.etaLabel = QLabel(self._t("eta") + ": —")
        self.etaLabel.setObjectName("etaLabel")
        self.etaLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        status_row.addWidget(self.statusLabel, 1)
        status_row.addWidget(self.etaLabel)
        details_layout.addLayout(status_row)

        # ── Log text area ──
        self.logEdit = QPlainTextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMaximumBlockCount(5000)
        self.logEdit.setMinimumHeight(200)
        self.logEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        details_layout.addWidget(self.logEdit)

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.cancelBtn = QPushButton("⏹  Cancel")
        self.cancelBtn.setObjectName("cancelButton")
        self.cancelBtn.setFixedHeight(34)
        self.cancelBtn.setVisible(False)
        self.cancelBtn.clicked.connect(self.cancel_clicked)

        self.saveLogBtn = QPushButton(self._t("save_log"))
        self.saveLogBtn.setObjectName("smallButton")
        self.saveLogBtn.clicked.connect(self._save_log)

        self.clearLogBtn = QPushButton(self._t("clear_log"))
        self.clearLogBtn.setObjectName("smallButton")
        self.clearLogBtn.clicked.connect(self._clear_log)

        self.openOutputBtn = QPushButton(self._t("open_output"))
        self.openOutputBtn.setObjectName("smallButton")
        self.openOutputBtn.clicked.connect(self._open_output)
        self.openOutputBtn.setEnabled(False)

        btn_row.addWidget(self.cancelBtn)
        btn_row.addStretch()
        btn_row.addWidget(self.saveLogBtn)
        btn_row.addWidget(self.clearLogBtn)
        btn_row.addWidget(self.openOutputBtn)
        details_layout.addLayout(btn_row)

        layout.addWidget(self.detailsWidget)
        self._details_expanded = False
        self.detailsWidget.setVisible(False)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_progress(self, value: int):
        self.progressBar.setValue(value)
        self.progressPctLabel.setText(f"{value}%")

    def set_eta(self, text: str):
        self.etaLabel.setText(self._t("eta") + f": {text}")

    def set_status(self, text: str):
        self.statusLabel.setText(self._t("status") + f": {text}")

    def set_step(self, step: int, total: int):
        self.stepLabel.setText(f"Step {step} / {total}")

    def append_log(self, text: str):
        """Append a line to the log, auto-scroll to bottom."""
        # Color-code lines
        cursor = self.logEdit.textCursor()
        cursor.movePosition(QTextCursor.End)

        if text.startswith("❌") or "error" in text.lower() or "failed" in text.lower():
            color = "#FF6B6B"
        elif text.startswith("✅") or "done" in text.lower() or "success" in text.lower():
            color = "#4ADE80"
        elif text.startswith("⚠") or "warning" in text.lower() or "skipped" in text.lower():
            color = "#FBB040"
        elif text.startswith("$"):
            color = "#6B7299"
        elif text.startswith("[Step"):
            color = "#A5B4FC"
        else:
            color = "#8B9EB0"

        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f'<span style="color:{color}; font-family: Consolas, monospace; font-size:12px;">[{timestamp}] {self._escape_html(text)}</span>'

        self.logEdit.appendHtml(line)
        self.logEdit.verticalScrollBar().setValue(
            self.logEdit.verticalScrollBar().maximum()
        )

    def set_processing(self, processing: bool, export_folder: str = ""):
        self.cancelBtn.setVisible(processing)
        if export_folder:
            self._export_folder = export_folder
            self.openOutputBtn.setEnabled(True)
        if not processing:
            self.cancelBtn.setVisible(False)

    def set_export_folder(self, folder: str):
        self._export_folder = folder
        self.openOutputBtn.setEnabled(bool(folder))

    def reset(self):
        self.set_progress(0)
        self.set_eta("—")
        self.set_status("—")
        self.stepLabel.setText("")

    # ── Private ───────────────────────────────────────────────────────────────

    def _save_log(self):
        text = self.logEdit.toPlainText()
        if not text.strip():
            return

        folder = self._export_folder or str(Path.home() / "Desktop")
        os.makedirs(folder, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(folder, f"guitar_extractor_{ts}.log")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(text)

        self.append_log(f"✅ Log saved to: {log_path}")

    def _clear_log(self):
        self.logEdit.clear()

    def _open_output(self):
        if self._export_folder and os.path.exists(self._export_folder):
            final = os.path.join(self._export_folder, "final_result")
            if os.path.exists(final):
                os.startfile(final)
            else:
                os.startfile(self._export_folder)

    def _toggle_details(self):
        self._details_expanded = not self._details_expanded
        self.detailsWidget.setVisible(self._details_expanded)
        self.expandBtn.setText(self._t("hide_details") if self._details_expanded else self._t("show_details"))

    def _escape_html(self, text: str) -> str:
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

    def retranslate(self, lang: str):
        self.lang = lang
        self.titleLabel.setText(self._t("card_debug"))
        self.saveLogBtn.setText(self._t("save_log"))
        self.clearLogBtn.setText(self._t("clear_log"))
        self.openOutputBtn.setText(self._t("open_output"))
        self.expandBtn.setText(self._t("hide_details") if self._details_expanded else self._t("show_details"))
        direction = Qt.RightToLeft if lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)

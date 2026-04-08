"""
Main Window — assembles header, 3 cards, manages pipeline + signals
"""
import os
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QSizePolicy,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

from gui.styles import LIGHT_STYLESHEET
from gui.card_performance import PerformanceCard
from gui.card_recent import RecentFilesCard
from gui.card_debug import DebugCard
from gui.dep_dialog import DependencyDialog
from pipeline.worker import PipelineWorker
from utils.translations import get_text
from utils import settings as settings_mgr


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = settings_mgr.load_settings()
        self._lang = self._settings.get("language", "en")
        # Force English as default first run
        if "language" not in self._settings:
            self._settings["language"] = "en"
            self._lang = "en"
            settings_mgr.save_settings(self._settings)
        self._worker: PipelineWorker | None = None
        self._last_config: dict | None = None

        self.setWindowTitle("🎸 Guitar Extractor")
        self.setMinimumSize(800, 700)
        self.resize(1000, 900)
        self.setGeometry(
            100, 100,
            min(1000, self.screen().availableGeometry().width() - 40),
            min(900, self.screen().availableGeometry().height() - 40)
        )

        self.setStyleSheet(LIGHT_STYLESHEET)
        self._build_ui()
        self._apply_language_font()
        self._apply_direction()

    def _t(self, key: str, **kw) -> str:
        return get_text(self._lang, key, **kw)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        root_layout.addWidget(self._build_header())

        # ── Scrollable content area ───────────────────────────────────────
        scroll = QScrollArea()
        scroll.setObjectName("scrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(28, 24, 28, 28)
        scroll_layout.setSpacing(20)

        # ── Card 1: Performance ───────────────────────────────────────────
        self.perfCard = PerformanceCard(self._lang, self._settings)
        self.perfCard.go_clicked.connect(self._on_go)
        self.perfCard.check_deps.connect(self._show_dep_dialog)
        self.perfCard.repeat_last.connect(self._on_repeat_last)
        scroll_layout.addWidget(self.perfCard)


        # ── Card 3: Debug ─────────────────────────────────────────────────
        self.debugCard = DebugCard(self._lang)
        self.debugCard.cancel_clicked.connect(self._on_cancel)
        scroll_layout.addWidget(self.debugCard)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("headerWidget")
        header.setFixedHeight(85)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        # Guitar emoji icon
        icon_label = QLabel("🎸")
        icon_label.setObjectName("guitarIcon")

        # App title + subtitle
        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        self.titleLabel = QLabel(self._t("app_title"))
        self.titleLabel.setObjectName("appTitle")

        self.subtitleLabel = QLabel(self._t("app_subtitle"))
        self.subtitleLabel.setObjectName("appSubtitle")

        title_col.addWidget(self.titleLabel)
        title_col.addWidget(self.subtitleLabel)

        layout.addWidget(icon_label)
        layout.addLayout(title_col)
        layout.addStretch()

        # Right side: made by + language toggle
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        right_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.madeByLabel = QLabel(self._t("made_by"))
        self.madeByLabel.setObjectName("madeByLabel")
        self.madeByLabel.setAlignment(Qt.AlignRight)

        # Language toggle button
        lang_row = QHBoxLayout()
        lang_row.setSpacing(6)
        self.langBtn = QPushButton("🇮🇱 Hebrew" if self._lang == "en" else "🇬🇧 English")
        self.langBtn.setObjectName("langButton")
        self.langBtn.clicked.connect(self._toggle_language)

        lang_row.addStretch()
        lang_row.addWidget(self.langBtn)

        right_col.addWidget(self.madeByLabel)
        right_col.addLayout(lang_row)

        layout.addLayout(right_col)
        return header

    # ── Language ──────────────────────────────────────────────────────────────

    def _toggle_language(self):
        self._lang = "he" if self._lang == "en" else "en"
        self._settings["language"] = self._lang
        settings_mgr.save_settings(self._settings)
        self._apply_language_font()
        self._retranslate()
        self._apply_direction()

    def _retranslate(self):
        self.titleLabel.setText(self._t("app_title"))
        self.subtitleLabel.setText(self._t("app_subtitle"))
        self.madeByLabel.setText(self._t("made_by"))
        self.langBtn.setText("🇮🇱 Hebrew" if self._lang == "en" else "🇬🇧 English")
        self.perfCard.retranslate(self._lang)
        self.debugCard.retranslate(self._lang)

    def _apply_direction(self):
        direction = Qt.RightToLeft if self._lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)

    def _apply_language_font(self):
        from PySide6.QtWidgets import QApplication
        font_family = "Teom" if self._lang == "he" else "Segoe UI"
        QApplication.instance().setFont(QFont(font_family, 11))

    # ── Pipeline ──────────────────────────────────────────────────────────────

    def _on_go(self, config: dict):
        if self._worker and self._worker.isRunning():
            return

        # Validate export folder
        folder = config.get("export_folder", "").strip()
        if not folder:
            QMessageBox.warning(self, "Error", self._t("error_no_folder"))
            return

        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot create export folder:\n{e}")
            return

        self._last_config = config
        self._settings["last_input"] = config.get("input_value", "")
        self._settings["last_input_type"] = config.get("input_type", "youtube")
        self._settings["export_folder"] = folder
        self._settings["format"] = config.get("format", "wav")
        # No single timeRangeEdit anymore - using separate start/end
        start = self.perfCard.timeStartEdit.text().strip()
        end = self.perfCard.timeEndEdit.text().strip()
        if start or end:
            self._settings["last_time_range"] = f"{start} - {end}"
        else:
            self._settings["last_time_range"] = ""
        self._settings["remove_crowd"] = bool(config.get("remove_crowd", False))
        self._settings["remove_reverb"] = bool(config.get("remove_reverb", False))
        self._settings["crowd_mode"] = config.get("crowd_mode", "remove")
        settings_mgr.save_settings(self._settings)

        # Reset debug card
        self.debugCard.reset()
        self.debugCard.set_export_folder(folder)
        self.debugCard.set_processing(True, folder)
        self.perfCard.set_processing(True)

        # Start worker
        self._worker = PipelineWorker(config)
        self._worker.progress.connect(self.debugCard.set_progress)
        self._worker.eta_update.connect(self.debugCard.set_eta)
        self._worker.log.connect(self.debugCard.append_log)
        self._worker.status.connect(self.debugCard.set_status)
        self._worker.step_changed.connect(self.debugCard.set_step)
        self._worker.pipeline_finished.connect(self._on_pipeline_finished)
        self._worker.error.connect(self._on_pipeline_error)
        self._worker.start()

    def _on_cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.debugCard.append_log("⚠ Cancelling...")
            self._worker.quit()
            self._worker.wait(3000)
        self._on_pipeline_done()

    def _on_pipeline_finished(self, output_path: str):
        self.debugCard.append_log(f"🎸 Primary output: {output_path}")
        self.debugCard.set_status(self._t("step_done"))
        self.debugCard.set_eta(self._t("eta_unknown").replace("Unknown", "Done!"))
        self._on_pipeline_done()

        folder = os.path.dirname(output_path)
        other_name = os.path.basename(output_path)
        
        # For solo mode output - only one file exists
        if output_path.lower().endswith("_solo_mix.wav"):
            mix_name = ""
        elif output_path.lower().endswith("_other.wav"):
            mix_name = os.path.basename(output_path)[:-len("_other.wav")] + "_everything_but_other.wav"
        else:
            mix_name = ""

        # Auto-open output folder
        if self._settings.get("auto_open_output", True):
            if os.path.exists(folder):
                QTimer.singleShot(500, lambda: os.startfile(folder))

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(self._t("export_done_title"))
        msg.setText(
            self._t(
                "export_done_body",
                folder=folder,
                other=other_name,
                mix=mix_name,
            )
        )
        open_btn = msg.addButton(self._t("open_folder"), QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)
        msg.exec()
        if msg.clickedButton() == open_btn and os.path.exists(folder):
            os.startfile(folder)

    def _on_pipeline_error(self, message: str, fix: str):
        self.debugCard.append_log(f"❌ ERROR: {message}")
        if fix:
            self.debugCard.append_log(f"💡 Fix: {fix}")
        self._on_pipeline_done()
        QMessageBox.critical(
            self,
            "Pipeline Error",
            f"❌ {message}\n\n💡 {fix}" if fix else f"❌ {message}"
        )

    def _on_pipeline_done(self):
        self.perfCard.set_processing(False)
        self.debugCard.set_processing(False)

    def _on_repeat_last(self):
        if self._last_config:
            self._on_go(self._last_config)
        else:
            QMessageBox.information(
                self, "No Previous Job",
                "There is no previous job to repeat yet."
            )

    # ── Dependency dialog ─────────────────────────────────────────────────────

    def _show_dep_dialog(self):
        dlg = DependencyDialog(self._lang, self)
        dlg.exec()

    # ── Window close ─────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self, "Processing in Progress",
                "A job is currently running. Cancel and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._worker.cancel()
                self._worker.quit()
                self._worker.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

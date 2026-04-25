"""
Main window — header + 3 cards (Settings / Progress / Player) + global shortcuts.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox,
)

from gui.card_debug import DebugCard
from gui.card_performance import PerformanceCard
from gui.card_player import PlayerCard
from gui.styles import DARK_STYLESHEET
from pipeline.worker import PipelineWorker
from utils import settings as settings_mgr
from utils.translations import get_text


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = settings_mgr.load_settings()
        self._lang = self._settings.get("language", "en")
        self._worker: PipelineWorker | None = None
        self._last_config: dict | None = None

        self.setWindowTitle("🎸 Guitar Extractor")
        self.setMinimumSize(820, 720)
        self.resize(1040, 940)
        self.setStyleSheet(DARK_STYLESHEET)

        self._build_ui()
        self._install_shortcuts()
        self._apply_language_font()
        self._apply_direction()

    # ── Build ────────────────────────────────────────────────────────────
    def _t(self, key: str, **kw) -> str:
        return get_text(self._lang, key, **kw)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setObjectName("scrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("scrollContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 28)
        content_layout.setSpacing(18)

        self.perfCard = PerformanceCard(self._lang, self._settings)
        self.perfCard.go_clicked.connect(self._on_go)
        self.perfCard.repeat_last.connect(self._on_repeat_last)
        content_layout.addWidget(self.perfCard)

        self.debugCard = DebugCard(self._lang)
        self.debugCard.cancel_clicked.connect(self._on_cancel)
        content_layout.addWidget(self.debugCard)

        self.playerCard = PlayerCard(self._lang)
        self.playerCard.open_folder_requested.connect(self._open_folder)
        content_layout.addWidget(self.playerCard)

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("headerWidget")
        header.setFixedHeight(72)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        icon = QLabel("🎸")
        icon.setObjectName("guitarIcon")
        layout.addWidget(icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.titleLabel = QLabel(self._t("app_title"))
        self.titleLabel.setObjectName("appTitle")
        self.subtitleLabel = QLabel(self._t("app_subtitle"))
        self.subtitleLabel.setObjectName("appSubtitle")
        title_col.addWidget(self.titleLabel)
        title_col.addWidget(self.subtitleLabel)
        layout.addLayout(title_col)
        layout.addStretch()

        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        right_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.madeByLabel = QLabel(self._t("made_by"))
        self.madeByLabel.setObjectName("madeByLabel")
        self.madeByLabel.setAlignment(Qt.AlignRight)
        lang_row = QHBoxLayout()
        lang_row.addStretch()
        self.langBtn = QPushButton()
        self.langBtn.setObjectName("langButton")
        self._update_lang_btn()
        self.langBtn.clicked.connect(self._toggle_language)
        lang_row.addWidget(self.langBtn)
        right_col.addWidget(self.madeByLabel)
        right_col.addLayout(lang_row)
        layout.addLayout(right_col)
        return header

    def _install_shortcuts(self):
        # Space = play/pause when player has tracks loaded.
        QShortcut(QKeySequence(Qt.Key_Space), self, activated=self._toggle_play)
        # Ctrl+Enter = GO.
        QShortcut(
            QKeySequence("Ctrl+Return"), self,
            activated=lambda: self.perfCard.goBtn.click() if self.perfCard.goBtn.isEnabled() else None,
        )
        # Esc = cancel if a job is running.
        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self._on_cancel_shortcut)

    def _toggle_play(self):
        if self.playerCard.isVisible():
            self.playerCard.toggle_play_pause()

    def _on_cancel_shortcut(self):
        if self._worker and self._worker.isRunning():
            self._on_cancel()

    # ── Language ─────────────────────────────────────────────────────────
    def _update_lang_btn(self):
        self.langBtn.setText("🇮🇱 עברית" if self._lang == "en" else "🇬🇧 English")

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
        self._update_lang_btn()
        self.perfCard.retranslate(self._lang)
        self.debugCard.retranslate(self._lang)
        self.playerCard.retranslate(self._lang)

    def _apply_direction(self):
        self.setLayoutDirection(Qt.RightToLeft if self._lang == "he" else Qt.LeftToRight)

    def _apply_language_font(self):
        from PySide6.QtWidgets import QApplication
        family = "Segoe UI" if self._lang == "en" else "Segoe UI"
        QApplication.instance().setFont(QFont(family, 10))

    # ── Pipeline ─────────────────────────────────────────────────────────
    def _on_go(self, config: dict):
        if self._worker and self._worker.isRunning():
            return

        folder = config.get("export_folder", "").strip()
        if not folder:
            QMessageBox.warning(self, self._t("app_title"), self._t("error_no_folder"))
            return
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, self._t("app_title"), f"Cannot create export folder:\n{e}")
            return

        self._last_config = config
        self._save_last_settings(config)

        # Reset UI for this run.
        self.playerCard.stop()
        self.playerCard.set_tracks({})
        self.debugCard.reset()
        self.debugCard.set_export_folder(folder)
        self.debugCard.set_processing(True, folder)
        self.perfCard.set_processing(True)

        self._worker = PipelineWorker(config)
        self._worker.progress.connect(self.debugCard.set_progress)
        self._worker.eta_update.connect(self.debugCard.set_eta)
        self._worker.log.connect(self.debugCard.append_log)
        self._worker.status.connect(self.debugCard.set_status)
        self._worker.step_changed.connect(self.debugCard.set_step)
        self._worker.pipeline_finished.connect(self._on_pipeline_finished)
        self._worker.error.connect(self._on_pipeline_error)
        self._worker.start()

    def _save_last_settings(self, config: dict):
        self._settings["last_input"] = config.get("input_value", "")
        self._settings["last_input_type"] = config.get("input_type", "youtube")
        self._settings["export_folder"] = config["export_folder"]
        self._settings["format"] = config.get("format", "wav")
        start_raw, end_raw = self.perfCard.get_time_range_raw()
        self._settings["last_time_range_start"] = start_raw
        self._settings["last_time_range_end"] = end_raw
        self._settings["remove_reverb"] = bool(config.get("remove_reverb", False))
        self._settings["remove_crowd"] = bool(config.get("remove_crowd", False))
        settings_mgr.save_settings(self._settings)

    def _on_cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.debugCard.append_log("⚠ Cancelling…")
            self._worker.quit()
            self._worker.wait(3000)
        self._after_pipeline()

    def _on_pipeline_finished(self, result: dict):
        self.debugCard.set_status(self._t("status_ready"))
        self.debugCard.set_eta("Done!")
        self._after_pipeline()

        self.playerCard.set_tracks(result)

        folder = result.get("folder") or ""
        if self._settings.get("auto_open_output", True) and folder and os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception:
                pass

        QMessageBox.information(
            self, self._t("export_done_title"),
            self._t("export_done_body", folder=folder),
        )

    def _on_pipeline_error(self, message: str, fix: str):
        self.debugCard.append_log(f"❌ {message}")
        if fix:
            self.debugCard.append_log(f"💡 {fix}")
        self._after_pipeline()
        QMessageBox.critical(
            self, "Pipeline Error",
            f"❌ {message}\n\n💡 {fix}" if fix else f"❌ {message}",
        )

    def _after_pipeline(self):
        self.perfCard.set_processing(False)
        self.debugCard.set_processing(False)

    def _on_repeat_last(self):
        if self._last_config:
            self._on_go(self._last_config)
        else:
            QMessageBox.information(
                self, self._t("app_title"), self._t("error_no_previous"),
            )

    def _open_folder(self, path: str):
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception:
                pass

    # ── Close ────────────────────────────────────────────────────────────
    def closeEvent(self, ev):
        if self._worker and self._worker.isRunning():
            reply = QMessageBox.question(
                self, self._t("app_title"), self._t("confirm_cancel_exit"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._worker.cancel()
                self._worker.quit()
                self._worker.wait(3000)
                ev.accept()
            else:
                ev.ignore()
        else:
            ev.accept()

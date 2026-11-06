"""
Main window: a slim header over two fixed panes, with no page scrolling.

Left is the setup pane. Right follows the job: a welcome page, then live progress,
then the player. Drop a file or link anywhere on the window to set the source.
"""
from __future__ import annotations

import ctypes
import os
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from gui.card_debug import DebugCard
from gui.card_performance import PerformanceCard
from gui.card_player import PlayerCard
from gui.icons import LOGO_ICO, logo_pixmap
from gui.styles import COLORS, DARK_STYLESHEET
from pipeline.worker import PipelineWorker
from utils import settings as settings_mgr
from utils.translations import get_text

SETUP_PANE_WIDTH = 410
WINDOW_SIZE = (960, 530)
MIN_WIDTH = 880

# DwmSetWindowAttribute ids (Windows 10 2004+ / Windows 11).
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_BORDER_COLOR = 34
_DWMWA_CAPTION_COLOR = 35


def _colorref(hex_color: str) -> int:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return r | (g << 8) | (b << 16)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = settings_mgr.load_settings()
        self._lang = self._settings.get("language", "en")
        self._worker: PipelineWorker | None = None
        self._cancelling = False
        self._compact_height = WINDOW_SIZE[1]

        self.setWindowTitle("Guitar Extractor")
        self.setWindowIcon(QIcon(str(LOGO_ICO)))
        # Only the width is fixed: the minimum height follows the layout, so the
        # window stays compact and grows just while Trim / Solo are open.
        self.setMinimumWidth(MIN_WIDTH)
        self.setStyleSheet(DARK_STYLESHEET)
        self.setAcceptDrops(True)

        self._build_ui()
        self._install_shortcuts()
        self._apply_direction()

        # Create the native window before sizing it: on a scaled display a size
        # set earlier gets divided by the scale factor when the window appears.
        self.winId()
        self.resize(*WINDOW_SIZE)

    def showEvent(self, ev):
        super().showEvent(ev)
        self._style_title_bar()

    def _style_title_bar(self):
        """Blend the native title bar into the header. Cosmetic, so never fatal."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            set_attr = ctypes.windll.dwmapi.DwmSetWindowAttribute
            for attr, value in (
                (_DWMWA_USE_IMMERSIVE_DARK_MODE, 1),
                (_DWMWA_CAPTION_COLOR, _colorref(COLORS["surface"])),
                (_DWMWA_BORDER_COLOR, _colorref(COLORS["border"])),
            ):
                data = ctypes.c_int(value)
                set_attr(hwnd, attr, ctypes.byref(data), ctypes.sizeof(data))
        except Exception:
            pass

    # ── Build ────────────────────────────────────────────────────────────
    def _t(self, key: str, **kw) -> str:
        return get_text(self._lang, key, **kw)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(12, 12, 12, 12)
        body.setSpacing(12)
        root.addLayout(body, 1)

        self.perfCard = PerformanceCard(self._lang, self._settings)
        self.perfCard.setFixedWidth(SETUP_PANE_WIDTH)
        self.perfCard.go_clicked.connect(self._on_go)
        self.perfCard.height_changed.connect(
            lambda: QTimer.singleShot(0, self._fit_height),
        )
        body.addWidget(self.perfCard)

        self.resultPane = QFrame()
        self.resultPane.setObjectName("pane")
        pane_layout = QVBoxLayout(self.resultPane)
        pane_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        pane_layout.addWidget(self.stack)
        body.addWidget(self.resultPane, 1)

        self.idlePage = self._build_idle_page()
        self.debugCard = DebugCard(self._lang)
        self.debugCard.cancel_clicked.connect(self._on_cancel)
        self.debugCard.back_clicked.connect(self._show_player)
        self.playerCard = PlayerCard(self._lang)
        self.playerCard.open_folder_requested.connect(self._open_folder)
        self.playerCard.show_log_requested.connect(self._show_log)
        for page in (self.idlePage, self.debugCard, self.playerCard):
            self.stack.addWidget(page)

    def _fit_height(self):
        """The layout grows the window for open option rows; this gives it back."""
        if self.isMaximized() or self.isFullScreen() or self.perfCard.options_open():
            return
        self.centralWidget().layout().activate()
        self.layout().activate()
        self.resize(self.width(), self._compact_height)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        # With no option rows open, any height is one the user chose. Keep it.
        compact = not (self.isMaximized() or self.isFullScreen())
        if compact and hasattr(self, "perfCard") and not self.perfCard.options_open():
            self._compact_height = ev.size().height()

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("header")
        header.setAttribute(Qt.WA_StyledBackground)
        header.setFixedHeight(46)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(28))
        layout.addWidget(logo)

        self.titleLabel = QLabel(self._t("app_title"))
        self.titleLabel.setObjectName("appTitle")
        self.subtitleLabel = QLabel(self._t("app_subtitle"))
        self.subtitleLabel.setObjectName("appSubtitle")
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.subtitleLabel)
        layout.addStretch(1)

        self.madeByLabel = QLabel(self._t("made_by"))
        self.madeByLabel.setObjectName("madeBy")
        layout.addWidget(self.madeByLabel)

        self.langBtn = QPushButton()
        self.langBtn.setObjectName("langButton")
        self.langBtn.clicked.connect(self._toggle_language)
        self._update_lang_btn()
        layout.addWidget(self.langBtn)
        return header

    def _build_idle_page(self) -> QWidget:
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(32, 24, 32, 24)
        col.setSpacing(8)
        col.addStretch(1)

        logo = QLabel()
        logo.setPixmap(logo_pixmap(64))
        logo.setAlignment(Qt.AlignCenter)
        col.addWidget(logo)
        col.addSpacing(8)

        self.idleTitle = QLabel()
        self.idleTitle.setObjectName("paneTitle")
        self.idleTitle.setAlignment(Qt.AlignCenter)
        col.addWidget(self.idleTitle)

        self.idleSteps = []
        for _ in range(3):
            step = QLabel()
            step.setObjectName("idleStep")
            step.setAlignment(Qt.AlignCenter)
            col.addWidget(step)
            self.idleSteps.append(step)

        col.addSpacing(10)
        self.idleKeys = QLabel()
        self.idleKeys.setObjectName("idleKeys")
        self.idleKeys.setAlignment(Qt.AlignCenter)
        col.addWidget(self.idleKeys)
        col.addStretch(1)
        self._retranslate_idle()
        return page

    def _retranslate_idle(self):
        self.idleTitle.setText(self._t("idle_title"))
        for i, step in enumerate(self.idleSteps, 1):
            step.setText(f"{i}.  {self._t(f'idle_step_{i}')}")
        self.idleKeys.setText(self._t("idle_keys"))

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
        if self.stack.currentWidget() is self.playerCard:
            self.playerCard.toggle_play_pause()

    def _on_cancel_shortcut(self):
        if self._worker and self._worker.isRunning():
            self._on_cancel()

    # ── Drag & drop (anywhere on the window) ─────────────────────────────
    def dragEnterEvent(self, ev):
        mime = ev.mimeData()
        if not self._is_busy() and (mime.hasUrls() or mime.hasText()):
            self.perfCard.set_drag_active(True)
            ev.acceptProposedAction()

    def dragLeaveEvent(self, ev):
        self.perfCard.set_drag_active(False)

    def dropEvent(self, ev):
        self.perfCard.set_drag_active(False)
        mime = ev.mimeData()
        if mime.hasUrls() and mime.urls():
            url = mime.urls()[0]
            self.perfCard.set_source(url.toLocalFile() if url.isLocalFile() else url.toString())
        elif mime.hasText():
            self.perfCard.set_source(mime.text().strip())
        ev.acceptProposedAction()

    # ── Language ─────────────────────────────────────────────────────────
    def _update_lang_btn(self):
        self.langBtn.setText("עברית" if self._lang == "en" else "English")

    def _toggle_language(self):
        self._lang = "he" if self._lang == "en" else "en"
        self._settings["language"] = self._lang
        settings_mgr.save_settings(self._settings)
        self._retranslate()
        self._apply_direction()

    def _retranslate(self):
        self.titleLabel.setText(self._t("app_title"))
        self.subtitleLabel.setText(self._t("app_subtitle"))
        self.madeByLabel.setText(self._t("made_by"))
        self._update_lang_btn()
        self._retranslate_idle()
        self.perfCard.retranslate(self._lang)
        self.debugCard.retranslate(self._lang)
        self.playerCard.retranslate(self._lang)

    def _apply_direction(self):
        self.setLayoutDirection(Qt.RightToLeft if self._lang == "he" else Qt.LeftToRight)

    # ── Pipeline ─────────────────────────────────────────────────────────
    def _is_busy(self) -> bool:
        return bool(self._worker and self._worker.isRunning())

    def _on_go(self, config: dict):
        if self._is_busy():
            return

        folder = config.get("export_folder", "").strip()
        if not folder:
            self.perfCard._fail(self._t("error_no_folder"))
            return
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            self.perfCard._fail(f"Cannot create export folder: {e}")
            return

        self._save_last_settings(config)

        # Reset UI for this run.
        self.playerCard.stop()
        self.playerCard.set_tracks({})
        self.debugCard.reset()
        self.debugCard.set_export_folder(folder)
        self.debugCard.set_processing(True, folder)
        self.debugCard.set_back_visible(False)
        self.perfCard.set_processing(True)
        self.stack.setCurrentWidget(self.debugCard)

        self._cancelling = False
        self._worker = PipelineWorker(config)
        self._worker.progress.connect(self.debugCard.set_progress)
        self._worker.eta_update.connect(self.debugCard.set_eta)
        self._worker.log.connect(self.debugCard.append_log)
        self._worker.status.connect(self._on_worker_status)
        self._worker.step_changed.connect(self.debugCard.set_step)
        self._worker.pipeline_finished.connect(self._on_pipeline_finished)
        self._worker.error.connect(self._on_pipeline_error)
        self._worker.finished.connect(self._on_worker_stopped)
        self._worker.start()

    def _on_worker_status(self, text: str):
        if not self._cancelling:
            self.debugCard.set_status(text)

    def _save_last_settings(self, config: dict):
        self._settings["last_input"] = config.get("input_value", "")
        self._settings["last_input_type"] = config.get("input_type", "youtube")
        self._settings["export_folder"] = config["export_folder"]
        self._settings["format"] = config.get("format", "wav")
        self._settings["export_video"] = bool(config.get("export_video", False))
        self._settings["detect_chords"] = bool(config.get("detect_chords", False))
        start_raw, end_raw = self.perfCard.get_time_range_raw()
        self._settings["last_time_range_start"] = start_raw
        self._settings["last_time_range_end"] = end_raw
        self._settings["remove_reverb"] = bool(config.get("remove_reverb", False))
        self._settings["remove_crowd"] = bool(config.get("remove_crowd", False))
        self._settings["export_stems"] = list(config.get("export_stems", ["guitar"]))
        self._settings["export_backing"] = bool(config.get("export_backing", True))
        settings_mgr.save_settings(self._settings)

    def _on_cancel(self):
        # The worker stops at its next checkpoint, which can be minutes away during
        # separation. The UI stays in "Cancelling" until the thread has really ended.
        if self._is_busy() and not self._cancelling:
            self._cancelling = True
            self._worker.cancel()
            self.debugCard.append_log("⚠ Cancelling…")
            self.debugCard.set_cancelling()

    def _on_worker_stopped(self):
        self._after_pipeline()
        if self._cancelling:
            self._cancelling = False
            self.stack.setCurrentWidget(self.idlePage)

    def _on_pipeline_finished(self, result: dict):
        self.debugCard.set_status(self._t("status_ready"))
        self.debugCard.set_eta("")
        self.playerCard.set_tracks(result)
        if self.playerCard.has_tracks:
            self._show_player()

        folder = result.get("folder") or ""
        if self._settings.get("auto_open_output", True) and folder and os.path.exists(folder):
            try:
                os.startfile(folder)
            except Exception:
                pass

    def _on_pipeline_error(self, message: str, fix: str):
        self.debugCard.append_log(f"❌ {message}")
        if fix:
            self.debugCard.append_log(f"💡 {fix}")
        self.debugCard.show_error(message, fix)

    def _after_pipeline(self):
        self.perfCard.set_processing(False)
        self.debugCard.set_processing(False)

    def _show_player(self):
        self.stack.setCurrentWidget(self.playerCard)

    def _show_log(self):
        self.debugCard.set_back_visible(True)
        self.debugCard._set_log_expanded(True)
        self.stack.setCurrentWidget(self.debugCard)

    def _open_folder(self, path: str):
        if path and os.path.exists(path):
            try:
                os.startfile(path)
            except Exception:
                pass

    # ── Close ────────────────────────────────────────────────────────────
    def closeEvent(self, ev):
        if self._is_busy():
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

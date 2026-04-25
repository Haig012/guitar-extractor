"""
Card 1 — input + settings + GO button.
Cleaner layout: Source / Output / Time Range / Solo Time / Go.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QRadioButton, QButtonGroup,
    QFrame, QMessageBox, QCheckBox,
)

from pipeline.uvr import (
    is_available as uvr_available,
    model_present,
    DEREVERB_MODEL,
    CROWD_MODEL,
)
from utils.helpers import is_valid_youtube_url
from utils.time_range import _parse_clock
from utils.translations import get_text


class _DropLineEdit(QLineEdit):
    """LineEdit that accepts drag-dropped URLs / local files."""
    file_dropped = Signal(str)
    url_dropped = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, ev: QDragEnterEvent):
        if ev.mimeData().hasUrls() or ev.mimeData().hasText():
            ev.acceptProposedAction()
        else:
            super().dragEnterEvent(ev)

    def dropEvent(self, ev: QDropEvent):
        mime = ev.mimeData()
        if mime.hasUrls() and mime.urls():
            url = mime.urls()[0]
            if url.isLocalFile():
                self.setText(url.toLocalFile())
                self.file_dropped.emit(url.toLocalFile())
            else:
                self.setText(url.toString())
                self.url_dropped.emit(url.toString())
        elif mime.hasText():
            self.setText(mime.text().strip())
            if self.text().startswith("http"):
                self.url_dropped.emit(self.text())
        ev.acceptProposedAction()


class PerformanceCard(QWidget):
    go_clicked = Signal(dict)
    repeat_last = Signal()
    input_changed = Signal()

    FORMATS = ("wav", "mp3", "m4a", "webm", "opus")

    def __init__(self, lang: str = "en", settings: dict | None = None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.settings = settings or {}
        self._selected_format = self.settings.get("format", "wav")
        self._remove_reverb = bool(self.settings.get("remove_reverb", False))
        self._remove_crowd = bool(self.settings.get("remove_crowd", False))
        self._solo_segments: list[dict] = []
        self._build_ui()
        self.retranslate(lang)
        self._apply_direction()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 22)
        layout.setSpacing(14)

        # Title
        self.titleLabel = QLabel()
        self.titleLabel.setObjectName("cardTitle")
        layout.addWidget(self.titleLabel)

        # ── Source ────────────────────────────────────────
        self.sourceLabel = self._section_label()
        layout.addWidget(self.sourceLabel)

        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(20)
        self._input_group = QButtonGroup(self)
        self.radioYT = QRadioButton()
        self.radioPC = QRadioButton()
        last_type = self.settings.get("last_input_type", "youtube")
        self.radioYT.setChecked(last_type == "youtube")
        self.radioPC.setChecked(last_type == "file")
        self._input_group.addButton(self.radioYT, 0)
        self._input_group.addButton(self.radioPC, 1)
        toggle_row.addWidget(self.radioYT)
        toggle_row.addWidget(self.radioPC)
        toggle_row.addStretch()
        layout.addLayout(toggle_row)

        self.urlEdit = _DropLineEdit()
        self.urlEdit.setText(self.settings.get("last_input", "") if last_type == "youtube" else "")
        self.urlEdit.textChanged.connect(self._on_input_changed)
        self.urlEdit.url_dropped.connect(lambda _: self._on_input_changed())
        layout.addWidget(self.urlEdit)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.fileEdit = _DropLineEdit()
        self.fileEdit.setText(self.settings.get("last_input", "") if last_type == "file" else "")
        self.fileEdit.textChanged.connect(self._on_input_changed)
        self.fileEdit.file_dropped.connect(lambda _: self._on_input_changed())
        self.filePickBtn = QPushButton()
        self.filePickBtn.clicked.connect(self._browse_file)
        file_row.addWidget(self.fileEdit, 1)
        file_row.addWidget(self.filePickBtn)
        layout.addLayout(file_row)

        # ── Export folder ─────────────────────────────────
        self.folderLabel = self._section_label()
        layout.addWidget(self.folderLabel)
        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)
        self.folderEdit = QLineEdit()
        self.folderEdit.setText(self.settings.get(
            "export_folder",
            str(Path.home() / "Desktop" / "exported_files"),
        ))
        self.folderEdit.setReadOnly(True)
        self.browseBtn = QPushButton()
        self.browseBtn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folderEdit, 1)
        folder_row.addWidget(self.browseBtn)
        layout.addLayout(folder_row)

        # ── Time range ────────────────────────────────────
        self.timeLabel = self._section_label()
        layout.addWidget(self.timeLabel)
        self.timeHint = QLabel()
        self.timeHint.setObjectName("hint")
        layout.addWidget(self.timeHint)
        time_row = QHBoxLayout()
        time_row.setSpacing(8)
        self.timeStartEdit = QLineEdit()
        self.timeStartEdit.setText(self.settings.get("last_time_range_start", ""))
        self.timeEndEdit = QLineEdit()
        self.timeEndEdit.setText(self.settings.get("last_time_range_end", ""))
        dash = QLabel("—")
        dash.setAlignment(Qt.AlignCenter)
        time_row.addWidget(self.timeStartEdit, 1)
        time_row.addWidget(dash)
        time_row.addWidget(self.timeEndEdit, 1)
        layout.addLayout(time_row)

        # ── Output format ─────────────────────────────────
        self.outputLabel = self._section_label()
        layout.addWidget(self.outputLabel)
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(6)
        self._format_buttons: dict[str, QPushButton] = {}
        for fmt in self.FORMATS:
            btn = QPushButton(fmt.upper())
            btn.setObjectName("formatButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, f=fmt: self._select_format(f))
            self._format_buttons[fmt] = btn
            fmt_row.addWidget(btn)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)
        self._select_format(self._selected_format)

        # ── Cleanup options (UVR) ─────────────────────────
        self.cleanupLabel = self._section_label()
        layout.addWidget(self.cleanupLabel)

        self.removeReverbCheckbox = QCheckBox()
        self.removeReverbCheckbox.setChecked(self._remove_reverb)
        self.removeCrowdCheckbox = QCheckBox()
        self.removeCrowdCheckbox.setChecked(self._remove_crowd)
        layout.addWidget(self.removeReverbCheckbox)
        layout.addWidget(self.removeCrowdCheckbox)

        self.uvrHint = QLabel()
        self.uvrHint.setObjectName("hint")
        self.uvrHint.setWordWrap(True)
        layout.addWidget(self.uvrHint)
        self._refresh_uvr_availability()

        # ── Solo Time ─────────────────────────────────────
        self.soloCheckbox = QCheckBox()
        layout.addWidget(self.soloCheckbox)

        self.soloContainer = QFrame()
        self.soloContainer.setObjectName("soloContainer")
        solo_layout = QVBoxLayout(self.soloContainer)
        solo_layout.setContentsMargins(14, 12, 14, 12)
        solo_layout.setSpacing(8)
        self.soloTitleLabel = QLabel()
        self.soloTitleLabel.setObjectName("soloTitle")
        solo_layout.addWidget(self.soloTitleLabel)
        self.soloSegmentsLayout = QVBoxLayout()
        self.soloSegmentsLayout.setSpacing(6)
        solo_layout.addLayout(self.soloSegmentsLayout)
        self.addSegmentBtn = QPushButton()
        self.addSegmentBtn.setObjectName("smallButton")
        self.addSegmentBtn.clicked.connect(self._add_solo_segment)
        solo_layout.addWidget(self.addSegmentBtn, 0, Qt.AlignLeft)
        layout.addWidget(self.soloContainer)
        self.soloContainer.setVisible(False)
        self.soloCheckbox.toggled.connect(self._toggle_solo_time)

        # ── Divider ───────────────────────────────────────
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        layout.addWidget(div)

        # ── Go row ────────────────────────────────────────
        go_row = QHBoxLayout()
        go_row.setSpacing(12)
        self.repeatBtn = QPushButton("🔁")
        self.repeatBtn.setObjectName("iconButton")
        self.repeatBtn.setToolTip(get_text(self.lang, "repeat_last"))
        self.repeatBtn.clicked.connect(self.repeat_last.emit)
        go_row.addWidget(self.repeatBtn)
        go_row.addStretch()
        self.goBtn = QPushButton()
        self.goBtn.setObjectName("goButton")
        self.goBtn.clicked.connect(self._on_go)
        self.goBtn.setEnabled(False)
        go_row.addWidget(self.goBtn)
        go_row.addStretch()
        layout.addLayout(go_row)

        self._toggle_input_mode()
        self.radioYT.toggled.connect(self._toggle_input_mode)

    def _section_label(self) -> QLabel:
        lbl = QLabel()
        lbl.setObjectName("sectionLabel")
        return lbl

    # ── Behaviour ────────────────────────────────────────────────────────
    def _toggle_input_mode(self):
        is_yt = self.radioYT.isChecked()
        self.urlEdit.setVisible(is_yt)
        self.fileEdit.setVisible(not is_yt)
        self.filePickBtn.setVisible(not is_yt)
        self._on_input_changed()

    def _browse_folder(self):
        current = self.folderEdit.text() or str(Path.home() / "Desktop")
        folder = QFileDialog.getExistingDirectory(self, get_text(self.lang, "export_folder"), current)
        if folder:
            self.folderEdit.setText(folder)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, get_text(self.lang, "upload_pc"), str(Path.home()),
            "Audio Files (*.wav *.mp3 *.m4a *.webm *.opus *.flac *.ogg);;All Files (*)",
        )
        if path:
            self.fileEdit.setText(path)
            self._on_input_changed()

    def _select_format(self, fmt: str):
        self._selected_format = fmt
        for f, btn in self._format_buttons.items():
            btn.setProperty("selected", "true" if f == fmt else "false")
            btn.setChecked(f == fmt)
            btn.style().unpolish(btn); btn.style().polish(btn)

    def _on_input_changed(self):
        self.goBtn.setEnabled(self._validate_input())
        self.input_changed.emit()

    def _validate_input(self) -> bool:
        if self.radioYT.isChecked():
            return is_valid_youtube_url(self.urlEdit.text().strip())
        path = self.fileEdit.text().strip()
        return bool(path) and os.path.isfile(path)

    def _on_go(self):
        if not self._validate_input():
            return

        time_range = None
        start_raw = self.timeStartEdit.text().strip()
        end_raw = self.timeEndEdit.text().strip()
        if start_raw or end_raw:
            try:
                start = _parse_clock(start_raw) if start_raw else 0.0
                end = _parse_clock(end_raw) if end_raw else None
                if end is not None and end <= start:
                    raise ValueError("End must be after start")
                time_range = (start, end)
            except ValueError as e:
                QMessageBox.warning(
                    self, get_text(self.lang, "section_time"),
                    get_text(self.lang, "error_invalid_time", msg=str(e)),
                )
                return

        solo_segments = []
        if self.soloCheckbox.isChecked():
            for seg in self._solo_segments:
                s = seg["start"].text().strip()
                e = seg["end"].text().strip()
                if not s and not e:
                    continue
                try:
                    a = _parse_clock(s); b = _parse_clock(e)
                    if b <= a:
                        raise ValueError("End must be after start")
                    solo_segments.append((a, b))
                except ValueError as err:
                    QMessageBox.warning(
                        self, get_text(self.lang, "section_solo"),
                        get_text(self.lang, "error_invalid_time", msg=str(err)),
                    )
                    return

        self.go_clicked.emit({
            "export_folder": self.folderEdit.text().strip(),
            "input_type": "youtube" if self.radioYT.isChecked() else "file",
            "input_value": (
                self.urlEdit.text().strip() if self.radioYT.isChecked()
                else self.fileEdit.text().strip()
            ),
            "format": self._selected_format,
            "clean_temp": True,
            "time_range": time_range,
            "solo_time_enabled": self.soloCheckbox.isChecked(),
            "solo_time_segments": solo_segments,
            "remove_reverb": self.removeReverbCheckbox.isChecked(),
            "remove_crowd": self.removeCrowdCheckbox.isChecked(),
        })

    # ── Solo segments ────────────────────────────────────────────────────
    def _toggle_solo_time(self, enabled: bool):
        self.soloContainer.setVisible(enabled)
        if enabled and not self._solo_segments:
            self._add_solo_segment()
        self._on_input_changed()

    def _add_solo_segment(self):
        seg_widget = QWidget()
        seg_layout = QHBoxLayout(seg_widget)
        seg_layout.setContentsMargins(0, 0, 0, 0)
        seg_layout.setSpacing(6)

        start_edit = QLineEdit(); start_edit.setPlaceholderText("1:50"); start_edit.setFixedWidth(80)
        arrow = QLabel("→"); arrow.setAlignment(Qt.AlignCenter)
        end_edit = QLineEdit(); end_edit.setPlaceholderText("3:00"); end_edit.setFixedWidth(80)
        rm_btn = QPushButton("✕"); rm_btn.setObjectName("smallButton"); rm_btn.setFixedWidth(30)

        seg_layout.addWidget(start_edit)
        seg_layout.addWidget(arrow)
        seg_layout.addWidget(end_edit)
        seg_layout.addWidget(rm_btn)
        seg_layout.addStretch()

        self.soloSegmentsLayout.addWidget(seg_widget)
        seg_data = {"widget": seg_widget, "start": start_edit, "end": end_edit}
        self._solo_segments.append(seg_data)
        rm_btn.clicked.connect(lambda: self._remove_solo_segment(seg_data))
        start_edit.textChanged.connect(self._on_input_changed)
        end_edit.textChanged.connect(self._on_input_changed)

    def _remove_solo_segment(self, seg_data: dict):
        seg_data["widget"].setParent(None)
        self._solo_segments.remove(seg_data)
        self._on_input_changed()

    # ── Public API ───────────────────────────────────────────────────────
    def set_processing(self, processing: bool):
        self.goBtn.setEnabled(not processing)
        self.goBtn.setText(
            get_text(self.lang, "go_button_processing") if processing
            else get_text(self.lang, "go_button")
        )
        for w in (
            self.browseBtn, self.filePickBtn, self.radioYT, self.radioPC,
            self.urlEdit, self.fileEdit, self.timeStartEdit, self.timeEndEdit,
            self.soloCheckbox, self.addSegmentBtn, self.repeatBtn,
            self.removeReverbCheckbox, self.removeCrowdCheckbox,
            *self._format_buttons.values(),
        ):
            w.setEnabled(not processing)
        if not processing:
            self._on_input_changed()

    def retranslate(self, lang: str):
        self.lang = lang
        t = lambda k, **kw: get_text(lang, k, **kw)

        self.titleLabel.setText("⚙️  " + t("section_input"))
        self.sourceLabel.setText(t("section_input"))
        self.radioYT.setText(t("youtube_link"))
        self.radioPC.setText(t("upload_pc"))
        self.urlEdit.setPlaceholderText(t("url_placeholder"))
        self.fileEdit.setPlaceholderText(t("upload_placeholder"))
        self.filePickBtn.setText("📂  " + t("browse"))
        self.browseBtn.setText("📁  " + t("browse"))
        self.folderLabel.setText(t("export_folder"))
        self.timeLabel.setText(t("section_time"))
        self.timeHint.setText(t("time_range_hint"))
        self.timeStartEdit.setPlaceholderText(t("time_start"))
        self.timeEndEdit.setPlaceholderText(t("time_end"))
        self.outputLabel.setText(t("output_format"))
        self.cleanupLabel.setText(t("section_cleanup"))
        self.removeReverbCheckbox.setText("💧  " + t("remove_reverb"))
        self.removeCrowdCheckbox.setText("👥  " + t("remove_crowd"))
        self._refresh_uvr_availability()
        self.soloCheckbox.setText("🎸  " + t("enable_solo_time"))
        self.soloTitleLabel.setText(t("solo_title"))
        self.addSegmentBtn.setText(t("add_segment"))
        self.repeatBtn.setToolTip(t("repeat_last"))
        self.goBtn.setText("🎸  " + t("go_button"))
        self._apply_direction()

    def _apply_direction(self):
        self.setLayoutDirection(Qt.RightToLeft if self.lang == "he" else Qt.LeftToRight)

    def get_export_folder(self) -> str:
        return self.folderEdit.text().strip()

    def get_time_range_raw(self) -> tuple[str, str]:
        return self.timeStartEdit.text().strip(), self.timeEndEdit.text().strip()

    # ── UVR availability ────────────────────────────────────────────────
    def _refresh_uvr_availability(self):
        t = lambda k: get_text(self.lang, k)
        problems: list[str] = []
        if not uvr_available():
            problems.append(t("uvr_pkg_missing"))
            self.removeReverbCheckbox.setEnabled(False)
            self.removeCrowdCheckbox.setEnabled(False)
        else:
            if not model_present(DEREVERB_MODEL):
                problems.append(t("uvr_dereverb_missing"))
                self.removeReverbCheckbox.setEnabled(False)
            else:
                self.removeReverbCheckbox.setEnabled(True)
            if not model_present(CROWD_MODEL):
                problems.append(t("uvr_crowd_missing"))
                self.removeCrowdCheckbox.setEnabled(False)
            else:
                self.removeCrowdCheckbox.setEnabled(True)
        self.uvrHint.setText("  •  ".join(problems) if problems else t("uvr_hint_ok"))

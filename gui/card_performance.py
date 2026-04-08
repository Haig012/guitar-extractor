"""
Card 1: Performance — Modern 2026 GUI design
"""
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QRadioButton, QButtonGroup,
    QFrame, QMessageBox, QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from utils.translations import get_text
from utils.helpers import is_valid_youtube_url
from utils.time_range import parse_time_range_line, _parse_clock


class DropLineEdit(QLineEdit):
    """LineEdit that accepts drag-and-drop of URLs and files."""
    file_dropped = Signal(str)
    url_dropped = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        mime = event.mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            if urls:
                url_str = urls[0].toString()
                if urls[0].isLocalFile():
                    local = urls[0].toLocalFile()
                    self.setText(local)
                    self.file_dropped.emit(local)
                else:
                    self.setText(url_str)
                    self.url_dropped.emit(url_str)
        elif mime.hasText():
            text = mime.text().strip()
            self.setText(text)
            if text.startswith("http"):
                self.url_dropped.emit(text)
        event.acceptProposedAction()


class PerformanceCard(QWidget):
    """Card 1: Performance settings + GO button."""

    go_clicked = Signal(dict)     # emits config dict
    check_deps = Signal()
    repeat_last = Signal()
    input_changed = Signal()

    FORMATS = ["wav", "mp3", "m4a", "webm", "opus"]

    def __init__(self, lang: str = "en", settings: dict = None, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.settings = settings or {}
        self._selected_format = self.settings.get("format", "wav")
        self._remove_crowd = bool(self.settings.get("remove_crowd", False))
        self._remove_reverb = bool(self.settings.get("remove_reverb", False))
        self._solo_segments = []

        self._build_ui()
        self.retranslate(lang)
        self._apply_layout_direction()

    def _t(self, key: str, **kw) -> str:
        return get_text(self.lang, key, **kw)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 20, 0, 20)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignHCenter)

        # Main card container
        card = QFrame()
        card.setObjectName("mainCard")
        card.setFixedWidth(650)
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 16, 24, 24)


        input_toggle = QHBoxLayout()
        input_toggle.setSpacing(24)
        self._input_group = QButtonGroup(self)
        self.radioYT = QRadioButton("YouTube Link")
        self.radioPC = QRadioButton("Local File")
        self.radioYT.setChecked(self.settings.get("last_input_type", "youtube") == "youtube")
        self.radioPC.setChecked(self.settings.get("last_input_type", "youtube") == "file")
        self._input_group.addButton(self.radioYT, 0)
        self._input_group.addButton(self.radioPC, 1)
        input_toggle.addWidget(self.radioYT)
        input_toggle.addWidget(self.radioPC)
        input_toggle.addStretch()
        layout.addLayout(input_toggle)

        # URL Input
        self.urlEdit = DropLineEdit()
        self.urlEdit.setPlaceholderText("Paste YouTube URL here...")
        self.urlEdit.setText(self.settings.get("last_input", ""))
        self.urlEdit.textChanged.connect(self._on_input_changed)
        self.urlEdit.url_dropped.connect(lambda u: self._on_input_changed())
        layout.addWidget(self.urlEdit)

        # File Input
        file_row = QHBoxLayout()
        self.fileEdit = QLineEdit()
        self.fileEdit.setPlaceholderText("Select audio file...")
        self.fileEdit.textChanged.connect(self._on_file_path_changed)
        self.filePickBtn = QPushButton("📂 Browse")
        self.filePickBtn.clicked.connect(self._browse_file)
        file_row.addWidget(self.fileEdit, 1)
        file_row.addWidget(self.filePickBtn)
        layout.addLayout(file_row)

        # Format info label
        self.formatInfoLabel = QLabel("")
        self.formatInfoLabel.setObjectName("formatInfo")
        self.formatInfoLabel.setVisible(False)
        layout.addWidget(self.formatInfoLabel)

        # ─────────────────────────────────────────────────────────────
        # SECTION 2: EXPORT FOLDER
        # ─────────────────────────────────────────────────────────────
        self.exportFolderLabel = self._section_label(self._t("export_folder"))
        layout.addWidget(self.exportFolderLabel)
        folder_row = QHBoxLayout()
        self.folderEdit = QLineEdit()
        default_folder = self.settings.get(
            "export_folder",
            str(Path.home() / "Desktop" / "exported_files")
        )
        self.folderEdit.setText(default_folder)
        self.folderEdit.setReadOnly(True)
        self.browseBtn = QPushButton("📁 Browse")
        self.browseBtn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folderEdit, 1)
        folder_row.addWidget(self.browseBtn)
        layout.addLayout(folder_row)

        # ─────────────────────────────────────────────────────────────
        # SECTION 3: TIME RANGE
        # ─────────────────────────────────────────────────────────────
        self.timeRangeLabel = self._section_label(self._t("time_range_label"))
        layout.addWidget(self.timeRangeLabel)
        time_row = QHBoxLayout()
        self.timeStartEdit = QLineEdit()
        self.timeStartEdit.setPlaceholderText("Start")
        self.timeEndEdit = QLineEdit()
        self.timeEndEdit.setPlaceholderText("End")
        time_sep = QLabel("—")
        time_sep.setAlignment(Qt.AlignCenter)
        time_row.addWidget(self.timeStartEdit, 1)
        time_row.addWidget(time_sep)
        time_row.addWidget(self.timeEndEdit, 1)
        layout.addLayout(time_row)

        # ─────────────────────────────────────────────────────────────
        # SECTION 4: SOLO TIME
        # ─────────────────────────────────────────────────────────────
        self.soloEnabledCheckbox = QCheckBox("🎸 " + self._t("enable_solo_time"))
        self.soloEnabledCheckbox.toggled.connect(self._toggle_solo_time)
        layout.addWidget(self.soloEnabledCheckbox)

        # Solo Time Container
        self.soloContainer = QFrame()
        self.soloContainer.setObjectName("soloContainer")
        solo_layout = QVBoxLayout(self.soloContainer)
        solo_layout.setSpacing(8)
        solo_layout.setContentsMargins(12, 12, 12, 12)

        self.soloTitleLabel = QLabel(self._t("solo_segments_title"))
        self.soloTitleLabel.setObjectName("soloTitle")
        solo_layout.addWidget(self.soloTitleLabel)

        self.soloSegmentsLayout = QVBoxLayout()
        self.soloSegmentsLayout.setSpacing(6)
        solo_layout.addLayout(self.soloSegmentsLayout)

        self.addSegmentBtn = QPushButton(self._t("add_segment"))
        self.addSegmentBtn.setObjectName("smallButton")
        self.addSegmentBtn.clicked.connect(self._add_solo_segment)
        solo_layout.addWidget(self.addSegmentBtn)

        layout.addWidget(self.soloContainer)
        self.soloContainer.setVisible(False)

        # ─────────────────────────────────────────────────────────────
        # SECTION 5: OUTPUT
        # ─────────────────────────────────────────────────────────────
        self.outputFormatLabel = self._section_label(self._t("output_format"))
        layout.addWidget(self.outputFormatLabel)
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(6)
        self._format_group = QButtonGroup(self)
        self._format_group.setExclusive(True)
        self._format_buttons = {}
        for fmt in self.FORMATS:
            btn = QPushButton(fmt.upper())
            btn.setObjectName("formatButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, f=fmt: self._select_format(f))
            self._format_group.addButton(btn)
            self._format_buttons[fmt] = btn
            fmt_row.addWidget(btn)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)
        self._select_format(self._selected_format)

        # Options
        options_layout = QVBoxLayout()
        options_layout.setSpacing(8)
        self.removeCrowdCheckbox = QCheckBox("Remove Crowd Noise")
        self.removeCrowdCheckbox.setChecked(self._remove_crowd)
        self.removeReverbCheckbox = QCheckBox("Remove Reverb")
        self.removeReverbCheckbox.setChecked(self._remove_reverb)
        options_layout.addWidget(self.removeCrowdCheckbox)
        options_layout.addWidget(self.removeReverbCheckbox)
        layout.addLayout(options_layout)

        # ─────────────────────────────────────────────────────────────
        # DIVIDER
        # ─────────────────────────────────────────────────────────────
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        layout.addWidget(div)

        # ─────────────────────────────────────────────────────────────
        # SECTION 6: ACTION
        # ─────────────────────────────────────────────────────────────
        self.goBtn = QPushButton("🎸 GO")
        self.goBtn.setObjectName("goButton")
        self.goBtn.clicked.connect(self._on_go)
        self.goBtn.setEnabled(False)
        layout.addWidget(self.goBtn, 0, Qt.AlignHCenter)

        # Status
        self.statusLabel = QLabel(self._t("status_ready"))
        self.statusLabel.setObjectName("statusLabel")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.statusLabel)

        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        layout.addWidget(self.progressBar)

        main_layout.addWidget(card)

        # Set initial visibility
        self._toggle_input_mode()
        self.radioYT.toggled.connect(self._toggle_input_mode)

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("sectionLabel")
        return lbl

    def _toggle_input_mode(self):
        is_yt = self.radioYT.isChecked()
        self.urlEdit.setVisible(is_yt)
        self.fileEdit.setVisible(not is_yt)
        self.filePickBtn.setVisible(not is_yt)
        self._on_input_changed()

    def _browse_folder(self):
        current = self.folderEdit.text() or str(Path.home() / "Desktop")
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder", current)
        if folder:
            self.folderEdit.setText(folder)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", str(Path.home()),
            "Audio Files (*.wav *.mp3 *.m4a *.webm *.opus *.flac *.ogg);;All Files (*)"
        )
        if path:
            self.fileEdit.setText(path)
            self._on_input_changed()

    def _on_file_path_changed(self):
        path = self.fileEdit.text().strip()
        if path and os.path.isfile(path):
            ext = Path(path).suffix.lower().lstrip('.')
            if ext in ['wav', 'mp3', 'm4a', 'webm', 'opus', 'flac', 'ogg']:
                self.formatInfoLabel.setText(f"✅ Detected format: {ext.upper()}")
                self.formatInfoLabel.setStyleSheet("color: #4CAF50;")
                self.formatInfoLabel.setVisible(True)
            else:
                self.formatInfoLabel.setText(f"⚠ Unsupported format: {ext.upper() if ext else 'unknown'}")
                self.formatInfoLabel.setStyleSheet("color: #ff6b6b;")
                self.formatInfoLabel.setVisible(True)
        else:
            self.formatInfoLabel.setVisible(False)
        self._on_input_changed()

    def _select_format(self, fmt: str):
        self._selected_format = fmt
        for f, btn in self._format_buttons.items():
            btn.setProperty("selected", "true" if f == fmt else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_input_changed(self):
        valid = self._validate_input()
        self.goBtn.setEnabled(valid)
        self.input_changed.emit()

    def _validate_input(self) -> bool:
        if self.radioYT.isChecked():
            url = self.urlEdit.text().strip()
            return is_valid_youtube_url(url)
        else:
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
                    raise ValueError("End time must be after start time")
                time_range = (start, end)
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Time Range", str(e))
                return

        solo_time_segments = []
        if self.soloEnabledCheckbox.isChecked():
            for seg in self._solo_segments:
                start_raw = seg["start"].text().strip()
                end_raw = seg["end"].text().strip()
                if not start_raw and not end_raw:
                    continue
                try:
                    start = _parse_clock(start_raw)
                    end = _parse_clock(end_raw)
                    if end <= start:
                        raise ValueError("End time must be after start time")
                    solo_time_segments.append((start, end))
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Solo Time", f"Segment error: {str(e)}")
                    return

        config = {
            "export_folder": self.folderEdit.text().strip(),
            "input_type": "youtube" if self.radioYT.isChecked() else "file",
            "input_value": (self.urlEdit.text().strip()
                            if self.radioYT.isChecked()
                            else self.fileEdit.text().strip()),
            "format": self._selected_format,
            "clean_temp": True,
            "time_range": time_range,
            "solo_time_enabled": self.soloEnabledCheckbox.isChecked(),
            "solo_time_segments": solo_time_segments,
            "remove_crowd": self.removeCrowdCheckbox.isChecked(),
            "remove_reverb": self.removeReverbCheckbox.isChecked(),
            "crowd_mode": "remove",
        }
        self.go_clicked.emit(config)

    def set_processing(self, processing: bool):
        """Disable/enable UI during processing."""
        self.goBtn.setEnabled(not processing)
        if processing:
            self.goBtn.setText("Processing...")
            self.progressBar.setVisible(True)
        else:
            self.goBtn.setText("🎸 GO")
            self.progressBar.setVisible(False)
            self._on_input_changed()

        for w in [self.browseBtn, self.filePickBtn, self.radioYT, self.radioPC,
                  self.fileEdit, self.timeStartEdit, self.timeEndEdit,
                  self.removeCrowdCheckbox, self.removeReverbCheckbox,
                  self.soloEnabledCheckbox, self.addSegmentBtn]:
            w.setEnabled(not processing)

    def set_status(self, text):
        self.statusLabel.setText(text)

    def set_progress(self, pct):
        self.progressBar.setValue(pct)

    def _toggle_solo_time(self, enabled: bool):
        self.soloContainer.setVisible(enabled)
        if enabled and len(self._solo_segments) == 0:
            self._add_solo_segment()
        self._on_input_changed()

    def _add_solo_segment(self):
        segment_widget = QWidget()
        segment_layout = QHBoxLayout(segment_widget)
        segment_layout.setContentsMargins(0, 0, 0, 0)
        segment_layout.setSpacing(6)

        start_edit = QLineEdit()
        start_edit.setPlaceholderText("1:50")
        start_edit.setFixedWidth(75)

        label = QLabel("→")
        label.setAlignment(Qt.AlignCenter)

        end_edit = QLineEdit()
        end_edit.setPlaceholderText("3:00")
        end_edit.setFixedWidth(75)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(30)
        remove_btn.setObjectName("smallButton")

        segment_layout.addWidget(start_edit)
        segment_layout.addWidget(label)
        segment_layout.addWidget(end_edit)
        segment_layout.addWidget(remove_btn)
        segment_layout.addStretch()

        self.soloSegmentsLayout.addWidget(segment_widget)

        segment_data = {
            "widget": segment_widget,
            "start": start_edit,
            "end": end_edit
        }

        self._solo_segments.append(segment_data)
        remove_btn.clicked.connect(lambda: self._remove_solo_segment(segment_data))
        start_edit.textChanged.connect(self._on_input_changed)
        end_edit.textChanged.connect(self._on_input_changed)

    def _remove_solo_segment(self, segment_data: dict):
        segment_data["widget"].setParent(None)
        self._solo_segments.remove(segment_data)
        self._on_input_changed()

    def _apply_layout_direction(self):
        direction = Qt.RightToLeft if self.lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)

    def retranslate(self, lang: str):
        self.lang = lang
        
        # Update all texts with proper translations
        self.radioYT.setText(self._t("youtube_link"))
        self.radioPC.setText(self._t("upload_pc"))
        self.urlEdit.setPlaceholderText(self._t("url_placeholder"))
        self.fileEdit.setPlaceholderText(self._t("upload_placeholder"))
        self.browseBtn.setText("📁  " + self._t("browse"))
        self.filePickBtn.setText("📂  " + self._t("browse"))
        self.exportFolderLabel.setText(self._t("export_folder"))
        self.timeRangeLabel.setText(self._t("time_range_label"))
        self.soloEnabledCheckbox.setText("🎸 " + self._t("enable_solo_time"))
        self.soloTitleLabel.setText(self._t("solo_segments_title"))
        self.addSegmentBtn.setText(self._t("add_segment"))
        self.outputFormatLabel.setText(self._t("output_format"))
        self.removeCrowdCheckbox.setText(self._t("remove_crowd_noise"))
        self.removeReverbCheckbox.setText(self._t("remove_reverb"))
        self.goBtn.setText(self._t("go_button"))
        self.statusLabel.setText(self._t("status_ready"))
        
        self._apply_layout_direction()

    def get_export_folder(self) -> str:
        return self.folderEdit.text().strip()

"""
Card 1: Performance — Export folder, input, format, GO button
"""
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QRadioButton, QButtonGroup,
    QFrame, QMessageBox, QCheckBox, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from utils.translations import get_text
from utils.helpers import is_valid_youtube_url
from utils.time_range import parse_time_range_line


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
        self._crowd_mode = self.settings.get("crowd_mode", "remove")
        self._format_buttons = {}
        self._build_ui()
        self._apply_layout_direction()

    def _t(self, key: str, **kw) -> str:
        return get_text(self.lang, key, **kw)

    def _build_ui(self):
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(24, 20, 24, 24)

        # ── Export Folder ──
        self.folderLabel = QLabel(self._t("export_folder"))
        self.folderLabel.setObjectName("sectionLabel")
        layout.addWidget(self.folderLabel)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)
        self.folderEdit = QLineEdit()
        self.folderEdit.setPlaceholderText(self._t("export_folder_placeholder"))
        default_folder = self.settings.get(
            "export_folder",
            str(Path.home() / "Desktop" / "exported_files")
        )
        self.folderEdit.setText(default_folder)
        self.folderEdit.setReadOnly(True)
        self.folderEdit.setToolTip(default_folder)

        self.browseBtn = QPushButton("📁  " + self._t("browse"))
        self.browseBtn.setObjectName("browseButton")
        self.browseBtn.setFixedWidth(110)
        self.browseBtn.clicked.connect(self._browse_folder)

        folder_row.addWidget(self.folderEdit)
        folder_row.addWidget(self.browseBtn)
        layout.addLayout(folder_row)

        # ── Input Source ──
        self.inputLabel = QLabel(self._t("input_source"))
        self.inputLabel.setObjectName("sectionLabel")
        layout.addWidget(self.inputLabel)

        # Radio toggle
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(16)
        self._input_group = QButtonGroup(self)
        self.radioYT = QRadioButton(self._t("youtube_link"))
        self.radioPC = QRadioButton(self._t("upload_pc"))
        self.radioYT.setChecked(self.settings.get("last_input_type", "youtube") == "youtube")
        self.radioPC.setChecked(self.settings.get("last_input_type", "youtube") == "file")
        self._input_group.addButton(self.radioYT, 0)
        self._input_group.addButton(self.radioPC, 1)
        toggle_row.addWidget(self.radioYT)
        toggle_row.addWidget(self.radioPC)
        toggle_row.addStretch()
        layout.addLayout(toggle_row)

        # URL input
        self.urlEdit = DropLineEdit()
        self.urlEdit.setPlaceholderText(self._t("url_placeholder"))
        self.urlEdit.setText(self.settings.get("last_input", ""))
        self.urlEdit.textChanged.connect(self._on_input_changed)
        self.urlEdit.url_dropped.connect(lambda u: self._on_input_changed())
        layout.addWidget(self.urlEdit)

        # File picker row
        file_row = QHBoxLayout()
        file_row.setSpacing(8)
        self.fileEdit = QLineEdit()
        self.fileEdit.setPlaceholderText(self._t("upload_placeholder"))
        self.fileEdit.textChanged.connect(self._on_file_path_changed)

        self.filePickBtn = QPushButton("📂  " + self._t("browse"))
        self.filePickBtn.setObjectName("browseButton")
        self.filePickBtn.setFixedWidth(110)
        self.filePickBtn.clicked.connect(self._browse_file)

        file_row.addWidget(self.fileEdit)
        file_row.addWidget(self.filePickBtn)

        # Format info label
        self.formatInfoLabel = QLabel("")
        self.formatInfoLabel.setObjectName("formatInfo")
        self.formatInfoLabel.setVisible(False)

        self.fileWidget = QWidget()
        file_layout = QVBoxLayout(self.fileWidget)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(4)
        file_layout.addLayout(file_row)
        file_layout.addWidget(self.formatInfoLabel)

        layout.addWidget(self.fileWidget)

        # Connect radio buttons to show/hide (called after goBtn is built)
        self.radioYT.toggled.connect(self._toggle_input_mode)

        # ── Format Selection ──
        self.formatLabel = QLabel(self._t("output_format"))
        self.formatLabel.setObjectName("sectionLabel")
        layout.addWidget(self.formatLabel)

        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(6)
        for fmt in self.FORMATS:
            btn = QPushButton(fmt)
            btn.setObjectName("formatButton")
            btn.setCheckable(False)
            btn.clicked.connect(lambda checked=False, f=fmt: self._select_format(f))
            self._format_buttons[fmt] = btn
            fmt_row.addWidget(btn)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)
        self._select_format(self._selected_format)

        # ── Optional time range (segment) ──
        self.timeRangeLabel = QLabel(self._t("time_range_label"))
        self.timeRangeLabel.setObjectName("sectionLabel")
        layout.addWidget(self.timeRangeLabel)

        self.timeRangeEdit = QLineEdit()
        self.timeRangeEdit.setPlaceholderText(self._t("time_range_placeholder"))
        self.timeRangeEdit.setText(self.settings.get("last_time_range", ""))
        self.timeRangeEdit.textChanged.connect(self._on_input_changed)
        layout.addWidget(self.timeRangeEdit)

        # ── Optional ONNX post-processing ──
        self.removeCrowdCheckbox = QCheckBox(self._t("remove_crowd_noise"))
        self.removeCrowdCheckbox.setChecked(self._remove_crowd)
        layout.addWidget(self.removeCrowdCheckbox)

        self.removeReverbCheckbox = QCheckBox(self._t("remove_reverb"))
        self.removeReverbCheckbox.setChecked(self._remove_reverb)
        layout.addWidget(self.removeReverbCheckbox)

        self.crowdModeLabel = QLabel(self._t("crowd_handling_mode"))
        self.crowdModeLabel.setObjectName("sectionLabel")
        layout.addWidget(self.crowdModeLabel)

        self.crowdModeCombo = QComboBox()
        self.crowdModeCombo.addItem(self._t("crowd_mode_remove"), "remove")
        self.crowdModeCombo.addItem(self._t("crowd_mode_separate"), "separate")
        self.crowdModeCombo.addItem(self._t("crowd_mode_mix_light"), "mix_light")
        ix = self.crowdModeCombo.findData(self._crowd_mode)
        self.crowdModeCombo.setCurrentIndex(ix if ix >= 0 else 0)
        layout.addWidget(self.crowdModeCombo)

        # ── Divider ──
        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.HLine)
        layout.addWidget(div)

        # ── GO + Action Buttons ──
        self.goBtn = QPushButton(self._t("go_button"))
        self.goBtn.setObjectName("goButton")
        self.goBtn.setMinimumHeight(50)
        self.goBtn.clicked.connect(self._on_go)
        self.goBtn.setEnabled(False)
        layout.addWidget(self.goBtn)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.repeatBtn = QPushButton(self._t("repeat_last"))
        self.repeatBtn.setObjectName("smallButton")
        self.repeatBtn.clicked.connect(self.repeat_last)

        self.checkDepsBtn = QPushButton(self._t("check_deps"))
        self.checkDepsBtn.setObjectName("smallButton")
        self.checkDepsBtn.clicked.connect(self.check_deps)

        btn_row.addWidget(self.repeatBtn)
        btn_row.addWidget(self.checkDepsBtn)
        layout.addLayout(btn_row)

        # Now that all widgets exist, set initial visibility
        self._toggle_input_mode()

    def _toggle_input_mode(self):
        is_yt = self.radioYT.isChecked()
        self.urlEdit.setVisible(is_yt)
        self.fileWidget.setVisible(not is_yt)
        self._on_input_changed()

    def _browse_folder(self):
        current = self.folderEdit.text() or str(Path.home() / "Desktop")
        folder = QFileDialog.getExistingDirectory(self, self._t("export_folder"), current)
        if folder:
            self.folderEdit.setText(folder)
            self.folderEdit.setToolTip(folder)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self._t("upload_pc"), str(Path.home()),
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
                self.formatInfoLabel.setText(f"📄 Detected format: {ext.upper()}")
                self.formatInfoLabel.setStyleSheet("color: green;")
                self.formatInfoLabel.setVisible(True)
            else:
                self.formatInfoLabel.setText(f"⚠ Unsupported format: {ext.upper() if ext else 'unknown'}")
                self.formatInfoLabel.setStyleSheet("color: red;")
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
        tr_raw = self.timeRangeEdit.text().strip()
        try:
            time_range = parse_time_range_line(tr_raw) if tr_raw else None
        except ValueError as e:
            QMessageBox.warning(self, self._t("time_range_invalid_title"), str(e))
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
            "remove_crowd": self.removeCrowdCheckbox.isChecked(),
            "remove_reverb": self.removeReverbCheckbox.isChecked(),
            "crowd_mode": self.crowdModeCombo.currentData(),
        }
        self.go_clicked.emit(config)

    def set_processing(self, processing: bool):
        """Disable/enable UI during processing."""
        self.goBtn.setEnabled(not processing)
        if processing:
            self.goBtn.setText(self._t("go_button_processing"))
        else:
            self.goBtn.setText(self._t("go_button"))
            self._on_input_changed()  # re-validate
        self.browseBtn.setEnabled(not processing)
        self.filePickBtn.setEnabled(not processing)
        self.radioYT.setEnabled(not processing)
        self.radioPC.setEnabled(not processing)
        self.fileEdit.setEnabled(not processing)
        self.timeRangeEdit.setEnabled(not processing)
        self.removeCrowdCheckbox.setEnabled(not processing)
        self.removeReverbCheckbox.setEnabled(not processing)
        self.crowdModeCombo.setEnabled(not processing)

    def retranslate(self, lang: str):
        self.lang = lang
        self.folderLabel.setText(self._t("export_folder"))
        self.folderEdit.setPlaceholderText(self._t("export_folder_placeholder"))
        self.browseBtn.setText("📁  " + self._t("browse"))
        self.inputLabel.setText(self._t("input_source"))
        self.radioYT.setText(self._t("youtube_link"))
        self.radioPC.setText(self._t("upload_pc"))
        self.urlEdit.setPlaceholderText(self._t("url_placeholder"))
        self.fileEdit.setPlaceholderText(self._t("upload_placeholder"))
        self.filePickBtn.setText("📂  " + self._t("browse"))
        self.formatLabel.setText(self._t("output_format"))
        self.timeRangeLabel.setText(self._t("time_range_label"))
        self.timeRangeEdit.setPlaceholderText(self._t("time_range_placeholder"))
        self.removeCrowdCheckbox.setText(self._t("remove_crowd_noise"))
        self.removeReverbCheckbox.setText(self._t("remove_reverb"))
        self.crowdModeLabel.setText(self._t("crowd_handling_mode"))
        self.crowdModeCombo.setItemText(0, self._t("crowd_mode_remove"))
        self.crowdModeCombo.setItemText(1, self._t("crowd_mode_separate"))
        self.crowdModeCombo.setItemText(2, self._t("crowd_mode_mix_light"))
        self.goBtn.setText(self._t("go_button"))
        self.repeatBtn.setText(self._t("repeat_last"))
        self.checkDepsBtn.setText(self._t("check_deps"))
        self._apply_layout_direction()

    def _apply_layout_direction(self):
        direction = Qt.RightToLeft if self.lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)

    def get_export_folder(self) -> str:
        return self.folderEdit.text().strip()

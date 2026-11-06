"""
Setup pane: source, tracks, extras, format, destination, Extract.

Designed to be read top to bottom with nothing to scroll. Optional inputs (Trim,
Solo) stay hidden until their chip is on, and long explanations live in tooltips.
A single line above Extract says what the app is waiting for.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from gui.icons import align_to_language, icon
from gui.styles import COLORS
from pipeline.uvr import (
    is_available as uvr_available,
    model_present,
    DEREVERB_MODEL,
    CROWD_MODEL,
)
from utils.helpers import is_valid_youtube_url
from utils.time_range import _parse_clock
from utils.translations import get_text

_SOLO_COLUMNS = 2
_SOLO_VISIBLE_ROWS = 2
_SOLO_ROW_HEIGHT = 32
_SOLO_ROW_GAP = 6


def _tip(text: str) -> str:
    """Rich text, because Qt only word-wraps tooltips that are rich text."""
    return f"<qt>{text}</qt>"


class _PathButton(QPushButton):
    """Shows a folder's name, elided to fit; the full path is in the tooltip."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path = ""

    def set_path(self, path: str):
        self._path = path
        self.setToolTip(path)
        self._refresh()

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._refresh()

    def _refresh(self):
        name = Path(self._path).name or self._path
        available = max(40, self.width() - self.iconSize().width() - 36)
        self.setText(QFontMetrics(self.font()).elidedText(name, Qt.ElideMiddle, available))


class PerformanceCard(QFrame):
    go_clicked = Signal(dict)
    height_changed = Signal()   # an optional row opened, closed, or grew

    FORMATS = ("wav", "mp3", "m4a", "webm", "opus")
    # The six stems htdemucs_6s produces, in display order.
    STEM_KEYS = ("guitar", "drums", "bass", "vocals", "piano", "other")
    TRACK_CHIPS = ("guitar", "backing", "drums", "bass", "vocals", "piano", "other")
    TRACK_COLUMNS = 4

    def __init__(self, lang: str = "en", settings: dict | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("pane")
        self.lang = lang
        self.settings = settings or {}
        self._selected_format = self.settings.get("format", "wav")
        self._error = ""
        self._solo_segments: list[dict] = []
        self._processing = False
        self._build_ui()
        self.retranslate(lang)

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 16)
        root.setSpacing(10)

        self.form = QWidget()
        form = QVBoxLayout(self.form)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(12)
        root.addWidget(self.form)
        root.addStretch(1)

        form.addLayout(self._build_source())
        form.addLayout(self._build_tracks())
        form.addLayout(self._build_extras())
        form.addWidget(self._build_trim())
        form.addWidget(self._build_solo())
        form.addLayout(self._build_output())

        self.hintLabel = QLabel()
        self.hintLabel.setObjectName("hint")
        self.hintLabel.setFixedHeight(18)
        root.addWidget(self.hintLabel)

        self.goBtn = QPushButton()
        self.goBtn.setObjectName("goButton")
        self.goBtn.setEnabled(False)
        self.goBtn.clicked.connect(self._on_go)
        root.addWidget(self.goBtn)

        self._refresh_uvr_availability()

    def _section(self, parent_layout: QVBoxLayout) -> QLabel:
        label = QLabel()
        label.setObjectName("sectionLabel")
        parent_layout.addWidget(label)
        return label

    def _chip(self, checked: bool = False) -> QPushButton:
        chip = QPushButton()
        chip.setObjectName("chip")
        chip.setCheckable(True)
        chip.setChecked(checked)
        return chip

    def _build_source(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(5)
        self.sourceLabel = self._section(col)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.sourceEdit = QLineEdit(self.settings.get("last_input", ""))
        # Drops are handled by the window, so they land anywhere, not just here.
        self.sourceEdit.setAcceptDrops(False)
        self.sourceEdit.textChanged.connect(self._on_input_changed)
        self.sourceEdit.returnPressed.connect(self._on_go)
        self.filePickBtn = QPushButton()
        self.filePickBtn.setIcon(icon("file", COLORS["text_dim"]))
        self.filePickBtn.clicked.connect(self._browse_file)
        row.addWidget(self.sourceEdit, 1)
        row.addWidget(self.filePickBtn)
        col.addLayout(row)
        return col

    def _build_tracks(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(5)
        self.tracksLabel = self._section(col)

        saved = self.settings.get("export_stems", ["guitar"])
        saved = set(saved if isinstance(saved, list) else ["guitar"])
        backing = bool(self.settings.get("export_backing", True))

        grid = QGridLayout()
        grid.setSpacing(6)
        self._stem_checks: dict[str, QPushButton] = {}
        for i, key in enumerate(self.TRACK_CHIPS):
            chip = self._chip(backing if key == "backing" else key in saved)
            chip.toggled.connect(self._on_input_changed)
            self._stem_checks[key] = chip
            grid.addWidget(chip, i // self.TRACK_COLUMNS, i % self.TRACK_COLUMNS)
        col.addLayout(grid)
        return col

    def _build_extras(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(5)
        self.extrasLabel = self._section(col)

        s = self.settings
        self.videoChip = self._chip(bool(s.get("export_video", False)))
        self.chordsChip = self._chip(bool(s.get("detect_chords", False)))
        self.reverbChip = self._chip(bool(s.get("remove_reverb", False)))
        self.crowdChip = self._chip(bool(s.get("remove_crowd", False)))
        has_trim = bool(s.get("last_time_range_start") or s.get("last_time_range_end"))
        self.trimChip = self._chip(has_trim)
        self.soloChip = self._chip(False)

        row = QHBoxLayout()
        row.setSpacing(6)
        for chip in (
            self.videoChip, self.chordsChip, self.reverbChip,
            self.crowdChip, self.trimChip, self.soloChip,
        ):
            row.addWidget(chip)
        col.addLayout(row)

        self.trimChip.toggled.connect(self._toggle_trim)
        self.soloChip.toggled.connect(self._toggle_solo)
        return col

    def _build_trim(self) -> QFrame:
        self.trimRow = QFrame()
        self.trimRow.setObjectName("inset")
        row = QHBoxLayout(self.trimRow)
        row.setContentsMargins(10, 5, 8, 5)
        row.setSpacing(6)
        self.trimLabel = QLabel()
        self.trimLabel.setObjectName("sectionLabel")
        self.timeStartEdit = self._time_edit(self.settings.get("last_time_range_start", ""))
        self.timeEndEdit = self._time_edit(self.settings.get("last_time_range_end", ""))
        self.timeStartEdit.textChanged.connect(self._on_input_changed)
        self.timeEndEdit.textChanged.connect(self._on_input_changed)
        row.addWidget(self.trimLabel)
        row.addStretch(1)
        row.addWidget(self.timeStartEdit)
        row.addWidget(QLabel("–"))
        row.addWidget(self.timeEndEdit)
        self.trimRow.setVisible(self.trimChip.isChecked())
        return self.trimRow

    def _build_solo(self) -> QFrame:
        self.soloRow = QFrame()
        self.soloRow.setObjectName("inset")
        col = QVBoxLayout(self.soloRow)
        col.setContentsMargins(10, 4, 8, 6)
        col.setSpacing(4)

        top = QHBoxLayout()
        self.soloLabel = QLabel()
        self.soloLabel.setObjectName("sectionLabel")
        self.addSegmentBtn = QPushButton()
        self.addSegmentBtn.setObjectName("ghost")
        self.addSegmentBtn.setIcon(icon("plus", COLORS["text_dim"]))
        self.addSegmentBtn.clicked.connect(self._add_solo_segment)
        top.addWidget(self.soloLabel)
        top.addStretch(1)
        top.addWidget(self.addSegmentBtn)
        col.addLayout(top)

        rows = QWidget()
        rows.setObjectName("soloRows")
        self._solo_grid = QGridLayout(rows)
        self._solo_grid.setContentsMargins(0, 0, 0, 0)
        self._solo_grid.setSpacing(_SOLO_ROW_GAP)
        self._solo_grid.setAlignment(Qt.AlignTop)
        self.soloScroll = QScrollArea()
        self.soloScroll.setObjectName("soloScroll")
        self.soloScroll.setWidgetResizable(True)
        self.soloScroll.setFrameShape(QFrame.NoFrame)
        self.soloScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.soloScroll.setWidget(rows)
        col.addWidget(self.soloScroll)

        self.soloRow.setVisible(False)
        return self.soloRow

    def _build_output(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        fmt_col = QVBoxLayout()
        fmt_col.setSpacing(5)
        self.outputLabel = self._section(fmt_col)
        segmented = QFrame()
        segmented.setObjectName("segmented")
        seg_row = QHBoxLayout(segmented)
        seg_row.setContentsMargins(2, 2, 2, 2)
        seg_row.setSpacing(0)
        self._format_group = QButtonGroup(self)
        self._format_buttons: dict[str, QPushButton] = {}
        for fmt in self.FORMATS:
            btn = QPushButton(fmt.upper())
            btn.setObjectName("segment")
            btn.setCheckable(True)
            btn.setChecked(fmt == self._selected_format)
            btn.clicked.connect(lambda _=False, f=fmt: self._select_format(f))
            self._format_group.addButton(btn)
            self._format_buttons[fmt] = btn
            seg_row.addWidget(btn)
        fmt_col.addWidget(segmented)
        row.addLayout(fmt_col)

        folder_col = QVBoxLayout()
        folder_col.setSpacing(5)
        self.folderLabel = self._section(folder_col)
        self.folderBtn = _PathButton()
        self.folderBtn.setIcon(icon("folder", COLORS["text_dim"]))
        self.folderBtn.clicked.connect(self._browse_folder)
        self._export_folder = self.settings.get(
            "export_folder", str(Path.home() / "Desktop" / "Backing Tracks"),
        )
        self.folderBtn.set_path(self._export_folder)
        folder_col.addWidget(self.folderBtn)
        row.addLayout(folder_col, 1)
        return row

    @staticmethod
    def _time_edit(text: str = "", width: int = 66) -> QLineEdit:
        edit = QLineEdit(text)
        edit.setObjectName("timeEdit")
        edit.setFixedWidth(width)
        edit.setAlignment(Qt.AlignCenter)
        edit.setLayoutDirection(Qt.LeftToRight)
        return edit

    # ── Behaviour ────────────────────────────────────────────────────────
    def _source(self) -> tuple[str | None, str]:
        """(kind, value), where kind is 'youtube', 'file', or None if unusable."""
        # Explorer's "Copy as path" wraps the path in double quotes.
        value = self.sourceEdit.text().strip().strip('"')
        if is_valid_youtube_url(value):
            return "youtube", value
        if value and os.path.isfile(value):
            return "file", value
        return None, value

    def _browse_folder(self):
        current = self._export_folder or str(Path.home() / "Desktop")
        folder = QFileDialog.getExistingDirectory(
            self, get_text(self.lang, "export_folder"), current,
        )
        if folder:
            self._export_folder = folder
            self.folderBtn.set_path(folder)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, get_text(self.lang, "browse"), str(Path.home()),
            "Audio / Video (*.wav *.mp3 *.m4a *.webm *.opus *.flac *.ogg "
            "*.mp4 *.mkv *.mov *.avi *.m4v);;All Files (*)",
        )
        if path:
            self.set_source(path)

    def set_source(self, value: str):
        self.sourceEdit.setText(value)

    def set_drag_active(self, active: bool):
        self.sourceEdit.setProperty("dragActive", "true" if active else "false")
        self.sourceEdit.style().unpolish(self.sourceEdit)
        self.sourceEdit.style().polish(self.sourceEdit)

    def _select_format(self, fmt: str):
        self._selected_format = fmt

    def _has_output(self) -> bool:
        return (
            any(chip.isChecked() for chip in self._stem_checks.values())
            or self.soloChip.isChecked()
        )

    def _on_input_changed(self, *_):
        self._error = ""
        self._refresh_hint()

    def _set_hint(self, text: str, state: str = ""):
        fm = QFontMetrics(self.hintLabel.font())
        width = max(200, self.width() - 32)
        self.hintLabel.setText(fm.elidedText(text, Qt.ElideMiddle, width))
        self.hintLabel.setProperty("state", state)
        self.hintLabel.style().unpolish(self.hintLabel)
        self.hintLabel.style().polish(self.hintLabel)

    def _refresh_hint(self):
        """Show what Extract is waiting for, and enable it only when ready."""
        t = lambda k, **kw: get_text(self.lang, k, **kw)
        kind, value = self._source()
        ready = False
        if not value:
            self._set_hint(t("hint_need_source"))
        elif kind is None:
            self._set_hint(t("hint_bad_source"), "err")
        elif not self._has_output():
            self._set_hint(t("error_no_tracks"), "warn")
        else:
            ready = True
            if self._error:
                self._set_hint(self._error, "err")
            elif kind == "youtube":
                self._set_hint(t("hint_ready_youtube"), "ok")
            else:
                self._set_hint(Path(value).name, "ok")
        if not self._processing:
            self.goBtn.setEnabled(ready)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self._refresh_hint()

    def _fail(self, message: str):
        self._error = message
        self._refresh_hint()

    def _on_go(self):
        kind, value = self._source()
        if kind is None or not self._has_output() or self._processing:
            return

        time_range = None
        start_raw, end_raw = self.get_time_range_raw()
        if start_raw or end_raw:
            try:
                start = _parse_clock(start_raw) if start_raw else 0.0
                end = _parse_clock(end_raw) if end_raw else None
                if end is not None and end <= start:
                    raise ValueError("End must be after start")
                time_range = (start, end)
            except ValueError as e:
                self._fail(get_text(self.lang, "error_invalid_time", msg=str(e)))
                return

        solo_on = self.soloChip.isChecked()
        solo_segments = []
        if solo_on:
            for seg in self._solo_segments:
                s = seg["start"].text().strip()
                e = seg["end"].text().strip()
                if not s and not e:
                    continue
                try:
                    a = _parse_clock(s)
                    b = _parse_clock(e)
                    if b <= a:
                        raise ValueError("End must be after start")
                    solo_segments.append((a, b))
                except ValueError as err:
                    self._fail(get_text(self.lang, "error_invalid_time", msg=str(err)))
                    return

        self.go_clicked.emit({
            "export_folder": self._export_folder.strip(),
            "input_type": kind,
            "input_value": value,
            "format": self._selected_format,
            "export_stems": [k for k in self.STEM_KEYS if self._stem_checks[k].isChecked()],
            "export_backing": self._stem_checks["backing"].isChecked(),
            "export_video": self.videoChip.isChecked(),
            "detect_chords": self.chordsChip.isChecked(),
            "clean_temp": True,
            "time_range": time_range,
            "solo_time_enabled": solo_on,
            "solo_time_segments": solo_segments,
            "remove_reverb": self.reverbChip.isChecked(),
            "remove_crowd": self.crowdChip.isChecked(),
        })

    # ── Optional rows ────────────────────────────────────────────────────
    def _toggle_trim(self, enabled: bool):
        self.trimRow.setVisible(enabled)
        self._on_input_changed()
        self.height_changed.emit()

    def _toggle_solo(self, enabled: bool):
        self.soloRow.setVisible(enabled)
        if enabled and not self._solo_segments:
            self._add_solo_segment()
        self._on_input_changed()
        self.height_changed.emit()

    def _add_solo_segment(self):
        seg_widget = QWidget()
        seg_widget.setLayoutDirection(Qt.LeftToRight)
        seg_layout = QHBoxLayout(seg_widget)
        seg_layout.setContentsMargins(0, 0, 0, 0)
        seg_layout.setSpacing(4)

        start_edit = self._time_edit(width=58)
        start_edit.setPlaceholderText("1:50")
        end_edit = self._time_edit(width=58)
        end_edit.setPlaceholderText("3:00")
        remove = QPushButton()
        remove.setObjectName("iconOnly")
        remove.setIcon(icon("close", COLORS["text_mute"]))
        seg_layout.addWidget(start_edit)
        seg_layout.addWidget(QLabel("–"))
        seg_layout.addWidget(end_edit)
        seg_layout.addWidget(remove)
        seg_layout.addStretch(1)

        seg_data = {"widget": seg_widget, "start": start_edit, "end": end_edit}
        self._solo_segments.append(seg_data)
        remove.clicked.connect(lambda: self._remove_solo_segment(seg_data))
        start_edit.textChanged.connect(self._on_input_changed)
        end_edit.textChanged.connect(self._on_input_changed)
        self._layout_solo_segments()
        start_edit.setFocus()

    def _remove_solo_segment(self, seg_data: dict):
        self._solo_segments.remove(seg_data)
        seg_data["widget"].setParent(None)
        seg_data["widget"].deleteLater()
        self._layout_solo_segments()
        self._on_input_changed()

    def _layout_solo_segments(self):
        for i, seg in enumerate(self._solo_segments):
            self._solo_grid.addWidget(
                seg["widget"], i // _SOLO_COLUMNS, i % _SOLO_COLUMNS,
            )
        rows = math.ceil(len(self._solo_segments) / _SOLO_COLUMNS)
        visible = max(1, min(rows, _SOLO_VISIBLE_ROWS))
        self.soloScroll.setFixedHeight(
            visible * _SOLO_ROW_HEIGHT + (visible - 1) * _SOLO_ROW_GAP,
        )
        self.height_changed.emit()

    # ── Public API ───────────────────────────────────────────────────────
    def set_processing(self, processing: bool):
        self._processing = processing
        self.form.setEnabled(not processing)
        self.goBtn.setText(get_text(
            self.lang, "go_button_processing" if processing else "go_button",
        ))
        if processing:
            self.goBtn.setEnabled(False)
        else:
            self._refresh_hint()

    def retranslate(self, lang: str):
        self.lang = lang
        t = lambda k, **kw: get_text(lang, k, **kw)

        self.sourceLabel.setText(t("section_input"))
        self.sourceEdit.setPlaceholderText(t("source_placeholder"))
        self.filePickBtn.setText(t("browse"))

        self.tracksLabel.setText(t("section_tracks"))
        for key, chip in self._stem_checks.items():
            chip.setText(t(f"track_{key}"))
            chip.setToolTip(_tip(t("tracks_hint")))
        self._stem_checks["backing"].setToolTip(_tip(t("tip_backing")))

        self.extrasLabel.setText(t("section_extras"))
        self.videoChip.setText(t("chip_video"))
        self.videoChip.setToolTip(_tip(f"<b>{t('export_video')}</b><br>{t('export_video_hint')}"))
        self.chordsChip.setText(t("chip_chords"))
        self.chordsChip.setToolTip(_tip(f"<b>{t('detect_chords')}</b><br>{t('detect_chords_hint')}"))
        self.reverbChip.setText(t("chip_reverb"))
        self.crowdChip.setText(t("chip_crowd"))
        self.trimChip.setText(t("chip_trim"))
        self.trimChip.setToolTip(_tip(f"<b>{t('section_time')}</b><br>{t('time_range_hint')}"))
        self.soloChip.setText(t("chip_solo"))
        self.soloChip.setToolTip(_tip(t("enable_solo_time")))
        self._refresh_uvr_availability()

        self.trimLabel.setText(t("section_time"))
        self.timeStartEdit.setPlaceholderText(t("time_start"))
        self.timeEndEdit.setPlaceholderText(t("time_end"))
        self.soloLabel.setText(t("solo_title"))
        self.addSegmentBtn.setText(t("add_segment"))

        self.outputLabel.setText(t("output_format"))
        self.folderLabel.setText(t("export_folder"))
        self.goBtn.setText(t("go_button_processing" if self._processing else "go_button"))
        align_to_language(lang, self.hintLabel)
        self._refresh_hint()

    def options_open(self) -> bool:
        return self.trimChip.isChecked() or self.soloChip.isChecked()

    def get_time_range_raw(self) -> tuple[str, str]:
        if not self.trimChip.isChecked():
            return "", ""
        return self.timeStartEdit.text().strip(), self.timeEndEdit.text().strip()

    # ── UVR availability ────────────────────────────────────────────────
    def _refresh_uvr_availability(self):
        t = lambda k: get_text(self.lang, k)
        installed = uvr_available()
        for chip, model, title, missing in (
            (self.reverbChip, DEREVERB_MODEL, "remove_reverb", "uvr_dereverb_missing"),
            (self.crowdChip, CROWD_MODEL, "remove_crowd", "uvr_crowd_missing"),
        ):
            usable = installed and model_present(model)
            chip.setEnabled(usable)
            if not usable:
                chip.setChecked(False)
            note = t("uvr_hint_ok") if usable else t("uvr_pkg_missing" if not installed else missing)
            chip.setToolTip(_tip(f"<b>{t(title)}</b><br>{note}"))

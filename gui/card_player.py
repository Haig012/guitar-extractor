"""
Built-in audio player.

What a guitar player actually wants after extraction:
    • Switch between any exported track (guitar / drums / bass / vocals / piano /
      other / no-guitar backing / solo mix / crowd / reverb)
    • Loop a chunk of the track to practise over
    • Slow it down to transcribe or learn by ear (Qt native playback rate)
    • Scrub the timeline

The track buttons are built dynamically from whatever the pipeline produced, so
the player only ever shows tracks that actually exist on disk.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal, QRect, QUrl, QTimer
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QStyle,
    QVBoxLayout, QWidget,
)

from gui.icons import align_to_language, icon
from gui.styles import COLORS
from pipeline.chords import parse_lrc
from utils.translations import get_text


class _SeekSlider(QSlider):
    """Timeline: click anywhere to jump, and the A–B loop is drawn on the groove."""

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self._loop: tuple[int | None, int | None] = (None, None)

    def set_loop(self, a: int | None, b: int | None):
        self._loop = (a, b)
        self.update()

    def _x_for(self, value: int) -> int:
        handle = 12  # matches the QSS handle width
        span = self.width() - handle
        x = QStyle.sliderPositionFromValue(self.minimum(), self.maximum(), value, span)
        return x + handle // 2

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.maximum() > 0:
            value = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(), int(ev.position().x()), self.width(),
            )
            self.setValue(value)
            self.sliderMoved.emit(value)
        super().mousePressEvent(ev)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        a, b = self._loop
        if self.maximum() <= 0 or (a is None and b is None):
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(COLORS["ok"])
        mid = self.height() // 2
        if a is not None and b is not None and b > a:
            band = QColor(color)
            band.setAlpha(150)
            x1, x2 = self._x_for(a), self._x_for(b)
            painter.setPen(Qt.NoPen)
            painter.setBrush(band)
            painter.drawRect(QRect(x1, mid - 3, x2 - x1, 6))
        painter.setPen(color)
        for point in (a, b):
            if point is not None:
                x = self._x_for(point)
                painter.drawLine(x, mid - 7, x, mid + 7)


class PlayerCard(QWidget):
    """Multi-track player with loop + tempo controls."""

    open_folder_requested = Signal(str)
    show_log_requested = Signal()

    TEMPO_MIN = 50    # 0.50x
    TEMPO_MAX = 150   # 1.50x

    # (result key → translation key), in display order. Only keys present in the
    # pipeline result get a button — everything else (folder, chords, video) is
    # ignored, so this doubles as the audio-track whitelist.
    TRACK_ORDER = (
        ("guitar", "player_guitar"),
        ("no_guitar", "player_backing"),
        ("solo", "player_solo"),
        ("drums", "player_drums"),
        ("bass", "player_bass"),
        ("vocals", "player_vocals"),
        ("piano", "player_piano"),
        ("other", "player_other"),
        ("crowd", "player_crowd"),
        ("reverb_echo", "player_reverb"),
        ("dry", "player_dry"),
        ("clean", "player_clean"),
    )
    BTNS_PER_ROW = 4

    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self._tracks: dict[str, str] = {}         # active key → path
        self._track_buttons: dict[str, QPushButton] = {}
        self._current_key: str | None = None
        self._folder = ""
        self._loop_a_ms: int | None = None
        self._loop_b_ms: int | None = None
        self._user_seeking = False
        self._chords: list[tuple[float, str]] = []  # (start_seconds, label)
        # Where to resume once a newly selected track has finished loading.
        self._pending: tuple[int, bool] | None = None

        self._player = QMediaPlayer(self)
        self._audio_out = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_out)
        self._audio_out.setVolume(0.85)

        self._loop_timer = QTimer(self)
        self._loop_timer.setInterval(120)
        self._loop_timer.timeout.connect(self._enforce_loop)

        self._build_ui()
        self._wire_player()
        self.retranslate(lang)
        self.set_tracks({})

    # ── Public API ────────────────────────────────────────────────────────
    @property
    def has_tracks(self) -> bool:
        return bool(self._tracks)

    def set_tracks(self, tracks: dict):
        """Accepts the worker's full result dict and builds a button per track."""
        self._folder = tracks.get("folder", "")
        self._load_chords(tracks.get("chords_lrc"))
        # Keep only known audio tracks that actually exist on disk.
        self._tracks = {
            key: tracks[key]
            for key, _t in self.TRACK_ORDER
            if tracks.get(key) and os.path.isfile(tracks[key])
        }
        self._clear_loop()
        self._set_song_name(os.path.basename(self._folder).replace("_", " "))
        self._rebuild_track_buttons()
        if not self._tracks:
            # Release the file so a re-run can overwrite it.
            self._player.setSource(QUrl())
            return
        if self._current_key not in self._tracks:
            self._current_key = next(iter(self._tracks))
        self._select_track(self._current_key)

    def _set_song_name(self, name: str):
        fm = QFontMetrics(self.songLabel.font())
        self.songLabel.setText(fm.elidedText(name, Qt.ElideMiddle, 280))
        self.songLabel.setToolTip(name)

    def _load_chords(self, lrc_path):
        raw = parse_lrc(lrc_path) if lrc_path and os.path.isfile(lrc_path) else []
        self._chords = [(t, lab) for t, lab in raw if lab != "N.C."]
        self.chordRow.setVisible(bool(self._chords))
        self._update_chord_label(self._player.position())

    def _rebuild_track_buttons(self):
        """Tear down and recreate the track-switcher buttons for current tracks."""
        for btn in self._track_buttons.values():
            self._track_group.removeButton(btn)
            btn.setParent(None)
            btn.deleteLater()
        self._track_buttons = {}

        idx = 0
        for key, tkey in self.TRACK_ORDER:
            if key not in self._tracks:
                continue
            btn = QPushButton(get_text(self.lang, tkey))
            btn.setObjectName("chip")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked=False, k=key: self._select_track(k))
            self._track_group.addButton(btn)
            self._tracks_grid.addWidget(btn, idx // self.BTNS_PER_ROW, idx % self.BTNS_PER_ROW)
            self._track_buttons[key] = btn
            idx += 1

    def retranslate(self, lang: str):
        self.lang = lang
        t = lambda k: get_text(lang, k)
        align_to_language(lang, self.songLabel)
        self.titleLabel.setText(t("section_player"))
        for key, tkey in self.TRACK_ORDER:
            btn = self._track_buttons.get(key)
            if btn:
                btn.setText(t(tkey))
        self.tempoLabel.setText(t("tempo"))
        self.openFolderBtn.setText(t("open_folder"))
        self.logBtn.setText(t("show_log"))
        self.setABtn.setToolTip(t("loop_set_a"))
        self.setBBtn.setToolTip(t("loop_set_b"))
        self.clearLoopBtn.setToolTip(t("loop_clear"))
        self.tempoValue.setToolTip(t("tempo_reset"))

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 18)
        root.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(4)
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self.titleLabel = QLabel()
        self.titleLabel.setObjectName("paneTitle")
        self.songLabel = QLabel()
        self.songLabel.setObjectName("paneSubtitle")
        title_col.addWidget(self.titleLabel)
        title_col.addWidget(self.songLabel)
        self.logBtn = QPushButton()
        self.logBtn.setObjectName("ghost")
        self.logBtn.setIcon(icon("log", COLORS["text_dim"]))
        self.logBtn.clicked.connect(self.show_log_requested.emit)
        self.openFolderBtn = QPushButton()
        self.openFolderBtn.setObjectName("ghost")
        self.openFolderBtn.setIcon(icon("folder", COLORS["text_dim"]))
        self.openFolderBtn.clicked.connect(self._open_folder)
        title_row.addLayout(title_col, 1)
        title_row.addWidget(self.logBtn, 0, Qt.AlignTop)
        title_row.addWidget(self.openFolderBtn, 0, Qt.AlignTop)
        root.addLayout(title_row)

        # Track switcher — dynamic grid.
        self._track_group = QButtonGroup(self)
        self._track_group.setExclusive(True)
        self._tracks_grid = QGridLayout()
        self._tracks_grid.setSpacing(6)
        root.addLayout(self._tracks_grid)

        root.addStretch(1)

        # Current chord (only visible when a chord chart was produced)
        self.chordRow = QWidget()
        chord_layout = QHBoxLayout(self.chordRow)
        chord_layout.setContentsMargins(0, 0, 0, 0)
        chord_layout.setSpacing(14)
        self.chordValue = QLabel("—")
        self.chordValue.setObjectName("chordValue")
        self.chordNext = QLabel("")
        self.chordNext.setObjectName("chordNext")
        chord_layout.addStretch(1)
        chord_layout.addWidget(self.chordValue)
        chord_layout.addWidget(self.chordNext)
        chord_layout.addStretch(1)
        root.addWidget(self.chordRow)
        self.chordRow.setVisible(False)

        root.addStretch(1)

        # Media controls read left-to-right in every language.
        transport = QWidget()
        transport.setLayoutDirection(Qt.LeftToRight)
        tcol = QVBoxLayout(transport)
        tcol.setContentsMargins(0, 0, 0, 0)
        tcol.setSpacing(10)
        root.addWidget(transport)

        seek_row = QHBoxLayout()
        seek_row.setSpacing(8)
        self.timeCurLabel = QLabel("0:00")
        self.timeCurLabel.setObjectName("timeLabel")
        self.seekSlider = _SeekSlider()
        self.seekSlider.setRange(0, 0)
        self.seekSlider.sliderPressed.connect(lambda: setattr(self, "_user_seeking", True))
        self.seekSlider.sliderReleased.connect(self._on_seek_release)
        self.seekSlider.sliderMoved.connect(self._on_seek_move)
        self.timeTotalLabel = QLabel("0:00")
        self.timeTotalLabel.setObjectName("timeLabel")
        seek_row.addWidget(self.timeCurLabel)
        seek_row.addWidget(self.seekSlider, 1)
        seek_row.addWidget(self.timeTotalLabel)
        tcol.addLayout(seek_row)

        controls = QHBoxLayout()
        controls.setSpacing(6)

        self.playBtn = QPushButton()
        self.playBtn.setObjectName("playBtn")
        self._play_icon = icon("play", COLORS["on_accent"])
        self._pause_icon = icon("pause", COLORS["on_accent"])
        self.playBtn.setIcon(self._play_icon)
        self.playBtn.clicked.connect(self._toggle_play)
        controls.addWidget(self.playBtn)
        controls.addSpacing(8)

        self.setABtn = QPushButton("A")
        self.setBBtn = QPushButton("B")
        for btn in (self.setABtn, self.setBBtn):
            btn.setObjectName("chip")
            btn.setCheckable(True)
            btn.setMinimumWidth(62)
            controls.addWidget(btn)
        self.setABtn.clicked.connect(self._set_loop_a)
        self.setBBtn.clicked.connect(self._set_loop_b)
        self.clearLoopBtn = QPushButton()
        self.clearLoopBtn.setObjectName("iconOnly")
        self.clearLoopBtn.setIcon(icon("close", COLORS["text_mute"]))
        self.clearLoopBtn.clicked.connect(self._clear_loop)
        controls.addWidget(self.clearLoopBtn)
        controls.addStretch(1)

        volume_icon = QLabel()
        volume_icon.setPixmap(icon("volume", COLORS["text_mute"]).pixmap(16, 16))
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(85)
        self.volumeSlider.setFixedWidth(84)
        self.volumeSlider.valueChanged.connect(lambda v: self._audio_out.setVolume(v / 100.0))
        controls.addWidget(volume_icon)
        controls.addWidget(self.volumeSlider)
        tcol.addLayout(controls)

        tempo_row = QHBoxLayout()
        tempo_row.setSpacing(8)
        self.tempoLabel = QLabel()
        self.tempoLabel.setObjectName("sectionLabel")
        self.tempoSlider = QSlider(Qt.Horizontal)
        self.tempoSlider.setRange(self.TEMPO_MIN, self.TEMPO_MAX)
        self.tempoSlider.setValue(100)
        self.tempoSlider.valueChanged.connect(self._on_tempo_changed)
        self.tempoValue = QPushButton("1.00×")
        self.tempoValue.setObjectName("tempoValue")
        self.tempoValue.clicked.connect(lambda: self.tempoSlider.setValue(100))
        tempo_row.addWidget(self.tempoLabel)
        tempo_row.addWidget(self.tempoSlider, 1)
        tempo_row.addWidget(self.tempoValue)
        tcol.addLayout(tempo_row)

    # ── Player wiring ─────────────────────────────────────────────────────
    def _wire_player(self):
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status)

    def _select_track(self, key: str):
        path = self._tracks.get(key)
        if not path:
            return
        playing = self._player.playbackState() == QMediaPlayer.PlayingState
        position = self._player.position()

        self._current_key = key
        self._player.stop()   # reports LoadedMedia for the old file, so arm after it
        self._pending = (position, playing)
        self._player.setSource(QUrl.fromLocalFile(os.path.abspath(path)))

        for k, btn in self._track_buttons.items():
            btn.setChecked(k == key)

    def _on_media_status(self, status):
        # All tracks derive from the same (trimmed) source, so they share a
        # duration. The source loads asynchronously, and a seek issued before it
        # finishes is dropped, so the play-head is restored here.
        if status != QMediaPlayer.LoadedMedia or self._pending is None:
            return
        position, playing = self._pending
        self._pending = None
        if position > 0:
            self._player.setPosition(position)
        if playing:
            self._player.play()

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            if self._player.source().isEmpty() and self._tracks:
                self._select_track(next(iter(self._tracks)))
            self._player.play()

    def _on_state_changed(self, state):
        playing = state == QMediaPlayer.PlayingState
        self.playBtn.setIcon(self._pause_icon if playing else self._play_icon)

    def _on_duration_changed(self, ms: int):
        self.seekSlider.setRange(0, ms)
        self.timeTotalLabel.setText(_fmt_ms(ms))

    def _on_position_changed(self, ms: int):
        if not self._user_seeking:
            self.seekSlider.setValue(ms)
            self.timeCurLabel.setText(_fmt_ms(ms))
            self._update_chord_label(ms)

    def _update_chord_label(self, ms: int):
        if not self._chords:
            return
        t = ms / 1000.0
        cur = "—"
        nexts: list[str] = []
        for i, (start, label) in enumerate(self._chords):
            if start <= t:
                cur = label
                nexts = [lab for _, lab in self._chords[i + 1:i + 3]]
            else:
                break
        self.chordValue.setText(cur)
        self.chordNext.setText("   ".join(nexts))

    def _on_seek_move(self, v: int):
        self.timeCurLabel.setText(_fmt_ms(v))
        self._update_chord_label(v)

    def _on_seek_release(self):
        self._user_seeking = False
        self._player.setPosition(self.seekSlider.value())

    # ── Loop ──────────────────────────────────────────────────────────────
    def _set_loop_a(self):
        self._loop_a_ms = self._player.position()
        self._update_loop_state()

    def _set_loop_b(self):
        self._loop_b_ms = self._player.position()
        self._update_loop_state()

    def _clear_loop(self):
        self._loop_a_ms = None
        self._loop_b_ms = None
        self._update_loop_state()

    def _update_loop_state(self):
        a, b = self._loop_a_ms, self._loop_b_ms
        self.setABtn.setText(f"A  {_fmt_ms(a)}" if a is not None else "A")
        self.setBBtn.setText(f"B  {_fmt_ms(b)}" if b is not None else "B")
        self.setABtn.setChecked(a is not None)
        self.setBBtn.setChecked(b is not None)
        self.clearLoopBtn.setVisible(a is not None or b is not None)
        self.seekSlider.set_loop(a, b)
        if a is not None and b is not None and b > a:
            self._loop_timer.start()
        else:
            self._loop_timer.stop()

    def _enforce_loop(self):
        if self._loop_a_ms is None or self._loop_b_ms is None:
            return
        pos = self._player.position()
        if pos >= self._loop_b_ms:
            self._player.setPosition(self._loop_a_ms)

    # ── Tempo ─────────────────────────────────────────────────────────────
    def _on_tempo_changed(self, v: int):
        rate = v / 100.0
        self.tempoValue.setText(f"{rate:.2f}×")
        self._player.setPlaybackRate(rate)

    # ── Misc ──────────────────────────────────────────────────────────────
    def _open_folder(self):
        if self._folder and os.path.exists(self._folder):
            self.open_folder_requested.emit(self._folder)

    def stop(self):
        self._player.stop()

    # Expose play toggle for global shortcut
    def toggle_play_pause(self):
        self._toggle_play()


def _fmt_ms(ms: int) -> str:
    if ms <= 0:
        return "0:00"
    total_s = ms // 1000
    m, s = divmod(total_s, 60)
    return f"{m}:{s:02d}"

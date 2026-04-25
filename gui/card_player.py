"""
Built-in audio player.

What a guitar player actually wants after extraction:
    • Switch between *isolated guitar*, *no-guitar backing*, and (optionally) *solo mix*
    • Loop a chunk of the track to practise over
    • Slow it down to transcribe or learn by ear (Qt native playback rate)
    • Scrub the timeline

This card stays invisible until the pipeline finishes and hands it a set of files.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QSizePolicy, QButtonGroup,
)

from utils.translations import get_text


class PlayerCard(QWidget):
    """A/B/C track player with loop + tempo controls."""

    open_folder_requested = Signal(str)

    TEMPO_MIN = 50    # 0.50x
    TEMPO_MAX = 150   # 1.50x

    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self._all_tracks: dict[str, str] = {}     # full set (incl. *_dry, *_clean, *_reverb, *_crowd)
        self._tracks: dict[str, str] = {}         # active 3 buttons map → path
        self._current_key: str | None = None
        self._loop_a_ms: int | None = None
        self._loop_b_ms: int | None = None
        self._user_seeking = False
        self._prefer_clean = True

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
    def set_tracks(self, tracks: dict):
        """
        Accepts the worker's full result dict. Picks per-button paths preferring
        cleaned variants (``*_dry``, ``*_clean``) when ``prefer_clean`` is on.
        """
        self._all_tracks = {k: v for k, v in tracks.items() if v and k != "folder"}
        self._folder = tracks.get("folder", "")
        self._refresh_buttons()
        self.cleanToggle.setVisible(self._has_any_cleaned())

    def _has_any_cleaned(self) -> bool:
        return any(
            k.endswith(("_dry", "_clean")) for k in self._all_tracks
        )

    def _resolve(self, base: str) -> str | None:
        """Pick best path for ``base`` (guitar / no_guitar / solo)."""
        if self._prefer_clean:
            # Prefer fully cleaned (dry+clean) → dry → clean → raw.
            for suffix in ("_dry_clean", "_clean_dry", "_dry", "_clean"):
                p = self._all_tracks.get(base + suffix)
                if p:
                    return p
        return self._all_tracks.get(base)

    def _refresh_buttons(self):
        self._tracks = {}
        for key in ("guitar", "no_guitar", "solo"):
            p = self._resolve(key)
            if p:
                self._tracks[key] = p

        has_any = bool(self._tracks)
        self.setVisible(has_any)
        if not has_any:
            return

        self.btnGuitar.setEnabled("guitar" in self._tracks)
        self.btnBacking.setEnabled("no_guitar" in self._tracks)
        self.btnSolo.setEnabled("solo" in self._tracks)

        # Keep current button if still valid; otherwise pick first.
        if self._current_key not in self._tracks:
            self._current_key = next(iter(self._tracks))
        self._select_track(self._current_key)

    def retranslate(self, lang: str):
        self.lang = lang
        self.titleLabel.setText("🎧  " + get_text(lang, "section_player"))
        self.btnGuitar.setText(get_text(lang, "player_guitar"))
        self.btnBacking.setText(get_text(lang, "player_backing"))
        self.btnSolo.setText(get_text(lang, "player_solo"))
        self.tempoLabel.setText(get_text(lang, "tempo"))
        self.volumeLabel.setText(get_text(lang, "volume"))
        self.openFolderBtn.setText("📂  " + get_text(lang, "open_folder"))
        direction = Qt.RightToLeft if lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setProperty("class", "card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 22)
        root.setSpacing(12)

        # Title row
        self.titleLabel = QLabel()
        self.titleLabel.setObjectName("cardTitle")
        root.addWidget(self.titleLabel)

        # Track switcher
        track_row = QHBoxLayout()
        track_row.setSpacing(8)
        self._track_group = QButtonGroup(self)
        self._track_group.setExclusive(True)

        self.btnGuitar = self._make_track_btn("guitar")
        self.btnBacking = self._make_track_btn("no_guitar")
        self.btnSolo = self._make_track_btn("solo")
        for b in (self.btnGuitar, self.btnBacking, self.btnSolo):
            self._track_group.addButton(b)
            track_row.addWidget(b)
        track_row.addStretch()

        self.cleanToggle = QPushButton("✨")
        self.cleanToggle.setObjectName("smallButton")
        self.cleanToggle.setCheckable(True)
        self.cleanToggle.setChecked(True)
        self.cleanToggle.setToolTip("Use cleaned (de-reverb / de-crowd) variant when available")
        self.cleanToggle.toggled.connect(self._on_clean_toggle)
        self.cleanToggle.setVisible(False)
        track_row.addWidget(self.cleanToggle)

        self.openFolderBtn = QPushButton()
        self.openFolderBtn.setObjectName("smallButton")
        self.openFolderBtn.clicked.connect(self._open_folder)
        track_row.addWidget(self.openFolderBtn)
        root.addLayout(track_row)

        # Transport: play button + time labels + seek
        transport = QHBoxLayout()
        transport.setSpacing(14)

        self.playBtn = QPushButton("▶")
        self.playBtn.setObjectName("playBtn")
        self.playBtn.clicked.connect(self._toggle_play)
        transport.addWidget(self.playBtn)

        # Seek column
        seek_col = QVBoxLayout()
        seek_col.setSpacing(4)

        seek_row = QHBoxLayout()
        seek_row.setSpacing(10)
        self.timeCurLabel = QLabel("0:00")
        self.timeCurLabel.setObjectName("timeLabel")
        self.seekSlider = QSlider(Qt.Horizontal)
        self.seekSlider.setRange(0, 0)
        self.seekSlider.sliderPressed.connect(lambda: setattr(self, "_user_seeking", True))
        self.seekSlider.sliderReleased.connect(self._on_seek_release)
        self.seekSlider.sliderMoved.connect(self._on_seek_move)
        self.timeTotalLabel = QLabel("0:00")
        self.timeTotalLabel.setObjectName("timeLabel")
        self.timeTotalLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        seek_row.addWidget(self.timeCurLabel)
        seek_row.addWidget(self.seekSlider, 1)
        seek_row.addWidget(self.timeTotalLabel)
        seek_col.addLayout(seek_row)

        # Loop controls
        loop_row = QHBoxLayout()
        loop_row.setSpacing(8)
        self.loopALabel = QLabel("A: —")
        self.loopALabel.setObjectName("timeLabel")
        self.loopBLabel = QLabel("B: —")
        self.loopBLabel.setObjectName("timeLabel")
        self.setABtn = QPushButton("Set A")
        self.setBBtn = QPushButton("Set B")
        self.clearLoopBtn = QPushButton("Clear loop")
        for b in (self.setABtn, self.setBBtn, self.clearLoopBtn):
            b.setObjectName("smallButton")
        self.setABtn.clicked.connect(self._set_loop_a)
        self.setBBtn.clicked.connect(self._set_loop_b)
        self.clearLoopBtn.clicked.connect(self._clear_loop)

        loop_row.addWidget(QLabel("🔁"))
        loop_row.addWidget(self.loopALabel)
        loop_row.addWidget(self.setABtn)
        loop_row.addWidget(self.loopBLabel)
        loop_row.addWidget(self.setBBtn)
        loop_row.addWidget(self.clearLoopBtn)
        loop_row.addStretch()
        seek_col.addLayout(loop_row)

        transport.addLayout(seek_col, 1)
        root.addLayout(transport)

        # Tempo + Volume
        knobs = QHBoxLayout()
        knobs.setSpacing(20)

        tempo_col = QVBoxLayout()
        tempo_col.setSpacing(4)
        tempo_top = QHBoxLayout()
        self.tempoLabel = QLabel()
        self.tempoLabel.setObjectName("sectionLabel")
        self.tempoValue = QLabel("1.00×")
        self.tempoValue.setObjectName("tempoValue")
        self.tempoValue.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tempo_top.addWidget(self.tempoLabel)
        tempo_top.addStretch()
        tempo_top.addWidget(self.tempoValue)
        self.tempoSlider = QSlider(Qt.Horizontal)
        self.tempoSlider.setRange(self.TEMPO_MIN, self.TEMPO_MAX)
        self.tempoSlider.setValue(100)
        self.tempoSlider.valueChanged.connect(self._on_tempo_changed)
        tempo_col.addLayout(tempo_top)
        tempo_col.addWidget(self.tempoSlider)
        knobs.addLayout(tempo_col, 1)

        vol_col = QVBoxLayout()
        vol_col.setSpacing(4)
        self.volumeLabel = QLabel()
        self.volumeLabel.setObjectName("sectionLabel")
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(85)
        self.volumeSlider.valueChanged.connect(lambda v: self._audio_out.setVolume(v / 100.0))
        vol_col.addWidget(self.volumeLabel)
        vol_col.addWidget(self.volumeSlider)
        knobs.addLayout(vol_col, 1)

        root.addLayout(knobs)

    def _make_track_btn(self, key: str) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("trackBtn")
        btn.setCheckable(True)
        btn.clicked.connect(lambda checked=False, k=key: self._select_track(k))
        return btn

    # ── Player wiring ─────────────────────────────────────────────────────
    def _wire_player(self):
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)

    def _select_track(self, key: str):
        path = self._tracks.get(key)
        if not path:
            return
        resume = self._player.playbackState() == QMediaPlayer.PlayingState
        pos = self._player.position()

        self._current_key = key
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(os.path.abspath(path)))

        for k, btn in (
            ("guitar", self.btnGuitar),
            ("no_guitar", self.btnBacking),
            ("solo", self.btnSolo),
        ):
            btn.setProperty("selected", "true" if k == key else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)
            btn.setChecked(k == key)

        if pos > 0:
            self._player.setPosition(pos)
        if resume:
            self._player.play()

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            if self._player.source().isEmpty() and self._tracks:
                self._select_track(next(iter(self._tracks)))
            self._player.play()

    def _on_state_changed(self, state):
        self.playBtn.setText("⏸" if state == QMediaPlayer.PlayingState else "▶")

    def _on_duration_changed(self, ms: int):
        self.seekSlider.setRange(0, ms)
        self.timeTotalLabel.setText(_fmt_ms(ms))

    def _on_position_changed(self, ms: int):
        if not self._user_seeking:
            self.seekSlider.setValue(ms)
        self.timeCurLabel.setText(_fmt_ms(ms))

    def _on_seek_move(self, v: int):
        self.timeCurLabel.setText(_fmt_ms(v))

    def _on_seek_release(self):
        self._user_seeking = False
        self._player.setPosition(self.seekSlider.value())

    # ── Loop ──────────────────────────────────────────────────────────────
    def _set_loop_a(self):
        self._loop_a_ms = self._player.position()
        self.loopALabel.setText(f"A: {_fmt_ms(self._loop_a_ms)}")
        self._update_loop_state()

    def _set_loop_b(self):
        self._loop_b_ms = self._player.position()
        self.loopBLabel.setText(f"B: {_fmt_ms(self._loop_b_ms)}")
        self._update_loop_state()

    def _clear_loop(self):
        self._loop_a_ms = None
        self._loop_b_ms = None
        self.loopALabel.setText("A: —")
        self.loopBLabel.setText("B: —")
        self._update_loop_state()

    def _update_loop_state(self):
        if (
            self._loop_a_ms is not None
            and self._loop_b_ms is not None
            and self._loop_b_ms > self._loop_a_ms
        ):
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

    def _on_clean_toggle(self, checked: bool):
        self._prefer_clean = checked
        self._refresh_buttons()

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

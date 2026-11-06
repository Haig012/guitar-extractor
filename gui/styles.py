"""
Guitar Extractor — visual theme.
Aesthetic: tube-amp glow (warm amber) on a deep charcoal body.
"""

# Palette — exposed so widgets can use the same values for painted elements.
COLORS = {
    "bg":            "#0D0E12",   # app background (deep charcoal)
    "surface":       "#15171D",   # pane body, header
    "elevated":      "#1E2129",   # input / elevated control
    "elevated_hi":   "#272B35",   # hover elevated
    "border":        "#262A34",   # subtle 1px line
    "border_hi":     "#3A3F4E",   # hovered border
    "text":          "#ECEDF1",   # primary text
    "text_dim":      "#A0A6B4",   # secondary text
    "text_mute":     "#7C8295",   # tertiary / placeholder

    "accent":        "#FF7A1A",   # tube-amp amber — primary accent
    "accent_hi":     "#FF9A4D",   # hover / text on tinted surfaces
    "accent_lo":     "#E66500",   # pressed
    "accent_soft":   "#331C0E",   # tinted background for accent surfaces
    "on_accent":     "#1A0F06",   # text on solid amber

    "ok":            "#32D583",   # LED green
    "warn":          "#FBBF4D",
    "err":           "#F47272",
}

DARK_STYLESHEET = f"""
QWidget {{
    color: {COLORS['text']};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}
QMainWindow, QDialog, QWidget#root {{
    background-color: {COLORS['bg']};
}}
QToolTip {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border_hi']};
    padding: 6px 8px;
    font-size: 12px;
}}

/* Header */
QWidget#header {{
    background-color: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
}}
QLabel#appTitle {{ font-size: 15px; font-weight: 700; }}
QLabel#appSubtitle, QLabel#madeBy {{ font-size: 12px; color: {COLORS['text_mute']}; }}
QPushButton#langButton {{
    background-color: transparent;
    border: 1px solid {COLORS['border_hi']};
    border-radius: 13px;
    padding: 0 12px;
    min-height: 24px;
    max-height: 24px;
    font-size: 12px;
    color: {COLORS['text_dim']};
}}
QPushButton#langButton:hover {{
    border-color: {COLORS['accent']};
    color: {COLORS['accent_hi']};
}}

/* Panes */
QFrame#pane {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}
QLabel#sectionLabel {{
    font-size: 11px;
    font-weight: 600;
    color: {COLORS['text_mute']};
}}
QLabel#paneTitle {{ font-size: 15px; font-weight: 700; }}
QLabel#paneSubtitle, QLabel#idleKeys {{
    font-size: 12px;
    color: {COLORS['text_mute']};
}}
QLabel#idleStep {{ color: {COLORS['text_dim']}; }}

/* Inputs */
QLineEdit {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 0 10px;
    min-height: 30px;
    selection-background-color: {COLORS['accent']};
    selection-color: {COLORS['on_accent']};
}}
QLineEdit:hover {{ border-color: {COLORS['border_hi']}; }}
QLineEdit:focus, QLineEdit[dragActive="true"] {{ border-color: {COLORS['accent']}; }}
QLineEdit:disabled {{ color: {COLORS['text_mute']}; background-color: {COLORS['surface']}; }}
QLineEdit#timeEdit {{ min-height: 26px; padding: 0 6px; }}

/* Buttons */
QPushButton {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 0 12px;
    min-height: 30px;
    font-weight: 500;
    outline: none;
}}
QPushButton:hover {{
    background-color: {COLORS['elevated_hi']};
    border-color: {COLORS['border_hi']};
}}
QPushButton:pressed {{ background-color: {COLORS['surface']}; }}
QPushButton:disabled {{
    color: {COLORS['text_mute']};
    background-color: {COLORS['surface']};
    border-color: {COLORS['border']};
}}
QPushButton#ghost {{
    background-color: transparent;
    border-color: transparent;
    color: {COLORS['text_dim']};
    padding: 0 8px;
    min-height: 26px;
    font-size: 12px;
}}
QPushButton#ghost:hover {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text']};
}}
QPushButton#ghost:disabled {{ color: {COLORS['border_hi']}; }}
QPushButton#iconOnly {{
    background-color: transparent;
    border-color: transparent;
    padding: 0;
    min-width: 24px; max-width: 24px;
    min-height: 24px; max-height: 24px;
}}
QPushButton#iconOnly:hover {{ background-color: {COLORS['elevated_hi']}; }}

QPushButton#goButton {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {COLORS['accent_hi']}, stop:1 {COLORS['accent']});
    border: none;
    border-radius: 10px;
    color: {COLORS['on_accent']};
    font-size: 15px;
    font-weight: 700;
    min-height: 44px;
}}
QPushButton#goButton:hover {{ background-color: {COLORS['accent_hi']}; }}
QPushButton#goButton:pressed {{ background-color: {COLORS['accent_lo']}; }}
QPushButton#goButton:disabled {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_mute']};
}}
QPushButton#cancelButton {{
    background-color: transparent;
    border-color: #5A2A33;
    color: {COLORS['err']};
}}
QPushButton#cancelButton:hover {{
    background-color: #2A1820;
    border-color: {COLORS['err']};
}}
QPushButton#cancelButton:disabled {{
    border-color: {COLORS['border']};
    color: {COLORS['text_mute']};
}}

/* On/off chips: tracks, extras, player tracks */
QPushButton#chip {{
    padding: 0 6px;
    font-size: 12px;
    font-weight: 600;
    color: {COLORS['text_dim']};
}}
QPushButton#chip:hover {{ color: {COLORS['text']}; }}
QPushButton#chip:checked {{
    background-color: {COLORS['accent_soft']};
    border-color: {COLORS['accent']};
    color: {COLORS['accent_hi']};
}}
QPushButton#chip:disabled {{
    background-color: {COLORS['surface']};
    border-color: {COLORS['border']};
    color: {COLORS['text_mute']};
}}
QPushButton#chip:checked:disabled {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_dim']};
}}

/* Segmented control: one pick out of a few */
QFrame#segmented {{
    background-color: {COLORS['elevated']};
    border-radius: 8px;
}}
QPushButton#segment {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 0 7px;
    min-height: 28px;
    font-size: 11px;
    font-weight: 700;
    color: {COLORS['text_mute']};
}}
QPushButton#segment:hover {{ color: {COLORS['text']}; }}
QPushButton#segment:checked {{
    background-color: {COLORS['elevated_hi']};
    color: {COLORS['accent_hi']};
}}
QPushButton#segment:disabled {{ color: {COLORS['border_hi']}; }}

/* Inset row revealed by the Trim / Solo chips */
QFrame#inset {{
    background-color: {COLORS['bg']};
    border-radius: 8px;
}}
QScrollArea#soloScroll, QWidget#soloRows {{ background: transparent; border: none; }}

/* Readiness line above Extract */
QLabel#hint {{ font-size: 12px; color: {COLORS['text_mute']}; }}
QLabel#hint[state="ok"] {{ color: {COLORS['ok']}; }}
QLabel#hint[state="warn"] {{ color: {COLORS['warn']}; }}
QLabel#hint[state="err"] {{ color: {COLORS['err']}; }}

/* Progress page */
QLabel#pctValue {{ font-size: 40px; font-weight: 700; }}
QLabel#stepValue {{ font-size: 12px; font-weight: 700; color: {COLORS['accent_hi']}; }}
QLabel#statusValue[state="err"] {{ color: {COLORS['err']}; font-weight: 600; }}
QLabel#etaValue {{ font-size: 12px; color: {COLORS['text_mute']}; }}
QProgressBar {{
    background-color: {COLORS['elevated']};
    border: none;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 3px;
}}
QPlainTextEdit {{
    background-color: {COLORS['bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    color: {COLORS['text_dim']};
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 11px;
    padding: 6px;
    selection-background-color: {COLORS['accent']};
}}

/* Scrollbars (log, solo list) */
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{
    background-color: {COLORS['elevated_hi']};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background-color: {COLORS['border_hi']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 4px;
    background: {COLORS['elevated_hi']};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {COLORS['accent']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['text']};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::handle:horizontal:hover {{ background: {COLORS['accent_hi']}; }}

/* Player */
QPushButton#playBtn {{
    background-color: {COLORS['accent']};
    border: none;
    padding: 0;
    min-width: 44px; max-width: 44px;
    min-height: 44px; max-height: 44px;
    border-radius: 22px;
}}
QPushButton#playBtn:hover {{ background-color: {COLORS['accent_hi']}; }}
QPushButton#playBtn:pressed {{ background-color: {COLORS['accent_lo']}; }}

QLabel#chordValue {{ font-size: 34px; font-weight: 700; color: {COLORS['accent_hi']}; }}
QLabel#chordNext {{ font-size: 15px; color: {COLORS['text_mute']}; }}
QLabel#timeLabel {{
    color: {COLORS['text_dim']};
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 11px;
}}
QPushButton#tempoValue {{
    background-color: transparent;
    border: none;
    padding: 0;
    min-height: 22px;
    min-width: 42px;
    color: {COLORS['accent_hi']};
    font-weight: 700;
    font-size: 12px;
}}
"""

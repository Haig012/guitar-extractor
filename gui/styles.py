"""
Guitar Extractor — visual theme.
Aesthetic: tube-amp glow (warm amber) on a deep charcoal body.
"""

# Palette — exposed so widgets can use the same values for painted elements.
COLORS = {
    "bg":            "#0E0F13",   # app background (deep charcoal)
    "surface":       "#181A21",   # card body
    "elevated":      "#22252F",   # input / elevated control
    "elevated_hi":   "#2B2F3B",   # hover elevated
    "border":        "#2A2E3B",   # subtle 1px line
    "border_hi":     "#3A3F52",   # hovered border
    "text":          "#E8E9EE",   # primary text
    "text_dim":      "#9AA0B0",   # secondary text
    "text_mute":     "#6B7085",   # tertiary / placeholder

    "accent":        "#FF7A1A",   # tube-amp amber — primary accent
    "accent_hi":     "#FF8C3D",   # hover
    "accent_lo":     "#E66500",   # pressed
    "accent_soft":   "#3B1E0D",   # tinted background for accent surfaces

    "ok":            "#32D583",   # LED green
    "warn":          "#FBBF4D",
    "err":           "#F47272",
}

DARK_STYLESHEET = f"""
/* ─── Base ─────────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    font-size: 13px;
}}

QToolTip {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
}}

/* ─── Header ───────────────────────────────────────────────────────────── */
QWidget#headerWidget {{
    background-color: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
}}

QLabel#guitarIcon {{
    font-size: 36px;
    padding-right: 4px;
}}

QLabel#appTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS['text']};
    letter-spacing: 0.3px;
}}

QLabel#appSubtitle {{
    font-size: 11px;
    color: {COLORS['text_dim']};
    letter-spacing: 0.5px;
}}

QLabel#madeByLabel {{
    font-size: 11px;
    color: {COLORS['text_mute']};
}}

QPushButton#langButton {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
    padding: 4px 12px;
    min-height: 22px;
    font-size: 11px;
    color: {COLORS['text_dim']};
}}
QPushButton#langButton:hover {{
    border-color: {COLORS['accent']};
    color: {COLORS['accent']};
}}

/* ─── Scroll area ──────────────────────────────────────────────────────── */
QScrollArea#scrollArea, QWidget#scrollContent {{
    background-color: {COLORS['bg']};
    border: none;
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg']};
    width: 10px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {COLORS['elevated_hi']};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ─── Cards ────────────────────────────────────────────────────────────── */
QFrame#mainCard, QFrame[class="card"], QWidget[class="card"] {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
}}

QLabel#cardTitle {{
    font-size: 14px;
    font-weight: 700;
    color: {COLORS['text']};
    letter-spacing: 0.3px;
}}

QLabel#sectionLabel {{
    font-size: 11px;
    color: {COLORS['text_dim']};
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding-top: 4px;
}}

QLabel#hint {{
    font-size: 11px;
    color: {COLORS['text_mute']};
}}

QFrame#divider {{
    background-color: {COLORS['border']};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

/* ─── Inputs ───────────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {COLORS['text']};
    selection-background-color: {COLORS['accent']};
    selection-color: #ffffff;
}}
QLineEdit:hover {{
    border-color: {COLORS['border_hi']};
}}
QLineEdit:focus {{
    border-color: {COLORS['accent']};
    background-color: {COLORS['elevated_hi']};
}}
QLineEdit:disabled {{
    color: {COLORS['text_mute']};
    background-color: {COLORS['surface']};
}}
QLineEdit[readOnly="true"] {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_dim']};
}}

/* ─── Buttons ──────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 7px 14px;
    color: {COLORS['text']};
    font-weight: 500;
    min-height: 22px;
}}
QPushButton:hover {{
    background-color: {COLORS['elevated_hi']};
    border-color: {COLORS['border_hi']};
}}
QPushButton:pressed {{
    background-color: {COLORS['surface']};
}}
QPushButton:disabled {{
    color: {COLORS['text_mute']};
    background-color: {COLORS['surface']};
    border-color: {COLORS['border']};
}}

QPushButton#goButton {{
    background-color: {COLORS['accent']};
    border: 1px solid {COLORS['accent_lo']};
    color: #18120A;
    font-weight: 800;
    font-size: 15px;
    min-height: 42px;
    min-width: 220px;
    border-radius: 12px;
    letter-spacing: 0.8px;
}}
QPushButton#goButton:hover {{
    background-color: {COLORS['accent_hi']};
}}
QPushButton#goButton:pressed {{
    background-color: {COLORS['accent_lo']};
}}
QPushButton#goButton:disabled {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_mute']};
    border-color: {COLORS['border']};
}}

QPushButton#cancelButton {{
    background-color: #2A1820;
    border: 1px solid #4A2530;
    color: {COLORS['err']};
    font-weight: 600;
}}
QPushButton#cancelButton:hover {{
    background-color: #3A1F2A;
    border-color: {COLORS['err']};
}}

QPushButton#smallButton {{
    padding: 4px 10px;
    min-height: 18px;
    font-size: 11px;
    color: {COLORS['text_dim']};
}}
QPushButton#smallButton:hover {{
    color: {COLORS['text']};
}}

QPushButton#iconButton {{
    background-color: transparent;
    border: none;
    padding: 4px 6px;
    font-size: 14px;
    color: {COLORS['text_dim']};
    min-height: 0;
}}
QPushButton#iconButton:hover {{
    color: {COLORS['accent']};
}}

/* Format chip buttons (WAV / MP3 / ...) */
QPushButton#formatButton {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 14px;
    min-width: 54px;
    min-height: 22px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    color: {COLORS['text_dim']};
}}
QPushButton#formatButton:hover {{
    border-color: {COLORS['accent']};
    color: {COLORS['text']};
}}
QPushButton#formatButton[selected="true"] {{
    background-color: {COLORS['accent_soft']};
    border-color: {COLORS['accent']};
    color: {COLORS['accent_hi']};
}}

/* ─── Radio / Checkbox ─────────────────────────────────────────────────── */
QRadioButton, QCheckBox {{
    spacing: 8px;
    color: {COLORS['text']};
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 9px;
    border: 2px solid {COLORS['border_hi']};
    background-color: {COLORS['elevated']};
}}
QRadioButton::indicator:hover {{
    border-color: {COLORS['accent']};
}}
QRadioButton::indicator:checked {{
    background-color: {COLORS['accent']};
    border: 2px solid {COLORS['accent']};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid {COLORS['border_hi']};
    background-color: {COLORS['elevated']};
}}
QCheckBox::indicator:hover {{
    border-color: {COLORS['accent']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent']};
    border: 2px solid {COLORS['accent']};
    image: none;
}}

/* ─── Progress ─────────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: {COLORS['elevated']};
    border: none;
    border-radius: 4px;
    text-align: center;
    color: {COLORS['text_dim']};
    font-size: 10px;
    min-height: 8px;
    max-height: 10px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 4px;
}}

/* ─── Slider (tempo / volume / seek) ───────────────────────────────────── */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {COLORS['elevated']};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {COLORS['accent']};
    border-radius: 3px;
}}
QSlider::add-page:horizontal {{
    background: {COLORS['elevated']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {COLORS['text']};
    border: 2px solid {COLORS['accent']};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {COLORS['accent_hi']};
}}

/* ─── Log area ─────────────────────────────────────────────────────────── */
QPlainTextEdit {{
    background-color: #09090C;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    color: {COLORS['text_dim']};
    font-family: "Cascadia Mono", "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 10px;
    selection-background-color: {COLORS['accent']};
}}

/* ─── Solo segments container ──────────────────────────────────────────── */
QFrame#soloContainer {{
    background-color: {COLORS['bg']};
    border: 1px dashed {COLORS['border_hi']};
    border-radius: 10px;
}}
QLabel#soloTitle {{
    color: {COLORS['accent_hi']};
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.5px;
}}

/* ─── Status pill ──────────────────────────────────────────────────────── */
QLabel#statusLabel {{
    color: {COLORS['text_dim']};
    font-size: 12px;
}}
QLabel#etaLabel {{
    color: {COLORS['text_dim']};
    font-size: 12px;
    font-weight: 600;
}}
QLabel#stepLabel {{
    color: {COLORS['accent_hi']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

/* ─── Player card ──────────────────────────────────────────────────────── */
QPushButton#playBtn {{
    background-color: {COLORS['accent']};
    border: 1px solid {COLORS['accent_lo']};
    color: #18120A;
    font-size: 18px;
    font-weight: 800;
    min-width: 56px;
    min-height: 56px;
    max-width: 56px;
    max-height: 56px;
    border-radius: 28px;
    padding: 0;
}}
QPushButton#playBtn:hover {{
    background-color: {COLORS['accent_hi']};
}}
QPushButton#playBtn:pressed {{
    background-color: {COLORS['accent_lo']};
}}
QPushButton#playBtn:disabled {{
    background-color: {COLORS['elevated']};
    color: {COLORS['text_mute']};
    border-color: {COLORS['border']};
}}

QPushButton#trackBtn {{
    background-color: {COLORS['elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 14px;
    min-height: 30px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
    color: {COLORS['text_dim']};
}}
QPushButton#trackBtn:hover {{
    border-color: {COLORS['accent']};
    color: {COLORS['text']};
}}
QPushButton#trackBtn[selected="true"] {{
    background-color: {COLORS['accent_soft']};
    border-color: {COLORS['accent']};
    color: {COLORS['accent_hi']};
}}
QPushButton#trackBtn:disabled {{
    color: {COLORS['text_mute']};
    background-color: {COLORS['surface']};
    border-color: {COLORS['border']};
}}

QLabel#timeLabel {{
    color: {COLORS['text_dim']};
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 600;
    min-width: 48px;
}}

QLabel#tempoValue {{
    color: {COLORS['accent']};
    font-weight: 700;
    font-size: 12px;
    min-width: 46px;
}}
"""

# Back-compat name used by older imports.
LIGHT_STYLESHEET = DARK_STYLESHEET

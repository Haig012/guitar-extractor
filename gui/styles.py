"""
Light modern stylesheet for Guitar Extractor
"""

LIGHT_STYLESHEET = """
/* ─── Global ─────────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "Segoe UI Emoji", sans-serif;
    font-size: 16px;
    color: #000000;
}

QMainWindow, QDialog {
    background-color: #FFFFFF;
}

QWidget {
    background-color: transparent;
}

/* ─── Main window background ─────────────────────────────────────── */
#centralWidget {
    background-color: #FFFFFF;
}

#scrollArea {
    background-color: #FFFFFF;
    border: none;
}

#scrollContent {
    background-color: #FFFFFF;
}

/* ─── Header ─────────────────────────────────────────────────────── */
#headerWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #E0E0E0, stop:0.5 #F0F0F0, stop:1 #E0E0E0);
    border-bottom: 2px solid #CCCCCC;
    padding: 0px;
}

#appTitle {
    font-size: 35px;
    font-weight: 700;
    color: #000000;
    letter-spacing: 1px;
}

#appSubtitle {
    font-size: 16px;
    color: #666666;
    letter-spacing: 0.5px;
}

#madeByLabel {
    font-size: 13px;
    color: #999999;
    font-style: italic;
}

#guitarIcon {
    font-size: 40px;
}

/* ─── Language toggle ────────────────────────────────────────────── */
#langButton {
    background-color: transparent;
    border: 2px solid #CCCCCC;
    border-radius: 16px;
    padding: 6px 16px;
    font-size: 16px;
    min-width: 70px;
    min-height: 36px;
}
#langButton:hover {
    background-color: #F0F0F0;
    border-color: #0078D4;
}
#langButton:pressed {
    background-color: #E0E0E0;
}

/* ─── Cards ──────────────────────────────────────────────────────── */
.card {
    background-color: #F9F9F9;
    border: 3px solid #999999;
    border-radius: 16px;
    padding: 32px;
}

.card:hover {
    border-color: #0078D4;
    border-width: 3px;
}

#cardTitle {
    font-size: 20px;
    font-weight: 600;
    color: #000000;
    letter-spacing: 0.5px;
    padding-bottom: 8px;
    border-bottom: 2px solid #CCCCCC;
    margin-bottom: 14px;
}

/* ─── Section labels ─────────────────────────────────────────────── */
#sectionLabel {
    font-size: 16px;
    font-weight: 600;
    color: #0078D4;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 12px;
    margin-bottom: 8px;
}

/* ─── Input fields ───────────────────────────────────────────────── */
QLineEdit {
    background-color: #FFFFFF;
    border: 2px solid #999999;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 16px;
    color: #000000;
    min-height: 46px;
    selection-background-color: #0078D4;
}

QLineEdit:focus {
    border-color: #0078D4;
    background-color: #F0F0F0;
}

QLineEdit:hover {
    border-color: #0078D4;
}

QLineEdit[readOnly="true"] {
    color: #666666;
}

/* ─── Buttons ────────────────────────────────────────────────────── */
QPushButton {
    background-color: #F0F0F0;
    border: 2px solid #999999;
    border-radius: 8px;
    padding: 11px 18px;
    font-size: 16px;
    color: #000000;
    min-height: 44px;
}

QPushButton:hover {
    background-color: #E0E0E0;
    border-color: #0078D4;
    color: #000000;
}

QPushButton:pressed {
    background-color: #D0D0D0;
}

QPushButton:disabled {
    background-color: #F5F5F5;
    color: #999999;
    border-color: #CCCCCC;
}

/* GO button - accent */
#goButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0078D4, stop:1 #005A9E);
    border: none;
    border-radius: 10px;
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
    min-height: 56px;
    letter-spacing: 1px;
}

#goButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #106EBE, stop:1 #004578);
}

#goButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #004578, stop:1 #003A5C);
}

#goButton:disabled {
    background: #CCCCCC;
    color: #666666;
}

/* Cancel button */
#cancelButton {
    background-color: #FFE6E6;
    border: 2px solid #FF9999;
    color: #CC0000;
    border-radius: 8px;
    font-size: 15px;
    min-height: 38px;
}

#cancelButton:hover {
    background-color: #FFCCCC;
    border-color: #FF6666;
}

/* Browse button */
#browseButton {
    background-color: #E6F2FF;
    border: 2px solid #99CCFF;
    border-radius: 8px;
    padding: 9px 14px;
    min-width: 90px;
}

#browseButton:hover {
    background-color: #CCE6FF;
    border-color: #0078D4;
}

/* Small action buttons */
#smallButton {
    background-color: transparent;
    border: 2px solid #CCCCCC;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 14px;
    color: #666666;
    min-height: 30px;
}

#smallButton:hover {
    border-color: #0078D4;
    color: #000000;
}

/* ─── Radio buttons / Toggle ─────────────────────────────────────── */
QRadioButton {
    font-size: 16px;
    color: #333333;
    spacing: 10px;
    background: transparent;
    padding: 4px 0px;
}
QRadioButton:checked {
    color: #000000;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #CCCCCC;
    background-color: #FFFFFF;
}
QRadioButton::indicator:checked {
    background-color: #0078D4;
    border-color: #0078D4;
}
QRadioButton::indicator:hover {
    border-color: #0078D4;
}

/* ─── Format buttons (toggle group) ─────────────────────────────── */
#formatButton {
    background-color: #FFFFFF;
    border: 2px solid #CCCCCC;
    border-radius: 7px;
    padding: 8px 16px;
    font-size: 15px;
    font-family: "Consolas", "Courier New", monospace;
    color: #666666;
    min-width: 65px;
    min-height: 36px;
}
#formatButton:hover {
    border-color: #0078D4;
    color: #000000;
}
#formatButton[selected="true"] {
    background-color: #E6F2FF;
    border: 2px solid #0078D4;
    color: #000000;
    font-weight: 600;
}

/* ─── Progress bar ───────────────────────────────────────────────── */
QProgressBar {
    background-color: #FFFFFF;
    border: 2px solid #CCCCCC;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 13px;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0078D4, stop:1 #005A9E);
    border-radius: 6px;
}

/* ─── Log text area ──────────────────────────────────────────────── */
QPlainTextEdit {
    background-color: #F5F5F5;
    border: 2px solid #999999;
    border-radius: 8px;
    padding: 14px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 15px;
    color: #333333;
    selection-background-color: #0078D4;
}

/* ─── Recent files list ──────────────────────────────────────────── */
#recentItem {
    background-color: #FFFFFF;
    border: 2px solid #CCCCCC;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 0px;
}

#recentItem:hover {
    background-color: #F0F0F0;
    border-color: #0078D4;
    cursor: pointer;
}

#recentName {
    font-size: 15px;
    color: #000000;
    font-weight: 500;
}

#recentDate {
    font-size: 13px;
    color: #666666;
}

/* ─── Status labels ──────────────────────────────────────────────── */
#statusLabel {
    font-size: 15px;
    color: #333333;
    padding: 6px 0;
}

#etaLabel {
    font-size: 14px;
    color: #0078D4;
}

#stepLabel {
    font-size: 14px;
    color: #666666;
    font-style: italic;
}

/* ─── Scrollbars ─────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #CCCCCC;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #0078D4;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    height: 6px;
    background: transparent;
}
QScrollBar::handle:horizontal {
    background: #CCCCCC;
    border-radius: 3px;
}

/* ─── Tooltip ────────────────────────────────────────────────────── */
QToolTip {
    background-color: #FFFFE0;
    border: 2px solid #0078D4;
    color: #000000;
    padding: 5px 8px;
    border-radius: 5px;
    font-size: 12px;
}

QCheckBox {
    font-size: 16px;
    color: #222222;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QComboBox {
    background-color: #FFFFFF;
    border: 2px solid #999999;
    border-radius: 8px;
    color: #000000;
    padding: 8px 12px;
    min-height: 42px;
    font-size: 16px;
}

QComboBox:hover {
    border-color: #0078D4;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #000000;
    selection-background-color: #E6F2FF;
    selection-color: #000000;
    border: 1px solid #CCCCCC;
    font-size: 16px;
}

/* ─── Message boxes ──────────────────────────────────────────────── */
QMessageBox {
    background-color: #F9F9F9;
}
QMessageBox QPushButton {
    min-width: 80px;
}

/* ─── Splitter ───────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #CCCCCC;
    width: 1px;
}

/* ─── Divider line ───────────────────────────────────────────────── */
#divider {
    background-color: #CCCCCC;
    max-height: 1px;
    min-height: 1px;
}
"""

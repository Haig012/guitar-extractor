"""
Modern stylesheet for Guitar Extractor
"""

LIGHT_STYLESHEET = """"""

DARK_STYLESHEET = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QFrame#card {
    background-color: #1e1e1e;
    border-radius: 12px;
    padding: 16px;
}

QLabel#sectionLabel {
    color: #a0a0a0;
    font-weight: 500;
    padding-top: 4px;
    padding-bottom: 2px;
}

QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 4px 8px;
    max-height: 28px;
    selection-background-color: #4CAF50;
}

QLineEdit:hover {
    border: 1px solid #4CAF50;
}

QLineEdit:focus {
    border: 2px solid #4CAF50;
}

QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #3d3d3d;
}

QPushButton:pressed {
    background-color: #4CAF50;
    color: white;
}

QPushButton#browseButton {
    min-width: 80px;
}

QPushButton#goButton {
    background-color: #4CAF50;
    color: white;
    font-weight: 600;
    font-size: 14px;
    min-height: 36px;
    min-width: 200px;
    border-radius: 8px;
}

QPushButton#goButton:hover {
    background-color: #45a049;
}

QPushButton#goButton:pressed {
    background-color: #3d8b40;
}

QPushButton#smallButton {
    min-width: 30px;
    max-height: 26px;
    padding: 2px 8px;
}

QPushButton#formatButton {
    min-width: 60px;
}

QPushButton#formatButton[selected="true"] {
    background-color: #4CAF50;
    color: white;
    border-color: #4CAF50;
}

QRadioButton {
    spacing: 6px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #3d3d3d;
    background-color: #2d2d2d;
}

QRadioButton::indicator:checked {
    background-color: #4CAF50;
    border: 2px solid #4CAF50;
}

QCheckBox {
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #3d3d3d;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #4CAF50;
    border: 2px solid #4CAF50;
}

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 28px;
}

QComboBox:hover {
    border: 1px solid #4CAF50;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    selection-background-color: #4CAF50;
    border-radius: 6px;
}

QFrame#divider {
    background-color: #3d3d3d;
    max-height: 1px;
}
"""
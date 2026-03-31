"""
Dependency Check Dialog
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget, QPlainTextEdit
)
from PySide6.QtCore import Qt

from utils.translations import get_text, INSTALL_COMMANDS
from pipeline.dep_checker import DepCheckWorker, AutoInstallWorker, DEPENDENCIES


class DependencyDialog(QDialog):
    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang
        self._results = {}
        self._check_worker = None
        self._install_worker = None
        self._build_ui()
        self._run_check()

    def _t(self, key: str, **kw) -> str:
        return get_text(self.lang, key, **kw)

    def _build_ui(self):
        direction = Qt.RightToLeft if self.lang == "he" else Qt.LeftToRight
        self.setLayoutDirection(direction)
        self.setWindowTitle(self._t("dep_check_title"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setStyleSheet("""
            QDialog { background-color: #0F1117; color: #E8EAF0; }
            QLabel { color: #E8EAF0; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(self._t("dep_check_title"))
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF;")
        layout.addWidget(title)

        # Dep rows container
        self.depContainer = QWidget()
        self.depLayout = QVBoxLayout(self.depContainer)
        self.depLayout.setSpacing(8)
        self.depLayout.setContentsMargins(0, 0, 0, 0)

        self._dep_labels = {}
        for dep in DEPENDENCIES:
            row = QWidget()
            row.setStyleSheet("background-color: #161923; border-radius: 8px; padding: 2px;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(14, 10, 14, 10)

            name_label = QLabel(dep)
            name_label.setStyleSheet("font-weight: 600; font-size: 13px;")
            name_label.setFixedWidth(140)

            status_label = QLabel("🔄 Checking...")
            status_label.setStyleSheet("color: #6B7299; font-size: 12px;")

            cmd_label = QLabel(f"<code style='color:#4A4F6A;font-size:10px;'>{INSTALL_COMMANDS.get(dep,'')}</code>")
            cmd_label.setTextFormat(Qt.RichText)

            row_layout.addWidget(name_label)
            row_layout.addWidget(status_label, 1)
            row_layout.addWidget(cmd_label)

            self.depLayout.addWidget(row)
            self._dep_labels[dep] = (status_label, cmd_label)

        layout.addWidget(self.depContainer)

        # Log area
        self.logEdit = QPlainTextEdit()
        self.logEdit.setReadOnly(True)
        self.logEdit.setMaximumHeight(120)
        self.logEdit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #080B10;
                border: 1px solid #141720;
                border-radius: 6px;
                font-family: Consolas, monospace;
                font-size: 11px;
                color: #6B7299;
                padding: 8px;
            }
        """)
        layout.addWidget(self.logEdit)

        # Buttons
        btn_row = QHBoxLayout()
        self.autoInstallBtn = QPushButton(self._t("dep_auto_install"))
        self.autoInstallBtn.setEnabled(False)
        self.autoInstallBtn.clicked.connect(self._auto_install)
        self.autoInstallBtn.setStyleSheet("""
            QPushButton {
                background-color: #1E2550;
                border: 1px solid #5865F2;
                border-radius: 8px;
                padding: 8px 16px;
                color: #A5B4FC;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #252840; }
            QPushButton:disabled { background-color: #141720; color: #3A3D52; border-color: #1A1D2E; }
        """)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E2133;
                border: 1px solid #2A2D4A;
                border-radius: 8px;
                padding: 8px 20px;
                color: #C5C9E0;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #252840; }
        """)

        btn_row.addWidget(self.autoInstallBtn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _run_check(self):
        self._check_worker = DepCheckWorker()
        self._check_worker.result.connect(self._on_dep_result)
        self._check_worker.all_done.connect(self._on_all_done)
        self._check_worker.start()

    def _on_dep_result(self, dep: str, found: bool, version: str):
        if dep not in self._dep_labels:
            return
        status_label, cmd_label = self._dep_labels[dep]
        if found:
            status_label.setText(f"✅  Found  {version[:40] if version else ''}")
            status_label.setStyleSheet("color: #4ADE80; font-size: 12px;")
            cmd_label.setVisible(False)
        else:
            status_label.setText("❌  Not found")
            status_label.setStyleSheet("color: #FF6B6B; font-size: 12px;")
            cmd_label.setVisible(True)
        self._results[dep] = found

    def _on_all_done(self, results: list):
        missing = [name for name, found, _ in results if not found]
        if not missing:
            self.logEdit.appendPlainText(self._t("dep_all_ok"))
        else:
            for dep in missing:
                cmd = INSTALL_COMMANDS.get(dep, "")
                self.logEdit.appendPlainText(
                    self._t("dep_install_hint", cmd=cmd)
                )
            self.autoInstallBtn.setEnabled(True)
        self._missing = missing

    def _auto_install(self):
        self.autoInstallBtn.setEnabled(False)
        self.logEdit.appendPlainText("Starting auto-install...")
        self._install_worker = AutoInstallWorker(
            [d for d in self._missing if d != "ffmpeg"]
        )
        self._install_worker.log.connect(self.logEdit.appendPlainText)
        self._install_worker.finished.connect(self._run_check)
        self._install_worker.start()

"""
Mini Dropbox - Desktop Client
Run this on any device on the same network: python client_gui.py
Requires: pip install PyQt5 requests
"""

import sys
import os
import time
import threading
import requests
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QFileDialog, QMessageBox, QFrame, QHeaderView,
    QSplitter, QStatusBar, QStackedWidget, QAbstractItemView
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, pyqtProperty
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter, QBrush,
    QLinearGradient, QFontDatabase
)

# ── Theme ──────────────────────────────────────────────────────────────────────
BG_DARK    = "#0D0F14"
BG_PANEL   = "#13161E"
BG_CARD    = "#1A1E2A"
BG_HOVER   = "#222738"
ACCENT     = "#4FFFC4"
ACCENT2    = "#6B8AFF"
TEXT_PRI   = "#E8ECF5"
TEXT_SEC   = "#6B7280"
TEXT_MUT   = "#374151"
DANGER     = "#FF5F6D"
WARNING    = "#FFB347"
SUCCESS    = "#4FFFC4"
BORDER     = "#1F2535"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRI};
    font-family: 'Consolas', 'Courier New', monospace;
}}
QLineEdit {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    color: {TEXT_PRI};
    padding: 10px 14px;
    font-size: 13px;
    font-family: 'Consolas', monospace;
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QPushButton {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    color: {TEXT_PRI};
    padding: 10px 20px;
    font-size: 13px;
    font-family: 'Consolas', monospace;
}}
QPushButton:hover {{
    background: {BG_HOVER};
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton:pressed {{
    background: {BG_CARD};
}}
QPushButton#accent_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT2});
    border: none;
    color: {BG_DARK};
    font-weight: bold;
    font-size: 13px;
    padding: 12px 28px;
    border-radius: 8px;
}}
QPushButton#accent_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6BFFD4, stop:1 #8BAEFF);
    color: {BG_DARK};
}}
QPushButton#danger_btn {{
    background: transparent;
    border: 1.5px solid {DANGER};
    color: {DANGER};
}}
QPushButton#danger_btn:hover {{
    background: {DANGER};
    color: white;
}}
QTableWidget {{
    background: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
    gridline-color: {BORDER};
    color: {TEXT_PRI};
    font-size: 12px;
    selection-background-color: {BG_HOVER};
}}
QTableWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {BORDER};
}}
QTableWidget::item:selected {{
    background: {BG_HOVER};
    color: {ACCENT};
}}
QHeaderView::section {{
    background: {BG_CARD};
    color: {TEXT_SEC};
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QProgressBar {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT}, stop:1 {ACCENT2});
    border-radius: 6px;
}}
QLabel#title_label {{
    font-size: 28px;
    font-weight: bold;
    color: {ACCENT};
    letter-spacing: 2px;
}}
QLabel#subtitle_label {{
    font-size: 12px;
    color: {TEXT_SEC};
    letter-spacing: 1px;
}}
QLabel#section_label {{
    font-size: 11px;
    color: {TEXT_SEC};
    letter-spacing: 2px;
    padding: 4px 0;
}}
QFrame#card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QStatusBar {{
    background: {BG_PANEL};
    color: {TEXT_SEC};
    border-top: 1px solid {BORDER};
    font-size: 11px;
}}
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {TEXT_MUT};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

# ── Worker Threads ─────────────────────────────────────────────────────────────
class UploadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, server, token, filepath, subfolder=""):
        super().__init__()
        self.server = server
        self.token = token
        self.filepath = filepath
        self.subfolder = subfolder

    def run(self):
        try:
            file_size = os.path.getsize(self.filepath)
            filename = os.path.basename(self.filepath)

            class ProgressFile:
                def __init__(self_, f):
                    self_.f = f
                    self_.uploaded = 0

                def read(self_, size=-1):
                    chunk = self_.f.read(size)
                    self_.uploaded += len(chunk)
                    if file_size > 0:
                        pct = int((self_.uploaded / file_size) * 100)
                        self.progress.emit(pct)
                    return chunk

                def __getattr__(self_, name):
                    return getattr(self_.f, name)

            with open(self.filepath, "rb") as f:
                wrapped = ProgressFile(f)
                resp = requests.post(
                    f"{self.server}/upload",
                    headers={"X-Auth-Token": self.token},
                    files={"file": (filename, wrapped)},
                    data={"path": self.subfolder},
                    timeout=120
                )
            if resp.status_code == 200:
                self.finished.emit(True, filename)
            else:
                self.finished.emit(False, resp.json().get("error", "Upload failed"))
        except Exception as e:
            self.finished.emit(False, str(e))


class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, server, token, remote_path, save_path):
        super().__init__()
        self.server = server
        self.token = token
        self.remote_path = remote_path
        self.save_path = save_path

    def run(self):
        try:
            resp = requests.get(
                f"{self.server}/download/{self.remote_path}",
                headers={"X-Auth-Token": self.token},
                stream=True,
                timeout=120
            )
            if resp.status_code == 200:
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(self.save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                self.progress.emit(int((downloaded / total) * 100))
                self.finished.emit(True, self.save_path)
            else:
                self.finished.emit(False, "Download failed")
        except Exception as e:
            self.finished.emit(False, str(e))


class FileFetchWorker(QThread):
    result = pyqtSignal(list)
    error  = pyqtSignal(str)

    def __init__(self, server, token):
        super().__init__()
        self.server = server
        self.token = token

    def run(self):
        try:
            resp = requests.get(
                f"{self.server}/files",
                headers={"X-Auth-Token": self.token},
                timeout=10
            )
            if resp.status_code == 200:
                self.result.emit(resp.json().get("files", []))
            else:
                self.error.emit("Failed to fetch files")
        except Exception as e:
            self.error.emit(str(e))


# ── Login Screen ───────────────────────────────────────────────────────────────
class LoginWidget(QWidget):
    login_success = pyqtSignal(str, str)  # server_url, token

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Center card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(40, 44, 40, 44)

        # Logo area
        logo_label = QLabel("⬡")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"font-size: 44px; color: {ACCENT}; margin-bottom: 4px;")

        title = QLabel("DROPLINK")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("SECURE LOCAL FILE SYNC")
        subtitle.setObjectName("subtitle_label")
        subtitle.setAlignment(Qt.AlignCenter)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {BORDER}; margin: 8px 0;")

        # Server URL
        server_lbl = QLabel("SERVER ADDRESS")
        server_lbl.setObjectName("section_label")
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("http://192.168.x.x:5000")
        self.server_input.setText("http://localhost:5000")

        # Password
        pass_lbl = QLabel("PASSWORD")
        pass_lbl.setObjectName("section_label")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter server password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.returnPressed.connect(self._do_login)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {DANGER}; font-size: 12px;")
        self.error_label.setAlignment(Qt.AlignCenter)

        # Login button
        self.login_btn = QPushButton("CONNECT")
        self.login_btn.setObjectName("accent_btn")
        self.login_btn.setFixedHeight(46)
        self.login_btn.clicked.connect(self._do_login)

        card_layout.addWidget(logo_label)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(sep)
        card_layout.addSpacing(8)
        card_layout.addWidget(server_lbl)
        card_layout.addWidget(self.server_input)
        card_layout.addWidget(pass_lbl)
        card_layout.addWidget(self.pass_input)
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.login_btn)

        layout.addWidget(card, alignment=Qt.AlignCenter)

    def _do_login(self):
        server = self.server_input.text().rstrip("/")
        password = self.pass_input.text()
        if not server or not password:
            self.error_label.setText("⚠ Please fill in all fields")
            return
        self.login_btn.setText("CONNECTING...")
        self.login_btn.setEnabled(False)
        self.error_label.setText("")
        try:
            resp = requests.post(f"{server}/login",
                                 json={"password": password}, timeout=5)
            if resp.status_code == 200:
                token = resp.json()["token"]
                self.login_success.emit(server, token)
            else:
                self.error_label.setText("✗ Invalid password")
        except Exception as e:
            self.error_label.setText(f"✗ Cannot reach server")
        finally:
            self.login_btn.setText("CONNECT")
            self.login_btn.setEnabled(True)


# ── Main Dashboard ─────────────────────────────────────────────────────────────
class DashboardWidget(QWidget):
    def __init__(self, server, token):
        super().__init__()
        self.server = server
        self.token = token
        self.files = []
        self._active_workers = []
        self._build_ui()
        self._start_sync_timer()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Top bar ──
        topbar = QFrame()
        topbar.setStyleSheet(f"background: {BG_PANEL}; border-bottom: 1px solid {BORDER};")
        topbar.setFixedHeight(64)
        tbl = QHBoxLayout(topbar)
        tbl.setContentsMargins(24, 0, 24, 0)

        logo = QLabel("⬡ DROPLINK")
        logo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ACCENT}; letter-spacing: 2px;")

        self.server_tag = QLabel(f"● {self.server}")
        self.server_tag.setStyleSheet(f"font-size: 11px; color: {SUCCESS}; letter-spacing: 1px;")

        self.logout_btn = QPushButton("DISCONNECT")
        self.logout_btn.setFixedSize(120, 34)
        self.logout_btn.setObjectName("danger_btn")
        self.logout_btn.clicked.connect(self._logout)

        tbl.addWidget(logo)
        tbl.addStretch()
        tbl.addWidget(self.server_tag)
        tbl.addSpacing(20)
        tbl.addWidget(self.logout_btn)

        # ── Content ──
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setSpacing(16)
        cl.setContentsMargins(24, 24, 24, 16)

        # Action bar
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        self.upload_btn = QPushButton("↑  UPLOAD FILES")
        self.upload_btn.setObjectName("accent_btn")
        self.upload_btn.setFixedHeight(40)
        self.upload_btn.clicked.connect(self._upload_files)

        self.refresh_btn = QPushButton("⟳  REFRESH")
        self.refresh_btn.setFixedHeight(40)
        self.refresh_btn.clicked.connect(self._refresh_files)

        self.download_btn = QPushButton("↓  DOWNLOAD")
        self.download_btn.setFixedHeight(40)
        self.download_btn.clicked.connect(self._download_selected)

        self.delete_btn = QPushButton("✕  DELETE")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setFixedHeight(40)
        self.delete_btn.clicked.connect(self._delete_selected)

        action_bar.addWidget(self.upload_btn)
        action_bar.addWidget(self.refresh_btn)
        action_bar.addStretch()
        action_bar.addWidget(self.download_btn)
        action_bar.addWidget(self.delete_btn)

        # Progress bar (hidden by default)
        self.progress_label = QLabel("Preparing...")
        self.progress_label.setStyleSheet(f"font-size: 11px; color: {TEXT_SEC};")
        self.progress_label.hide()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.hide()

        # File table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["FILENAME", "SIZE", "MODIFIED"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 170)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)

        # Stats bar
        self.stats_label = QLabel("0 files")
        self.stats_label.setStyleSheet(f"font-size: 11px; color: {TEXT_SEC}; letter-spacing: 1px;")

        cl.addLayout(action_bar)
        cl.addWidget(self.progress_label)
        cl.addWidget(self.progress_bar)
        cl.addWidget(self.table)
        cl.addWidget(self.stats_label)

        root.addWidget(topbar)
        root.addWidget(content)

    def _format_size(self, size_bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _format_time(self, ts):
        import datetime
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d  %H:%M")

    def _refresh_files(self):
        self.stats_label.setText("Syncing...")
        worker = FileFetchWorker(self.server, self.token)
        worker.result.connect(self._populate_table)
        worker.error.connect(lambda e: self.stats_label.setText(f"✗ {e}"))
        worker.start()
        self._active_workers.append(worker)

    def _populate_table(self, files):
        self.files = files
        self.table.setRowCount(len(files))
        for i, f in enumerate(files):
            name_item = QTableWidgetItem(f["name"])
            name_item.setForeground(QColor(TEXT_PRI))
            size_item = QTableWidgetItem(self._format_size(f["size"]))
            size_item.setForeground(QColor(TEXT_SEC))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            mod_item = QTableWidgetItem(self._format_time(f["modified"]))
            mod_item.setForeground(QColor(TEXT_SEC))
            mod_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, size_item)
            self.table.setItem(i, 2, mod_item)
            self.table.setRowHeight(i, 42)
        total_size = sum(f["size"] for f in files)
        self.stats_label.setText(
            f"{len(files)} file{'s' if len(files) != 1 else ''}  ·  {self._format_size(total_size)} total"
        )

    def _upload_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files to Upload")
        if not paths:
            return
        for path in paths:
            self._start_upload(path)

    def _start_upload(self, filepath):
        self.progress_label.setText(f"Uploading: {os.path.basename(filepath)}")
        self.progress_label.show()
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        worker = UploadWorker(self.server, self.token, filepath)
        worker.progress.connect(self.progress_bar.setValue)
        worker.finished.connect(self._on_upload_done)
        worker.start()
        self._active_workers.append(worker)

    def _on_upload_done(self, success, msg):
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText(f"✓ Uploaded: {msg}")
            QTimer.singleShot(2000, self._hide_progress)
            self._refresh_files()
        else:
            self.progress_label.setText(f"✗ {msg}")
            self.progress_label.setStyleSheet(f"font-size: 11px; color: {DANGER};")
            QTimer.singleShot(3000, self._hide_progress)

    def _hide_progress(self):
        self.progress_bar.hide()
        self.progress_label.hide()
        self.progress_label.setStyleSheet(f"font-size: 11px; color: {TEXT_SEC};")

    def _download_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select File", "Please select a file to download.")
            return
        remote_path = self.files[row]["name"]
        filename = os.path.basename(remote_path)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File As", filename)
        if not save_path:
            return
        self.progress_label.setText(f"Downloading: {filename}")
        self.progress_label.show()
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        worker = DownloadWorker(self.server, self.token, remote_path, save_path)
        worker.progress.connect(self.progress_bar.setValue)
        worker.finished.connect(self._on_download_done)
        worker.start()
        self._active_workers.append(worker)

    def _on_download_done(self, success, msg):
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText(f"✓ Saved to: {msg}")
            QTimer.singleShot(3000, self._hide_progress)
        else:
            self.progress_label.setText(f"✗ {msg}")
            self.progress_label.setStyleSheet(f"font-size: 11px; color: {DANGER};")
            QTimer.singleShot(3000, self._hide_progress)

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select File", "Please select a file to delete.")
            return
        name = self.files[row]["name"]
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{name}' from server?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            resp = requests.delete(
                f"{self.server}/delete/{name}",
                headers={"X-Auth-Token": self.token},
                timeout=5
            )
            if resp.status_code == 200:
                self._refresh_files()
                self.stats_label.setText(f"✓ Deleted: {name}")
            else:
                self.stats_label.setText("✗ Delete failed")
        except Exception as e:
            self.stats_label.setText(f"✗ {e}")

    def _start_sync_timer(self):
        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._refresh_files)
        self._sync_timer.start(10_000)  # auto-refresh every 10s
        self._refresh_files()

    def _logout(self):
        try:
            requests.post(f"{self.server}/logout",
                          headers={"X-Auth-Token": self.token}, timeout=3)
        except:
            pass
        self._sync_timer.stop()
        # Signal parent to go back to login
        self.parent().go_to_login()


# ── Main Window ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Droplink — Local File Sync")
        self.resize(900, 620)
        self.setMinimumSize(700, 500)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_widget = LoginWidget()
        self.login_widget.login_success.connect(self._on_login)
        self.stack.addWidget(self.login_widget)

        status = self.statusBar()
        status.showMessage("  Ready — enter server address to connect")

    def _on_login(self, server, token):
        self.dashboard = DashboardWidget(server, token)
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        self.statusBar().showMessage(f"  Connected to {server}")

    def go_to_login(self):
        self.stack.setCurrentWidget(self.login_widget)
        if self.stack.count() > 1:
            old = self.stack.widget(1)
            self.stack.removeWidget(old)
            old.deleteLater()
        self.statusBar().showMessage("  Disconnected")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setApplicationName("Droplink")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
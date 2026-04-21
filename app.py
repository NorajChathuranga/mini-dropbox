"""
Droplink v2 — Unified Launcher
Run: python app.py
Choose Server or Client mode from the launcher screen.

Dependencies: pip install flask werkzeug requests PyQt5
"""

import sys, os, time, socket, threading, hashlib, secrets, mimetypes
from pathlib import Path
from functools import wraps

# ── Flask (server side) ────────────────────────────────────────────────────────
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename

# ── Qt ─────────────────────────────────────────────────────────────────────────
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QFileDialog, QMessageBox, QFrame, QHeaderView,
    QStackedWidget, QAbstractItemView, QTextEdit, QSplitter,
    QScrollArea, QSizePolicy, QSpacerItem, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QByteArray
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QPixmap, QImage, QTextCursor
)

# ══════════════════════════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg":       "#080A10",
    "panel":    "#0E111A",
    "card":     "#141822",
    "hover":    "#1C2130",
    "border":   "#1E2438",
    "accent":   "#00F5C3",
    "accent2":  "#5B7FFF",
    "purple":   "#A855F7",
    "text":     "#DDE3F0",
    "muted":    "#5A6480",
    "dim":      "#2A3050",
    "danger":   "#FF4D6A",
    "warn":     "#FFB020",
    "success":  "#00F5C3",
}

QSS = f"""
* {{ font-family: 'Consolas', 'Courier New', monospace; }}
QMainWindow, QWidget, QDialog {{ background: {C['bg']}; color: {C['text']}; }}
QFrame {{ background: transparent; }}

QLineEdit {{
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    padding: 9px 12px;
    font-size: 13px;
    selection-background-color: {C['accent2']};
}}
QLineEdit:focus {{ border-color: {C['accent']}; }}

QPushButton {{
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    padding: 9px 18px;
    font-size: 12px;
    letter-spacing: 1px;
}}
QPushButton:hover {{ background: {C['hover']}; border-color: {C['accent']}; color: {C['accent']}; }}
QPushButton:pressed {{ background: {C['card']}; }}
QPushButton:disabled {{ color: {C['dim']}; border-color: {C['dim']}; }}

QPushButton#btn_server {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #001F3F, stop:1 #003060);
    border: 1px solid {C['accent2']};
    color: {C['accent2']};
    font-size: 13px;
    padding: 20px 36px;
    border-radius: 10px;
}}
QPushButton#btn_server:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #002550, stop:1 #003A78);
    border-color: #7B9FFF;
    color: #7B9FFF;
}}

QPushButton#btn_client {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #001F2A, stop:1 #003040);
    border: 1px solid {C['accent']};
    color: {C['accent']};
    font-size: 13px;
    padding: 20px 36px;
    border-radius: 10px;
}}
QPushButton#btn_client:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #002535, stop:1 #003A50);
    border-color: #40FFD4;
    color: #40FFD4;
}}

QPushButton#btn_accent {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['accent']}, stop:1 {C['accent2']});
    border: none;
    color: {C['bg']};
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 1px;
    border-radius: 6px;
}}
QPushButton#btn_accent:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #30FFD0, stop:1 #7B9FFF);
    color: {C['bg']};
}}

QPushButton#btn_danger {{
    background: transparent;
    border: 1px solid {C['danger']};
    color: {C['danger']};
}}
QPushButton#btn_danger:hover {{ background: {C['danger']}; color: white; }}

QPushButton#btn_stop {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #7B0020, stop:1 #5B0015);
    border: 1px solid {C['danger']};
    color: {C['danger']};
    font-weight: bold;
}}
QPushButton#btn_stop:hover {{ background: {C['danger']}; color: white; }}

QTableWidget {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    gridline-color: {C['border']};
    color: {C['text']};
    font-size: 12px;
    outline: none;
}}
QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {C['border']}; }}
QTableWidget::item:selected {{ background: {C['hover']}; color: {C['accent']}; }}
QHeaderView::section {{
    background: {C['card']};
    color: {C['muted']};
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {C['border']};
    font-size: 10px;
    letter-spacing: 2px;
}}

QProgressBar {{
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['accent']}, stop:1 {C['accent2']});
    border-radius: 4px;
}}

QTextEdit {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    color: {C['text']};
    font-size: 12px;
    padding: 8px;
    selection-background-color: {C['accent2']};
}}

QScrollBar:vertical {{
    background: {C['panel']}; width: 5px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C['dim']}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: {C['panel']}; height: 5px; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {C['dim']}; border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QSplitter::handle {{ background: {C['border']}; width: 1px; height: 1px; }}

QDialog {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 10px; }}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def fmt_size(b):
    for u in ["B","KB","MB","GB"]:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def fmt_time(ts):
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d  %H:%M")

def label(text, style=""):
    l = QLabel(text)
    l.setStyleSheet(style)
    return l

def hline():
    f = QFrame(); f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"color: {C['border']};"); return f

# ══════════════════════════════════════════════════════════════════════════════
#  FLASK BACKEND (runs in a thread)
# ══════════════════════════════════════════════════════════════════════════════
SYNC_FOLDER = Path("synced")
SYNC_FOLDER.mkdir(exist_ok=True)
_flask_app = Flask(__name__)
_server_state = {
    "password": "dropbox123",
    "tokens": {},          # token -> expiry
    "log_cb": None,        # callable(msg) — GUI log callback
    "clients": {},         # ip -> last_seen timestamp
}

def _log(msg):
    ts = time.strftime("%H:%M:%S")
    full = f"[{ts}]  {msg}"
    if _server_state["log_cb"]:
        _server_state["log_cb"](full)

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

def _require(f):
    @wraps(f)
    def wrap(*a, **kw):
        tok = request.headers.get("X-Auth-Token","")
        if tok not in _server_state["tokens"]:
            abort(401)
        if time.time() > _server_state["tokens"][tok]:
            del _server_state["tokens"][tok]; abort(401)
        ip = request.remote_addr
        _server_state["clients"][ip] = time.time()
        return f(*a, **kw)
    return wrap

@_flask_app.route("/ping")
def _ping():
    return jsonify({"status":"ok","version":"2.0"})

@_flask_app.route("/login", methods=["POST"])
def _login():
    data = request.get_json() or {}
    if _hash(data.get("password","")) != _hash(_server_state["password"]):
        _log(f"❌  Failed login from {request.remote_addr}")
        return jsonify({"error":"Invalid password"}), 403
    tok = secrets.token_hex(24)
    _server_state["tokens"][tok] = time.time() + 86400
    _log(f"✅  Client connected: {request.remote_addr}")
    return jsonify({"token": tok})

@_flask_app.route("/logout", methods=["POST"])
@_require
def _logout():
    tok = request.headers.get("X-Auth-Token","")
    _server_state["tokens"].pop(tok, None)
    _log(f"👋  Client disconnected: {request.remote_addr}")
    return jsonify({"status":"ok"})

@_flask_app.route("/files")
@_require
def _files():
    out = []
    for p in SYNC_FOLDER.rglob("*"):
        if p.is_file():
            st = p.stat()
            out.append({"name": str(p.relative_to(SYNC_FOLDER)),
                        "size": st.st_size, "modified": st.st_mtime})
    return jsonify({"files": out})

@_flask_app.route("/upload", methods=["POST"])
@_require
def _upload():
    f = request.files.get("file")
    if not f: return jsonify({"error":"No file"}), 400
    sub = request.form.get("path","")
    name = secure_filename(f.filename)
    dest = (SYNC_FOLDER / sub / name) if sub else (SYNC_FOLDER / name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    f.save(str(dest))
    _log(f"↑  Uploaded: {name}  ({fmt_size(dest.stat().st_size)})  from {request.remote_addr}")
    return jsonify({"status":"ok","file":name})

@_flask_app.route("/download/<path:fp>")
@_require
def _download(fp):
    full = (SYNC_FOLDER / fp).resolve()
    try: full.relative_to(SYNC_FOLDER.resolve())
    except ValueError: abort(403)
    if not full.is_file(): abort(404)
    _log(f"↓  Downloaded: {fp}  by {request.remote_addr}")
    return send_file(str(full), as_attachment=True, download_name=full.name)

@_flask_app.route("/preview/<path:fp>")
@_require
def _preview(fp):
    """Returns file content for preview (no attachment header)."""
    full = (SYNC_FOLDER / fp).resolve()
    try: full.relative_to(SYNC_FOLDER.resolve())
    except ValueError: abort(403)
    if not full.is_file(): abort(404)
    mime, _ = mimetypes.guess_type(str(full))
    return send_file(str(full), mimetype=mime or "application/octet-stream")

@_flask_app.route("/delete/<path:fp>", methods=["DELETE"])
@_require
def _delete(fp):
    full = (SYNC_FOLDER / fp).resolve()
    try: full.relative_to(SYNC_FOLDER.resolve())
    except ValueError: abort(403)
    if not full.is_file(): abort(404)
    full.unlink()
    _log(f"🗑  Deleted: {fp}  by {request.remote_addr}")
    return jsonify({"status":"ok"})

class FlaskThread(QThread):
    def __init__(self, port=5000):
        super().__init__()
        self.port = port
    def run(self):
        import logging
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)
        _flask_app.run(host="0.0.0.0", port=self.port, debug=False, use_reloader=False)

# ══════════════════════════════════════════════════════════════════════════════
#  WORKER THREADS (client side)
# ══════════════════════════════════════════════════════════════════════════════
import requests as _req

class UploadWorker(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(bool, str)
    def __init__(self, srv, tok, path):
        super().__init__(); self.srv=srv; self.tok=tok; self.path=path
    def run(self):
        try:
            size = os.path.getsize(self.path)
            name = os.path.basename(self.path)
            uploaded = [0]
            orig = open(self.path,"rb")
            this = self
            class Wrapped:
                def read(self_, n=-1):
                    chunk = orig.read(n)
                    uploaded[0] += len(chunk)
                    if size: this.progress.emit(int(uploaded[0]/size*100))
                    return chunk
                def __getattr__(self_, k): return getattr(orig, k)
            r = _req.post(f"{self.srv}/upload",
                headers={"X-Auth-Token":self.tok},
                files={"file":(name,Wrapped())}, timeout=120)
            orig.close()
            self.done.emit(r.status_code==200, name)
        except Exception as e: self.done.emit(False, str(e))

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(bool, str)
    def __init__(self, srv, tok, rp, sp):
        super().__init__(); self.srv=srv; self.tok=tok; self.rp=rp; self.sp=sp
    def run(self):
        try:
            r = _req.get(f"{self.srv}/download/{self.rp}",
                headers={"X-Auth-Token":self.tok}, stream=True, timeout=120)
            total = int(r.headers.get("content-length",0))
            done = 0
            with open(self.sp,"wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk); done+=len(chunk)
                        if total: self.progress.emit(int(done/total*100))
            self.done.emit(r.status_code==200, self.sp)
        except Exception as e: self.done.emit(False, str(e))

class PreviewWorker(QThread):
    done = pyqtSignal(bytes, str)  # data, mime
    error = pyqtSignal(str)
    def __init__(self, srv, tok, rp):
        super().__init__(); self.srv=srv; self.tok=tok; self.rp=rp
    def run(self):
        try:
            r = _req.get(f"{self.srv}/preview/{self.rp}",
                headers={"X-Auth-Token":self.tok}, timeout=30)
            mime = r.headers.get("content-type","").split(";")[0]
            self.done.emit(r.content, mime)
        except Exception as e: self.error.emit(str(e))

class FileFetchWorker(QThread):
    result = pyqtSignal(list)
    error  = pyqtSignal(str)
    def __init__(self, srv, tok):
        super().__init__(); self.srv=srv; self.tok=tok
    def run(self):
        try:
            r = _req.get(f"{self.srv}/files",
                headers={"X-Auth-Token":self.tok}, timeout=8)
            self.result.emit(r.json().get("files",[]) if r.ok else [])
        except Exception as e: self.error.emit(str(e))

# ══════════════════════════════════════════════════════════════════════════════
#  LAUNCHER SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class LauncherWidget(QWidget):
    chose_server = pyqtSignal()
    chose_client = pyqtSignal()

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)
        root.setSpacing(0)
        root.setContentsMargins(0,0,0,0)

        wrap = QWidget(); wrap.setFixedWidth(560)
        wl = QVBoxLayout(wrap); wl.setSpacing(32); wl.setContentsMargins(40,60,40,60)

        # Header
        icon_lbl = label("◈", f"font-size:52px;color:{C['accent']};")
        icon_lbl.setAlignment(Qt.AlignCenter)
        title_lbl = label("DROPLINK", f"font-size:32px;font-weight:bold;color:{C['accent']};letter-spacing:6px;")
        title_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl = label("LOCAL FILE SYNC  ·  v2.0",
            f"font-size:11px;color:{C['muted']};letter-spacing:3px;")
        sub_lbl.setAlignment(Qt.AlignCenter)

        wl.addWidget(icon_lbl)
        wl.addWidget(title_lbl)
        wl.addWidget(sub_lbl)
        wl.addWidget(hline())

        # Mode label
        mode_lbl = label("SELECT MODE",
            f"font-size:10px;color:{C['muted']};letter-spacing:3px;")
        mode_lbl.setAlignment(Qt.AlignCenter)
        wl.addWidget(mode_lbl)

        # Mode cards
        cards = QHBoxLayout(); cards.setSpacing(20)

        # Server card
        srv_card = QFrame()
        srv_card.setStyleSheet(f"""
            QFrame {{
                background: {C['card']};
                border: 1px solid {C['accent2']};
                border-radius: 12px;
                padding: 10px;
            }}
        """)
        srv_cl = QVBoxLayout(srv_card); srv_cl.setSpacing(12); srv_cl.setContentsMargins(24,28,24,28)
        srv_cl.addWidget(label("🖥", "font-size:32px;"), alignment=Qt.AlignCenter)
        srv_cl.addWidget(label("SERVER", f"font-size:16px;font-weight:bold;color:{C['accent2']};letter-spacing:3px;"), alignment=Qt.AlignCenter)
        srv_cl.addWidget(label("Host & share files\non your machine",
            f"font-size:11px;color:{C['muted']};text-align:center;"), alignment=Qt.AlignCenter)
        srv_btn = QPushButton("START SERVER")
        srv_btn.setObjectName("btn_server")
        srv_btn.setFixedHeight(44)
        srv_btn.clicked.connect(self.chose_server)
        srv_cl.addWidget(srv_btn)

        # Client card
        cli_card = QFrame()
        cli_card.setStyleSheet(f"""
            QFrame {{
                background: {C['card']};
                border: 1px solid {C['accent']};
                border-radius: 12px;
                padding: 10px;
            }}
        """)
        cli_cl = QVBoxLayout(cli_card); cli_cl.setSpacing(12); cli_cl.setContentsMargins(24,28,24,28)
        cli_cl.addWidget(label("💻", "font-size:32px;"), alignment=Qt.AlignCenter)
        cli_cl.addWidget(label("CLIENT", f"font-size:16px;font-weight:bold;color:{C['accent']};letter-spacing:3px;"), alignment=Qt.AlignCenter)
        cli_cl.addWidget(label("Connect to a server\nand sync files",
            f"font-size:11px;color:{C['muted']};text-align:center;"), alignment=Qt.AlignCenter)
        cli_btn = QPushButton("CONNECT")
        cli_btn.setObjectName("btn_client")
        cli_btn.setFixedHeight(44)
        cli_btn.clicked.connect(self.chose_client)
        cli_cl.addWidget(cli_btn)

        cards.addWidget(srv_card)
        cards.addWidget(cli_card)
        wl.addLayout(cards)

        foot = label("Only use on trusted local networks  ·  No HTTPS",
            f"font-size:10px;color:{C['dim']};")
        foot.setAlignment(Qt.AlignCenter)
        wl.addWidget(foot)

        root.addWidget(wrap, alignment=Qt.AlignCenter)

# ══════════════════════════════════════════════════════════════════════════════
#  SERVER SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class ServerWidget(QWidget):
    go_back = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._flask_thread = None
        self._running = False
        self._workers = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0,0,0,0)

        # ── Top bar ──
        bar = QFrame(); bar.setFixedHeight(58)
        bar.setStyleSheet(f"background:{C['panel']};border-bottom:1px solid {C['border']};")
        bl = QHBoxLayout(bar); bl.setContentsMargins(20,0,20,0)
        back_btn = QPushButton("← BACK")
        back_btn.setFixedSize(90,32)
        back_btn.clicked.connect(self._confirm_back)
        bl.addWidget(back_btn)
        bl.addWidget(label("SERVER MODE",
            f"font-size:13px;font-weight:bold;color:{C['accent2']};letter-spacing:3px;"))
        bl.addStretch()
        self._status_dot = label("● OFFLINE", f"font-size:11px;color:{C['danger']};letter-spacing:1px;")
        bl.addWidget(self._status_dot)
        root.addWidget(bar)

        # ── Body ──
        body = QWidget()
        bl2 = QHBoxLayout(body); bl2.setSpacing(0); bl2.setContentsMargins(0,0,0,0)

        # LEFT PANEL — config + stats
        left = QWidget(); left.setFixedWidth(280)
        left.setStyleSheet(f"background:{C['panel']};border-right:1px solid {C['border']};")
        ll = QVBoxLayout(left); ll.setSpacing(16); ll.setContentsMargins(20,20,20,20)

        ll.addWidget(label("CONFIGURATION",
            f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))

        # Port
        ll.addWidget(label("Port", f"font-size:11px;color:{C['muted']};"))
        self._port_input = QLineEdit("5000")
        ll.addWidget(self._port_input)

        # Password
        ll.addWidget(label("Password", f"font-size:11px;color:{C['muted']};"))
        pw_row = QHBoxLayout(); pw_row.setSpacing(6)
        self._pw_input = QLineEdit("dropbox123")
        self._pw_input.setEchoMode(QLineEdit.Password)
        self._show_pw = QPushButton("👁"); self._show_pw.setFixedSize(36,36)
        self._show_pw.setCheckable(True)
        self._show_pw.toggled.connect(lambda c: self._pw_input.setEchoMode(
            QLineEdit.Normal if c else QLineEdit.Password))
        pw_row.addWidget(self._pw_input); pw_row.addWidget(self._show_pw)
        ll.addLayout(pw_row)

        # Sync folder
        ll.addWidget(label("Sync Folder", f"font-size:11px;color:{C['muted']};"))
        fol_row = QHBoxLayout(); fol_row.setSpacing(6)
        self._folder_input = QLineEdit(str(SYNC_FOLDER.resolve()))
        self._folder_input.setReadOnly(True)
        fol_btn = QPushButton("…"); fol_btn.setFixedSize(36,36)
        fol_btn.clicked.connect(self._pick_folder)
        fol_row.addWidget(self._folder_input); fol_row.addWidget(fol_btn)
        ll.addLayout(fol_row)

        ll.addWidget(hline())

        # Start/Stop
        self._start_btn = QPushButton("▶  START SERVER")
        self._start_btn.setObjectName("btn_accent")
        self._start_btn.setFixedHeight(42)
        self._start_btn.clicked.connect(self._start_server)

        self._stop_btn = QPushButton("■  STOP SERVER")
        self._stop_btn.setObjectName("btn_stop")
        self._stop_btn.setFixedHeight(42)
        self._stop_btn.clicked.connect(self._stop_server)
        self._stop_btn.hide()

        ll.addWidget(self._start_btn)
        ll.addWidget(self._stop_btn)

        ll.addWidget(hline())
        ll.addWidget(label("SERVER INFO",
            f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))

        self._info_local  = label("Local:  —", f"font-size:11px;color:{C['muted']};")
        self._info_net    = label("Network:  —", f"font-size:11px;color:{C['muted']};")
        self._info_clients = label("Clients:  0", f"font-size:11px;color:{C['muted']};")
        self._info_files  = label("Files:  0", f"font-size:11px;color:{C['muted']};")
        for w in [self._info_local,self._info_net,self._info_clients,self._info_files]:
            ll.addWidget(w)

        ll.addStretch()

        # RIGHT PANEL — logs + file list
        right = QWidget()
        rl = QVBoxLayout(right); rl.setSpacing(0); rl.setContentsMargins(0,0,0,0)

        splitter = QSplitter(Qt.Vertical)

        # Log panel
        log_panel = QWidget()
        log_panel.setStyleSheet(f"background:{C['bg']};")
        lpl = QVBoxLayout(log_panel); lpl.setSpacing(8); lpl.setContentsMargins(16,14,16,14)
        log_hdr = QHBoxLayout()
        log_hdr.addWidget(label("ACTIVITY LOG",
            f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))
        log_hdr.addStretch()
        clr_btn = QPushButton("CLEAR"); clr_btn.setFixedSize(60,24)
        clr_btn.clicked.connect(lambda: self._log_box.clear())
        log_hdr.addWidget(clr_btn)
        self._log_box = QTextEdit()
        self._log_box.setReadOnly(True)
        self._log_box.setFont(QFont("Consolas", 11))
        lpl.addLayout(log_hdr)
        lpl.addWidget(self._log_box)

        # File panel
        file_panel = QWidget()
        file_panel.setStyleSheet(f"background:{C['bg']};")
        fpl = QVBoxLayout(file_panel); fpl.setSpacing(8); fpl.setContentsMargins(16,14,16,14)
        file_hdr = QHBoxLayout()
        file_hdr.addWidget(label("SYNCED FILES",
            f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))
        file_hdr.addStretch()
        ref_btn = QPushButton("⟳"); ref_btn.setFixedSize(28,24)
        ref_btn.clicked.connect(self._refresh_server_files)
        file_hdr.addWidget(ref_btn)
        self._srv_file_table = QTableWidget()
        self._srv_file_table.setColumnCount(3)
        self._srv_file_table.setHorizontalHeaderLabels(["FILENAME","SIZE","MODIFIED"])
        self._srv_file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._srv_file_table.setColumnWidth(1,90); self._srv_file_table.setColumnWidth(2,160)
        self._srv_file_table.verticalHeader().setVisible(False)
        self._srv_file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._srv_file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        fpl.addLayout(file_hdr)
        fpl.addWidget(self._srv_file_table)

        splitter.addWidget(log_panel)
        splitter.addWidget(file_panel)
        splitter.setSizes([300,200])

        rl.addWidget(splitter)
        bl2.addWidget(left)
        bl2.addWidget(right)
        root.addWidget(body)

        # Stats refresh timer
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(3000)

    def _pick_folder(self):
        global SYNC_FOLDER
        d = QFileDialog.getExistingDirectory(self, "Select Sync Folder")
        if d:
            SYNC_FOLDER = Path(d)
            SYNC_FOLDER.mkdir(exist_ok=True)
            self._folder_input.setText(d)

    def _start_server(self):
        pw = self._pw_input.text().strip()
        if not pw: QMessageBox.warning(self,"Error","Password cannot be empty."); return
        port = int(self._port_input.text().strip() or "5000")
        _server_state["password"] = pw
        _server_state["log_cb"] = self._append_log
        self._flask_thread = FlaskThread(port)
        self._flask_thread.start()
        self._running = True
        ip = get_local_ip()
        self._info_local.setText(f"Local:  http://localhost:{port}")
        self._info_net.setText(f"Network:  http://{ip}:{port}")
        self._status_dot.setText("● ONLINE")
        self._status_dot.setStyleSheet(f"font-size:11px;color:{C['success']};letter-spacing:1px;")
        self._start_btn.hide(); self._stop_btn.show()
        self._port_input.setEnabled(False)
        self._pw_input.setEnabled(False)
        self._append_log(f"🚀  Server started on port {port}")
        self._append_log(f"📁  Sync folder: {SYNC_FOLDER.resolve()}")
        self._refresh_server_files()

    def _stop_server(self):
        # Flask dev server can't be gracefully stopped from a thread easily.
        # We hide stop and warn the user — full stop requires process restart.
        self._append_log("⚠  To fully stop the server, restart the application.")
        self._stop_btn.hide(); self._start_btn.show()
        self._running = False
        self._status_dot.setText("● STOPPING…")
        self._status_dot.setStyleSheet(f"font-size:11px;color:{C['warn']};letter-spacing:1px;")

    def _append_log(self, msg):
        self._log_box.append(
            f'<span style="color:{C["muted"]}">{msg}</span>')
        self._log_box.moveCursor(QTextCursor.End)

    def _update_stats(self):
        if not self._running: return
        active = sum(1 for t in _server_state["clients"].values()
                     if time.time()-t < 30)
        self._info_clients.setText(f"Clients:  {active} active")
        cnt = sum(1 for p in SYNC_FOLDER.rglob("*") if p.is_file())
        self._info_files.setText(f"Files:  {cnt}")

    def _refresh_server_files(self):
        files = [{"name": str(p.relative_to(SYNC_FOLDER)),
                  "size": p.stat().st_size,
                  "modified": p.stat().st_mtime}
                 for p in SYNC_FOLDER.rglob("*") if p.is_file()]
        t = self._srv_file_table
        t.setRowCount(len(files))
        for i,f in enumerate(files):
            t.setItem(i,0,QTableWidgetItem(f["name"]))
            si = QTableWidgetItem(fmt_size(f["size"]))
            si.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            t.setItem(i,1,si)
            mi = QTableWidgetItem(fmt_time(f["modified"]))
            mi.setTextAlignment(Qt.AlignCenter)
            t.setItem(i,2,mi)
            t.setRowHeight(i,36)

    def _confirm_back(self):
        if self._running:
            r = QMessageBox.question(self,"Go Back",
                "Server is running. Go back to launcher?\n(Server will keep running in background)",
                QMessageBox.Yes|QMessageBox.No)
            if r != QMessageBox.Yes: return
        self.go_back.emit()

# ══════════════════════════════════════════════════════════════════════════════
#  PREVIEW DIALOG
# ══════════════════════════════════════════════════════════════════════════════
class PreviewDialog(QDialog):
    def __init__(self, filename, data, mime, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Preview — {filename}")
        self.resize(820, 620)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16,16,16,16)
        lay.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(label(f"📄  {filename}",
            f"font-size:13px;color:{C['text']};"))
        hdr.addStretch()
        hdr.addWidget(label(f"{mime}",
            f"font-size:10px;color:{C['muted']};"))
        lay.addLayout(hdr)
        lay.addWidget(hline())

        # Content
        is_image = mime.startswith("image/")
        is_text  = mime.startswith("text/") or mime in (
            "application/json","application/xml","application/javascript")

        if is_image:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet(f"background:{C['panel']};border:1px solid {C['border']};border-radius:8px;")
            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignCenter)
            px = QPixmap()
            px.loadFromData(QByteArray(data))
            if px.width() > 780:
                px = px.scaledToWidth(780, Qt.SmoothTransformation)
            img_lbl.setPixmap(px)
            scroll.setWidget(img_lbl)
            lay.addWidget(scroll)

        elif is_text:
            txt = QTextEdit()
            txt.setReadOnly(True)
            try: content = data.decode("utf-8")
            except: content = data.decode("latin-1", errors="replace")
            txt.setPlainText(content)
            txt.setFont(QFont("Consolas", 11))
            lay.addWidget(txt)

        else:
            info = label(
                f"⚠  Preview not available for this file type.\n\n"
                f"Type: {mime}\nSize: {fmt_size(len(data))}",
                f"font-size:13px;color:{C['muted']};")
            info.setAlignment(Qt.AlignCenter)
            lay.addWidget(info)

        # Close
        close_btn = QPushButton("CLOSE")
        close_btn.setObjectName("btn_accent")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)

# ══════════════════════════════════════════════════════════════════════════════
#  CLIENT LOGIN SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class ClientLoginWidget(QWidget):
    login_ok = pyqtSignal(str, str)   # server, token
    go_back  = pyqtSignal()

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setSpacing(0); root.setContentsMargins(0,0,0,0)

        # Top bar
        bar = QFrame(); bar.setFixedHeight(58)
        bar.setStyleSheet(f"background:{C['panel']};border-bottom:1px solid {C['border']};")
        bl = QHBoxLayout(bar); bl.setContentsMargins(20,0,20,0)
        back = QPushButton("← BACK"); back.setFixedSize(90,32)
        back.clicked.connect(self.go_back)
        bl.addWidget(back)
        bl.addWidget(label("CLIENT MODE",
            f"font-size:13px;font-weight:bold;color:{C['accent']};letter-spacing:3px;"))
        bl.addStretch()
        root.addWidget(bar)

        # Center card
        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                background:{C['card']};
                border:1px solid {C['border']};
                border-radius:14px;
            }}
        """)
        cl = QVBoxLayout(card); cl.setSpacing(14); cl.setContentsMargins(36,40,36,40)

        cl.addWidget(label("◈", f"font-size:40px;color:{C['accent']};"), alignment=Qt.AlignCenter)
        cl.addWidget(label("CONNECT TO SERVER",
            f"font-size:15px;font-weight:bold;color:{C['text']};letter-spacing:2px;"),
            alignment=Qt.AlignCenter)
        cl.addWidget(hline())

        cl.addWidget(label("SERVER ADDRESS", f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))
        self._srv = QLineEdit("http://localhost:5000")
        self._srv.setPlaceholderText("http://192.168.x.x:5000")
        cl.addWidget(self._srv)

        cl.addWidget(label("PASSWORD", f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))
        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.Password)
        self._pw.setPlaceholderText("Server password")
        self._pw.returnPressed.connect(self._do_login)
        cl.addWidget(self._pw)

        self._err = label("", f"color:{C['danger']};font-size:11px;")
        self._err.setAlignment(Qt.AlignCenter)
        cl.addWidget(self._err)

        self._btn = QPushButton("CONNECT")
        self._btn.setObjectName("btn_accent")
        self._btn.setFixedHeight(44)
        self._btn.clicked.connect(self._do_login)
        cl.addWidget(self._btn)

        center.addWidget(card)
        root.addLayout(center)

    def _do_login(self):
        srv = self._srv.text().rstrip("/")
        pw  = self._pw.text()
        if not srv or not pw:
            self._err.setText("⚠  Fill in all fields"); return
        self._btn.setText("CONNECTING…"); self._btn.setEnabled(False)
        self._err.setText("")
        try:
            r = _req.post(f"{srv}/login", json={"password":pw}, timeout=5)
            if r.status_code == 200:
                self.login_ok.emit(srv, r.json()["token"])
            else:
                self._err.setText("✗  Invalid password")
        except:
            self._err.setText("✗  Cannot reach server")
        finally:
            self._btn.setText("CONNECT"); self._btn.setEnabled(True)

# ══════════════════════════════════════════════════════════════════════════════
#  CLIENT DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
class ClientDashWidget(QWidget):
    go_back = pyqtSignal()

    def __init__(self, server, token):
        super().__init__()
        self.server = server; self.token = token
        self.files = []; self._workers = []
        self._build_ui()
        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._refresh)
        self._sync_timer.start(10000)
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self); root.setSpacing(0); root.setContentsMargins(0,0,0,0)

        # Top bar
        bar = QFrame(); bar.setFixedHeight(58)
        bar.setStyleSheet(f"background:{C['panel']};border-bottom:1px solid {C['border']};")
        bl = QHBoxLayout(bar); bl.setContentsMargins(20,0,20,0)
        back = QPushButton("⏏  DISCONNECT"); back.setObjectName("btn_danger")
        back.setFixedSize(130,32); back.clicked.connect(self._disconnect)
        bl.addWidget(back)
        bl.addSpacing(12)
        bl.addWidget(label(f"● {self.server}",
            f"font-size:11px;color:{C['success']};letter-spacing:1px;"))
        bl.addStretch()
        self._sync_label = label("Syncing…", f"font-size:11px;color:{C['muted']};")
        bl.addWidget(self._sync_label)
        root.addWidget(bar)

        # Main splitter — file list LEFT, preview RIGHT
        splitter = QSplitter(Qt.Horizontal)

        # ── LEFT: file list ──
        left = QWidget()
        ll = QVBoxLayout(left); ll.setSpacing(10); ll.setContentsMargins(14,14,14,14)

        # Action row
        ar = QHBoxLayout(); ar.setSpacing(8)
        self._upload_btn = QPushButton("↑ UPLOAD")
        self._upload_btn.setObjectName("btn_accent"); self._upload_btn.setFixedHeight(36)
        self._upload_btn.clicked.connect(self._upload)
        self._dl_btn = QPushButton("↓ DOWNLOAD"); self._dl_btn.setFixedHeight(36)
        self._dl_btn.clicked.connect(self._download)
        self._prev_btn = QPushButton("◉ PREVIEW"); self._prev_btn.setFixedHeight(36)
        self._prev_btn.clicked.connect(self._preview)
        self._del_btn = QPushButton("✕ DELETE")
        self._del_btn.setObjectName("btn_danger"); self._del_btn.setFixedHeight(36)
        self._del_btn.clicked.connect(self._delete)
        ar.addWidget(self._upload_btn); ar.addWidget(self._dl_btn)
        ar.addWidget(self._prev_btn); ar.addStretch()
        ar.addWidget(self._del_btn)
        ll.addLayout(ar)

        # Progress
        self._prog_label = label("", f"font-size:11px;color:{C['muted']};")
        self._prog_label.hide()
        self._prog_bar = QProgressBar(); self._prog_bar.setFixedHeight(6)
        self._prog_bar.hide()
        ll.addWidget(self._prog_label); ll.addWidget(self._prog_bar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["FILENAME","SIZE","MODIFIED"])
        self._table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        self._table.setColumnWidth(1,90); self._table.setColumnWidth(2,160)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.doubleClicked.connect(self._preview)
        ll.addWidget(self._table)

        self._stats_label = label("0 files", f"font-size:11px;color:{C['muted']};")
        ll.addWidget(self._stats_label)

        # ── RIGHT: inline preview panel ──
        right = QWidget()
        right.setMinimumWidth(200)
        right.setStyleSheet(f"background:{C['panel']};border-left:1px solid {C['border']};")
        rl = QVBoxLayout(right); rl.setSpacing(10); rl.setContentsMargins(14,14,14,14)

        ph = QHBoxLayout()
        ph.addWidget(label("PREVIEW PANEL",
            f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))
        ph.addStretch()
        self._pop_btn = QPushButton("⤢"); self._pop_btn.setFixedSize(28,24)
        self._pop_btn.setToolTip("Open in popup")
        self._pop_btn.clicked.connect(self._popup_preview)
        ph.addWidget(self._pop_btn)
        rl.addLayout(ph)
        rl.addWidget(hline())

        self._prev_stack = QStackedWidget()

        # Placeholder
        placeholder = QWidget()
        phl = QVBoxLayout(placeholder); phl.setAlignment(Qt.AlignCenter)
        phl.addWidget(label("◈",f"font-size:36px;color:{C['dim']};"), alignment=Qt.AlignCenter)
        phl.addWidget(label("Select a file and click\nPREVIEW to inspect it",
            f"font-size:11px;color:{C['dim']};text-align:center;"), alignment=Qt.AlignCenter)

        # Image viewer
        self._img_scroll = QScrollArea()
        self._img_scroll.setWidgetResizable(True)
        self._img_scroll.setStyleSheet("background:transparent;border:none;")
        self._img_label = QLabel(); self._img_label.setAlignment(Qt.AlignCenter)
        self._img_scroll.setWidget(self._img_label)

        # Text viewer
        self._txt_view = QTextEdit()
        self._txt_view.setReadOnly(True)
        self._txt_view.setFont(QFont("Consolas",11))

        # Unsupported
        self._unsup = QLabel()
        self._unsup.setAlignment(Qt.AlignCenter)
        self._unsup.setStyleSheet(f"font-size:12px;color:{C['muted']};")

        # Loading
        self._loading = QLabel("Loading preview…")
        self._loading.setAlignment(Qt.AlignCenter)
        self._loading.setStyleSheet(f"font-size:12px;color:{C['muted']};")

        self._prev_stack.addWidget(placeholder)      # 0
        self._prev_stack.addWidget(self._img_scroll) # 1
        self._prev_stack.addWidget(self._txt_view)   # 2
        self._prev_stack.addWidget(self._unsup)      # 3
        self._prev_stack.addWidget(self._loading)    # 4

        rl.addWidget(self._prev_stack)

        # File name in preview
        self._prev_filename = label("",f"font-size:10px;color:{C['muted']};")
        rl.addWidget(self._prev_filename)

        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setSizes([580,340])
        root.addWidget(splitter)

        # Store last preview data for popup
        self._last_preview = None  # (filename, data, mime)

    # ── Actions ──
    def _refresh(self):
        self._sync_label.setText("⟳ Syncing…")
        w = FileFetchWorker(self.server, self.token)
        w.result.connect(self._populate)
        w.error.connect(lambda e: self._sync_label.setText(f"✗ {e}"))
        w.start(); self._workers.append(w)

    def _populate(self, files):
        self.files = files
        self._table.setRowCount(len(files))
        for i,f in enumerate(files):
            ni = QTableWidgetItem(f["name"]); ni.setForeground(QColor(C["text"]))
            si = QTableWidgetItem(fmt_size(f["size"]))
            si.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter); si.setForeground(QColor(C["muted"]))
            mi = QTableWidgetItem(fmt_time(f["modified"]))
            mi.setTextAlignment(Qt.AlignCenter); mi.setForeground(QColor(C["muted"]))
            self._table.setItem(i,0,ni); self._table.setItem(i,1,si); self._table.setItem(i,2,mi)
            self._table.setRowHeight(i,38)
        total = sum(f["size"] for f in files)
        self._stats_label.setText(f"{len(files)} file{'s' if len(files)!=1 else ''}  ·  {fmt_size(total)}")
        self._sync_label.setText("✓ Synced")

    def _sel_file(self):
        row = self._table.currentRow()
        return self.files[row]["name"] if row >= 0 else None

    def _upload(self):
        paths,_ = QFileDialog.getOpenFileNames(self,"Select Files to Upload")
        for p in paths: self._do_upload(p)

    def _do_upload(self, path):
        self._prog_label.setText(f"Uploading: {os.path.basename(path)}")
        self._prog_label.show(); self._prog_bar.setValue(0); self._prog_bar.show()
        w = UploadWorker(self.server, self.token, path)
        w.progress.connect(self._prog_bar.setValue)
        w.done.connect(lambda ok,m: self._upload_done(ok,m))
        w.start(); self._workers.append(w)

    def _upload_done(self, ok, msg):
        self._prog_bar.setValue(100)
        self._prog_label.setText(f"{'✓ Uploaded' if ok else '✗'}: {msg}")
        QTimer.singleShot(2500, self._hide_prog)
        if ok: self._refresh()

    def _download(self):
        name = self._sel_file()
        if not name: return
        save,_ = QFileDialog.getSaveFileName(self,"Save As", os.path.basename(name))
        if not save: return
        self._prog_label.setText(f"Downloading: {os.path.basename(name)}")
        self._prog_label.show(); self._prog_bar.setValue(0); self._prog_bar.show()
        w = DownloadWorker(self.server, self.token, name, save)
        w.progress.connect(self._prog_bar.setValue)
        w.done.connect(lambda ok,m: self._dl_done(ok,m))
        w.start(); self._workers.append(w)

    def _dl_done(self, ok, msg):
        self._prog_bar.setValue(100)
        self._prog_label.setText(f"{'✓ Saved' if ok else '✗ Failed'}: {msg}")
        QTimer.singleShot(3000, self._hide_prog)

    def _preview(self):
        name = self._sel_file()
        if not name: return
        self._prev_stack.setCurrentIndex(4)  # loading
        self._prev_filename.setText(f"Loading {os.path.basename(name)}…")
        w = PreviewWorker(self.server, self.token, name)
        w.done.connect(lambda data,mime: self._show_inline(name, data, mime))
        w.error.connect(lambda e: self._show_error(e))
        w.start(); self._workers.append(w)

    def _show_inline(self, name, data, mime):
        self._last_preview = (name, data, mime)
        fname = os.path.basename(name)
        self._prev_filename.setText(f"{fname}  ·  {fmt_size(len(data))}")
        is_img  = mime.startswith("image/")
        is_text = mime.startswith("text/") or mime in (
            "application/json","application/xml","application/javascript")
        if is_img:
            px = QPixmap(); px.loadFromData(QByteArray(data))
            avail = self._img_scroll.width() - 20
            if px.width() > avail:
                px = px.scaledToWidth(avail, Qt.SmoothTransformation)
            self._img_label.setPixmap(px)
            self._prev_stack.setCurrentIndex(1)
        elif is_text:
            try: txt = data.decode("utf-8")
            except: txt = data.decode("latin-1","replace")
            self._txt_view.setPlainText(txt)
            self._prev_stack.setCurrentIndex(2)
        else:
            self._unsup.setText(f"⚠  Cannot preview\n{mime}\nSize: {fmt_size(len(data))}")
            self._prev_stack.setCurrentIndex(3)

    def _show_error(self, msg):
        self._unsup.setText(f"✗ Preview error:\n{msg}")
        self._prev_stack.setCurrentIndex(3)

    def _popup_preview(self):
        if not self._last_preview: return
        dlg = PreviewDialog(*self._last_preview, parent=self)
        dlg.exec_()

    def _delete(self):
        name = self._sel_file()
        if not name: return
        r = QMessageBox.question(self,"Confirm",f"Delete '{name}' from server?",
            QMessageBox.Yes|QMessageBox.No)
        if r != QMessageBox.Yes: return
        try:
            resp = _req.delete(f"{self.server}/delete/{name}",
                headers={"X-Auth-Token":self.token}, timeout=5)
            if resp.ok: self._refresh()
            else: self._stats_label.setText("✗ Delete failed")
        except Exception as e:
            self._stats_label.setText(f"✗ {e}")

    def _hide_prog(self):
        self._prog_bar.hide(); self._prog_label.hide()

    def _disconnect(self):
        self._sync_timer.stop()
        try: _req.post(f"{self.server}/logout",
            headers={"X-Auth-Token":self.token}, timeout=3)
        except: pass
        self.go_back.emit()

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Droplink v2")
        self.resize(1060, 700)
        self.setMinimumSize(800, 560)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._launcher   = LauncherWidget()
        self._srv_widget = ServerWidget()
        self._cli_login  = ClientLoginWidget()
        # dashboard created on login

        self._stack.addWidget(self._launcher)    # 0
        self._stack.addWidget(self._srv_widget)  # 1
        self._stack.addWidget(self._cli_login)   # 2

        self._launcher.chose_server.connect(lambda: self._stack.setCurrentIndex(1))
        self._launcher.chose_client.connect(lambda: self._stack.setCurrentIndex(2))
        self._srv_widget.go_back.connect(lambda: self._stack.setCurrentIndex(0))
        self._cli_login.go_back.connect(lambda: self._stack.setCurrentIndex(0))
        self._cli_login.login_ok.connect(self._on_login)

        self.statusBar().setStyleSheet(
            f"background:{C['panel']};color:{C['muted']};border-top:1px solid {C['border']};")
        self.statusBar().showMessage("  Welcome to Droplink v2")

    def _on_login(self, server, token):
        dash = ClientDashWidget(server, token)
        dash.go_back.connect(self._on_client_back)
        self._stack.addWidget(dash)
        self._stack.setCurrentWidget(dash)
        self.statusBar().showMessage(f"  Connected to {server}")

    def _on_client_back(self):
        # Remove dashboard widget
        w = self._stack.currentWidget()
        self._stack.setCurrentIndex(2)
        self._stack.removeWidget(w)
        w.deleteLater()
        self.statusBar().showMessage("  Disconnected")

# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setApplicationName("Droplink")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
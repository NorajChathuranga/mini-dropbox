"""
Droplink v2 — Unified Launcher (Responsive Glassmorphism Edition)
Run: python app.py
Choose Server or Client mode from the launcher screen.
"""

import sys, os, time, socket, secrets, mimetypes, ssl, ipaddress
import re, json, hashlib, threading
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

import bcrypt
import uvicorn
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QFileDialog, QMessageBox, QFrame, QHeaderView,
    QStackedWidget, QAbstractItemView, QTextEdit, QSplitter,
    QScrollArea, QDialog, QComboBox, QSizePolicy, QShortcut, QGraphicsOpacityEffect
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QByteArray, QSettings, QEvent, QPropertyAnimation, QEasingCurve
)
from PyQt5.QtGui import (
    QFont, QColor, QPixmap, QTextCursor, QIntValidator, QKeySequence,
)

# ══════════════════════════════════════════════════════════════════════════════
#  THEME (GLASSMORPHISM)
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg_grad1": "#0B101E",
    "bg_grad2": "#1A2535",
    "panel":    "rgba(22, 32, 48, 0.7)",       
    "card":     "rgba(30, 42, 60, 0.6)",       
    "hover":    "rgba(45, 65, 90, 0.8)",
    "border":   "rgba(0, 245, 195, 0.25)",     
    "border_s": "rgba(255, 255, 255, 0.1)",    
    "accent":   "#00F5C3",
    "accent2":  "#00D4FF",
    "purple":   "#A855F7",
    "text":     "#F0F5FF",
    "muted":    "#8AA1C6",
    "dim":      "#4B5E80",
    "danger":   "#FF4D6A",
    "warn":     "#FFB020",
    "success":  "#00F5C3",
}

QSS = f"""
* {{ font-family: 'Segoe UI Variable', 'Segoe UI', 'Consolas', sans-serif; font-size: 12px; }}
QMainWindow, QDialog {{ 
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C['bg_grad1']}, stop:1 {C['bg_grad2']}); 
    color: {C['text']}; 
}}
QWidget {{ background: transparent; color: {C['text']}; }}

/* Glass Panels */
QFrame#glass_panel {{
    background: rgba(22, 32, 48, 0.76);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 18px;
}}
QFrame#glass_panel_accent {{
    background: rgba(24, 35, 52, 0.8);
    border: 1px solid rgba(0, 245, 195, 0.3);
    border-radius: 18px;
}}
QFrame#glass_panel_accent:hover {{
    border: 1px solid rgba(0, 245, 195, 0.65);
    background: rgba(30, 44, 64, 0.9);
}}

QLabel {{ color: {C['text']}; }}

QLineEdit, QComboBox {{
    background: rgba(8, 14, 24, 0.62);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    color: {C['text']};
    padding: 10px 12px;
    font-size: 13px;
}}
QLineEdit::placeholder {{ color: {C['dim']}; }}
QLineEdit:read-only {{ background: rgba(0,0,0,0.2); color: {C['muted']}; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {C['accent']}; background: rgba(15, 22, 35, 0.7); }}

QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow {{ image: none; width: 0; }}
QComboBox QAbstractItemView {{
    background: #162030;
    border: 1px solid {C['border_s']};
    border-radius: 8px;
    color: {C['text']};
    selection-background-color: {C['hover']};
    outline: none;
}}

QPushButton {{
    background: {C['card']};
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 10px;
    color: {C['text']};
    padding: 10px 16px;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 0.8px;
}}
QPushButton:hover {{ background: rgba(58, 82, 112, 0.88); border-color: {C['accent2']}; }}
QPushButton:pressed {{ background: rgba(0,0,0,0.4); }}
QPushButton:disabled {{ color: {C['dim']}; border-color: transparent; background: rgba(20,30,45,0.3); }}

QPushButton#btn_subtle {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: {C['muted']};
}}
QPushButton#btn_subtle:hover {{ background: rgba(255,255,255,0.1); color: {C['text']}; border-color: {C['border']}; }}

QPushButton#btn_icon, QPushButton#btn_field {{
    background: transparent;
    border: 1px solid transparent;
    color: {C['muted']};
    padding: 2px;
    font-size: 14px;
}}
QPushButton#btn_icon:hover, QPushButton#btn_field:hover {{ color: {C['accent']}; background: rgba(0, 245, 195, 0.1); border-radius: 8px; }}

QPushButton#btn_server {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(0, 163, 255, 0.2), stop:1 rgba(0, 163, 255, 0.05));
    border: 1px solid rgba(0, 163, 255, 0.5);
    color: #7B9FFF;
    font-size: 13px;
    padding: 16px 36px;
    border-radius: 12px;
}}
QPushButton#btn_server:hover {{ background: rgba(0, 163, 255, 0.3); border-color: #A3C2FF; color: #FFF; }}

QPushButton#btn_client {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(0, 245, 195, 0.2), stop:1 rgba(0, 245, 195, 0.05));
    border: 1px solid rgba(0, 245, 195, 0.5);
    color: {C['accent']};
    font-size: 13px;
    padding: 16px 36px;
    border-radius: 12px;
}}
QPushButton#btn_client:hover {{ background: rgba(0, 245, 195, 0.3); border-color: #66FFD9; color: #FFF; }}

QPushButton#btn_accent {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {C['accent']}, stop:1 {C['accent2']});
    border: none;
    color: #0A0F18;
    font-size: 12px;
}}
QPushButton#btn_accent:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #66FFD9, stop:1 #66CCFF); }}

QPushButton#btn_danger {{
    background: rgba(255, 77, 106, 0.1);
    border: 1px solid rgba(255, 77, 106, 0.4);
    color: #FF8CA1;
}}
QPushButton#btn_danger:hover {{ background: rgba(255, 77, 106, 0.3); color: #FFF; border-color: #FF4D6A; }}

QTableWidget {{
    background: rgba(255, 255, 255, 0.015);
    alternate-background-color: rgba(255, 255, 255, 0.02);
    border: none;
    gridline-color: transparent;
    color: {C['text']};
    font-size: 12px;
    outline: none;
}}
QTableWidget::item {{ padding: 9px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); }}
QTableWidget::item:selected {{ background: rgba(0, 245, 195, 0.15); color: #FFF; border-radius: 4px; }}
QTableWidget::item:hover {{ background: rgba(255, 255, 255, 0.05); }}

QHeaderView::section {{
    background: transparent;
    color: {C['muted']};
    padding: 9px 12px;
    border: none;
    border-bottom: 1px solid {C['border_s']};
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 2px;
}}

QProgressBar {{
    background: rgba(0,0,0,0.3);
    border: 1px solid {C['border_s']};
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {C['accent']}, stop:1 {C['accent2']});
    border-radius: 3px;
}}

QTextEdit {{
    background: rgba(0,0,0,0.2);
    border: 1px solid transparent;
    border-radius: 8px;
    color: {C['text']};
    font-size: 12px;
    padding: 8px;
    selection-background-color: rgba(0, 245, 195, 0.3);
}}

QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0px; }}
QScrollBar::handle:vertical {{ background: rgba(255,255,255,0.2); border-radius: 4px; min-height: 20px; }}
QScrollBar::handle:vertical:hover {{ background: rgba(255,255,255,0.3); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 0px; }}
QScrollBar::handle:horizontal {{ background: rgba(255,255,255,0.2); border-radius: 4px; }}
QScrollBar::handle:horizontal:hover {{ background: rgba(255,255,255,0.3); }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QSplitter::handle {{ background: transparent; width: 12px; height: 12px; }}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS & CORE BACKEND
# ══════════════════════════════════════════════════════════════════════════════
PREVIEW_SIZE_LIMIT = 50 * 1024 * 1024

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def fmt_size(b):
    for u in ["B", "KB", "MB", "GB"]:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d  %H:%M")

def label(text, style="", wrap=False):
    l = QLabel(text)
    l.setStyleSheet(style)
    if wrap: l.setWordWrap(True)
    return l

def hline():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet(f"color: {C['border_s']};")
    return f

def _hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=13))

def _verify_password(password: str, password_hash: bytes) -> bool:
    try: return bcrypt.checkpw(password.encode("utf-8"), password_hash)
    except ValueError: return False

TLS_DIR          = Path("certs")
TLS_CERT_FILE    = TLS_DIR / "droplink-cert.pem"
TLS_KEY_FILE     = TLS_DIR / "droplink-key.pem"
DISCOVERY_SERVICE_TYPE = "_droplink._tcp.local."
_trusted_server_fingerprints: dict[str, str] = {}
_state_lock = threading.RLock()

def _cert_fingerprint_sha256(cert_file: Path) -> str:
    try:
        cert = x509.load_pem_x509_certificate(cert_file.read_bytes())
        return cert.fingerprint(hashes.SHA256()).hex()
    except: return ""

def _normalize_fingerprint(fp: str) -> str:
    return "".join(ch for ch in (fp or "").lower() if ch in "0123456789abcdef")

def _authority_key(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host: raise RuntimeError("Invalid server URL")
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    return f"{host}:{port}"

def _probe_server_fingerprint(url: str, timeout: float = 5.0) -> str:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host: raise RuntimeError("Invalid server URL")
    port = parsed.port or 443
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as tls_sock:
            der = tls_sock.getpeercert(binary_form=True)
    if not der: raise RuntimeError("Server did not provide a TLS certificate")
    return hashlib.sha256(der).hexdigest()

def _ensure_self_signed_cert(cert_file: Path, key_file: Path):
    if cert_file.exists() and key_file.exists(): return
    cert_file.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Droplink Local Server"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Droplink"),
    ])
    san_entries = [x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
    local_ip = get_local_ip()
    try: san_entries.append(x509.IPAddress(ipaddress.ip_address(local_ip)))
    except ValueError: pass
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=3650))
        .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
        .sign(private_key=key, algorithm=hashes.SHA256())
    )
    key_file.write_bytes(key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    try: os.chmod(key_file, 0o600)
    except OSError: pass

def _safe_filename(name: str) -> str:
    base = Path(name or "").name
    if base.startswith(".") and len(base) > 1:
        rest = re.sub(r"[^A-Za-z0-9._-]", "_", base[1:]).strip("_")
        return f".{rest}" if rest else ""
    return re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._")

SYNC_FOLDER = Path("synced")
SYNC_FOLDER.mkdir(exist_ok=True)

_server_state = {"password_hash": _hash_password("dropbox123"), "tokens": {}, "log_cb": None, "clients": {}}
_server_ready_callback: Optional[callable] = None

@asynccontextmanager
async def _lifespan(app):
    if _server_ready_callback: _server_ready_callback()
    yield

_api_app = FastAPI(title="Droplink API", version="2.0", lifespan=_lifespan)

class LoginPayload(BaseModel): password: str = ""

def _log(msg: str):
    ts = time.strftime("%H:%M:%S")
    full = f"[{ts}]  {msg}"
    with _state_lock: log_cb = _server_state["log_cb"]
    if log_cb: log_cb(full)

def _client_ip(request: Request) -> str: return request.client.host if request.client else "unknown"

def _resolve_within_sync(path_str: str) -> Path:
    root = SYNC_FOLDER.resolve()
    full = (root / path_str).resolve()
    try: full.relative_to(root)
    except ValueError: raise HTTPException(status_code=403, detail="Forbidden path")
    return full

def _require_auth(request: Request, x_auth_token: Optional[str] = Header(default=None, alias="X-Auth-Token")) -> str:
    tok = (x_auth_token or "").strip()
    with _state_lock:
        if tok not in _server_state["tokens"]: raise HTTPException(status_code=401, detail="Unauthorized")
        if time.time() > _server_state["tokens"][tok]:
            _server_state["tokens"].pop(tok, None)
            raise HTTPException(status_code=401, detail="Session expired")
        _server_state["clients"][_client_ip(request)] = time.time()
    return tok

@_api_app.get("/ping")
async def api_ping(): return {"status": "ok", "version": "2.0"}

@_api_app.post("/login")
async def api_login(data: LoginPayload, request: Request):
    with _state_lock: password_hash = _server_state["password_hash"]
    if not _verify_password(data.password, password_hash):
        _log(f"❌  Failed login from {_client_ip(request)}")
        raise HTTPException(status_code=403, detail="Invalid password")
    tok = secrets.token_hex(24)
    with _state_lock: _server_state["tokens"][tok] = time.time() + 86400
    _log(f"✅  Client connected: {_client_ip(request)}")
    return {"token": tok}

@_api_app.post("/logout")
async def api_logout(request: Request, tok: str = Depends(_require_auth)):
    with _state_lock: _server_state["tokens"].pop(tok, None)
    _log(f"👋  Client disconnected: {_client_ip(request)}")
    return {"status": "ok"}

@_api_app.get("/files")
async def api_files(_tok: str = Depends(_require_auth)):
    out = []
    for p in SYNC_FOLDER.rglob("*"):
        if p.is_file():
            st = p.stat()
            out.append({"name": str(p.relative_to(SYNC_FOLDER)), "size": st.st_size, "modified": st.st_mtime})
    return {"files": out}

@_api_app.post("/upload")
async def api_upload(request: Request, _tok: str = Depends(_require_auth), file: UploadFile = File(...), path: str = Form(default="")):
    name = _safe_filename(file.filename or "")
    if not name: raise HTTPException(status_code=400, detail="Invalid filename")
    relative_dest = str(Path(path) / name) if path else name
    dest = _resolve_within_sync(relative_dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk: break
            out.write(chunk)
    await file.close()
    _log(f"↑  Uploaded: {name}  ({fmt_size(dest.stat().st_size)})  from {_client_ip(request)}")
    return {"status": "ok", "file": name}

@_api_app.get("/download/{fp:path}")
async def api_download(fp: str, request: Request, _tok: str = Depends(_require_auth)):
    full = _resolve_within_sync(fp)
    if not full.is_file(): raise HTTPException(status_code=404, detail="Not found")
    mime, _ = mimetypes.guess_type(str(full))
    _log(f"↓  Downloaded: {fp}  by {_client_ip(request)}")
    return FileResponse(path=str(full), media_type=mime or "application/octet-stream", filename=full.name)

@_api_app.get("/preview/{fp:path}")
async def api_preview(fp: str, _tok: str = Depends(_require_auth)):
    full = _resolve_within_sync(fp)
    if not full.is_file(): raise HTTPException(status_code=404, detail="Not found")
    mime, _ = mimetypes.guess_type(str(full))
    return FileResponse(path=str(full), media_type=mime or "application/octet-stream")

@_api_app.delete("/delete/{fp:path}")
async def api_delete(fp: str, request: Request, _tok: str = Depends(_require_auth)):
    full = _resolve_within_sync(fp)
    if not full.is_file(): raise HTTPException(status_code=404, detail="Not found")
    full.unlink()
    _log(f"🗑  Deleted: {fp}  by {_client_ip(request)}")
    return {"status": "ok"}


class UvicornThread(QThread):
    started_ok = pyqtSignal()
    failed     = pyqtSignal(str)

    def __init__(self, port: int = 5000):
        super().__init__()
        self.port, self._server = port, None
        self.cert_file, self.key_file = TLS_CERT_FILE, TLS_KEY_FILE

    def run(self):
        import logging
        logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
        logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
        global _server_ready_callback
        _server_ready_callback = self.started_ok.emit
        try:
            _ensure_self_signed_cert(self.cert_file, self.key_file)
            config = uvicorn.Config(
                _api_app, host="0.0.0.0", port=self.port, access_log=False,
                log_level="error", ssl_certfile=str(self.cert_file), ssl_keyfile=str(self.key_file),
                log_config=None,
            )
            self._server = uvicorn.Server(config)
            self._server.run()
        except Exception as e: self.failed.emit(str(e))
        finally: _server_ready_callback, self._server = None, None

    def stop(self):
        if self._server: self._server.should_exit = True


import requests as _req
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

def _api_request(method: str, url: str, *, expected_fingerprint: Optional[str] = None, allow_untrusted: bool = False, **kwargs):
    if url.lower().startswith("https://"):
        authority = _authority_key(url)
        raw_timeout = kwargs.get("timeout", 5)
        connect_timeout = (raw_timeout[0] if isinstance(raw_timeout, (tuple, list)) else float(raw_timeout or 5))
        try: observed_fp = _probe_server_fingerprint(url, connect_timeout)
        except Exception as e: raise RuntimeError(f"TLS handshake failed: {e}")

        provided_fp = _normalize_fingerprint(expected_fingerprint or "")
        pinned_fp   = _normalize_fingerprint(_trusted_server_fingerprints.get(authority, ""))
        required_fp = provided_fp or pinned_fp

        if required_fp:
            if observed_fp != required_fp: raise RuntimeError("Server certificate fingerprint mismatch.")
            _trusted_server_fingerprints[authority] = required_fp
        else:
            if not allow_untrusted: raise RuntimeError("Untrusted server certificate. Connect once to pin.")
            _trusted_server_fingerprints[authority] = observed_fp
        kwargs.setdefault("verify", False)
    return _req.request(method, url, **kwargs)


class ZeroconfAdvertiser:
    def __init__(self, *, local_ip: str, port: int, fingerprint: str):
        self.local_ip, self.port, self.fingerprint = local_ip, port, fingerprint
        self._zeroconf, self._info = None, None

    def start(self):
        host = socket.gethostname() or "droplink"
        name = f"Droplink-{host}-{self.port}.{DISCOVERY_SERVICE_TYPE}"
        props = {"name": host, "proto": "https", "ver": "2", "fp": self.fingerprint}
        encoded = {k.encode(): v.encode() for k, v in props.items()}
        self._info = ServiceInfo(
            type_=DISCOVERY_SERVICE_TYPE, name=name, addresses=[socket.inet_aton(self.local_ip)],
            port=self.port, properties=encoded, server=f"{host}.local."
        )
        self._zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self._zeroconf.register_service(self._info)

    def stop(self):
        try:
            if self._zeroconf and self._info: self._zeroconf.unregister_service(self._info)
        except: pass
        try:
            if self._zeroconf: self._zeroconf.close()
        except: pass
        self._info = self._zeroconf = None


class _DiscoveryListener(ServiceListener):
    def __init__(self, owner): self.owner = owner
    def add_service(self, zc, type_, name): self.owner._emit_service(name)
    def update_service(self, zc, type_, name): self.owner._emit_service(name)
    def remove_service(self, zc, type_, name): self.owner.service_remove.emit(name)


class DiscoveryBrowserThread(QThread):
    service_upsert = pyqtSignal(object)
    service_remove = pyqtSignal(str)
    status         = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running, self._zeroconf, self._browser = True, None, None

    def run(self):
        self._running = True
        try:
            self._zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
            listener = _DiscoveryListener(self)
            self._browser = ServiceBrowser(self._zeroconf, DISCOVERY_SERVICE_TYPE, listener)
            self.status.emit("Scanning LAN for Droplink servers…")
            while self._running: self.msleep(200)
        except Exception as e: self.status.emit(f"Discovery unavailable: {e}")
        finally:
            try:
                if self._browser: self._browser.cancel()
            except: pass
            try:
                if self._zeroconf: self._zeroconf.close()
            except: pass
            self._browser = self._zeroconf = None

    def stop(self): self._running = False

    def _emit_service(self, service_name: str):
        if not self._zeroconf: return
        info = self._zeroconf.get_service_info(DISCOVERY_SERVICE_TYPE, service_name, timeout=2000)
        if not info or not info.addresses: return
        ip = socket.inet_ntoa(info.addresses[0])
        props = {}
        for k, v in (info.properties or {}).items():
            key = k.decode("utf-8", errors="ignore") if isinstance(k, bytes) else str(k)
            val = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)
            props[key] = val
        proto = props.get("proto", "https")
        url = f"{proto}://{ip}:{info.port}"
        display = f"{props.get('name', 'Droplink')} ({ip}:{info.port})"
        self.service_upsert.emit({"id": service_name, "display": display, "url": url, "fingerprint": props.get("fp", "")})


class UploadWorker(QThread):
    progress = pyqtSignal(int)
    done     = pyqtSignal(bool, str)

    def __init__(self, srv: str, tok: str, path: str):
        super().__init__()
        self.srv, self.tok, self.path = srv, tok, path

    def run(self):
        try:
            size, name, uploaded, this = os.path.getsize(self.path), os.path.basename(self.path), [0], self
            with open(self.path, "rb") as orig:
                class _Wrapped:
                    def read(self_, n=-1):
                        chunk = orig.read(n)
                        uploaded[0] += len(chunk)
                        if size: this.progress.emit(int(uploaded[0] / size * 100))
                        return chunk
                    def __getattr__(self_, k): return getattr(orig, k)
                r = _api_request("POST", f"{self.srv}/upload", headers={"X-Auth-Token": self.tok}, files={"file": (name, _Wrapped())}, timeout=120)
            if r.ok: self.done.emit(True, name)
            else: self.done.emit(False, f"{name} (HTTP {r.status_code})")
        except Exception as e: self.done.emit(False, str(e))

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    done     = pyqtSignal(bool, str)

    def __init__(self, srv: str, tok: str, rp: str, sp: str):
        super().__init__()
        self.srv, self.tok, self.rp, self.sp = srv, tok, rp, sp

    def run(self):
        try:
            r = _api_request("GET", f"{self.srv}/download/{self.rp}", headers={"X-Auth-Token": self.tok}, stream=True, timeout=120)
            if not r.ok:
                self.done.emit(False, f"HTTP {r.status_code}")
                return
            total, done = int(r.headers.get("content-length", 0)), 0
            with open(self.sp, "wb") as f:
                for chunk in r.iter_content(65536):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if total: self.progress.emit(int(done / total * 100))
            self.done.emit(True, self.sp)
        except Exception as e: self.done.emit(False, str(e))

class PreviewWorker(QThread):
    done  = pyqtSignal(bytes, str)
    error = pyqtSignal(str)

    def __init__(self, srv: str, tok: str, rp: str):
        super().__init__()
        self.srv, self.tok, self.rp = srv, tok, rp

    def run(self):
        try:
            r = _api_request("GET", f"{self.srv}/preview/{self.rp}", headers={"X-Auth-Token": self.tok}, stream=True, timeout=30)
            if not r.ok:
                self.error.emit(f"HTTP {r.status_code}")
                return
            content_length = int(r.headers.get("content-length", 0))
            if content_length > PREVIEW_SIZE_LIMIT:
                self.error.emit(f"File too large to preview ({fmt_size(content_length)}). Limit is {fmt_size(PREVIEW_SIZE_LIMIT)}.")
                return
            chunks, received = [], 0
            for chunk in r.iter_content(65536):
                if chunk:
                    received += len(chunk)
                    if received > PREVIEW_SIZE_LIMIT:
                        self.error.emit(f"File exceeded preview limit.")
                        return
                    chunks.append(chunk)
            mime = r.headers.get("content-type", "").split(";")[0].strip()
            self.done.emit(b"".join(chunks), mime)
        except Exception as e: self.error.emit(str(e))

class FileFetchWorker(QThread):
    result = pyqtSignal(list)
    error  = pyqtSignal(str)

    def __init__(self, srv: str, tok: str):
        super().__init__()
        self.srv, self.tok = srv, tok

    def run(self):
        try:
            r = _api_request("GET", f"{self.srv}/files", headers={"X-Auth-Token": self.tok}, timeout=8)
            if not r.ok:
                self.error.emit(f"HTTP {r.status_code}")
                return
            self.result.emit(r.json().get("files", []))
        except Exception as e: self.error.emit(str(e))

class LoginWorker(QThread):
    success = pyqtSignal(str, str, str)
    failure = pyqtSignal(str)

    def __init__(self, srv: str, pw: str, pin_fp: str, allow_untrusted: bool):
        super().__init__()
        self.srv, self.pw, self.pin_fp, self.allow_untrusted = srv, pw, pin_fp, allow_untrusted

    def run(self):
        try:
            r = _api_request("POST", f"{self.srv}/login", json={"password": self.pw}, timeout=5, expected_fingerprint=self.pin_fp or None, allow_untrusted=self.allow_untrusted)
            if r.status_code == 200:
                authority = _authority_key(self.srv)
                learned_fp = _normalize_fingerprint(_trusted_server_fingerprints.get(authority, ""))
                self.success.emit(self.srv, r.json()["token"], learned_fp)
            elif r.status_code == 403: self.failure.emit("✗  Invalid password")
            else: self.failure.emit(f"✗  Login failed (HTTP {r.status_code})")
        except RuntimeError as e: self.failure.emit(f"✗  {e}")
        except Exception as e: self.failure.emit(f"✗  Cannot reach server ({e})")


# ══════════════════════════════════════════════════════════════════════════════
#  GUI WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class LauncherWidget(QWidget):
    chose_server = pyqtSignal()
    chose_client = pyqtSignal()

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)

        wrap = QWidget()
        wrap.setMaximumWidth(750)
        wrap.setMinimumSize(400, 450) # Added explicit minimum size
        wl = QVBoxLayout(wrap)
        wl.setSpacing(40)
        wl.setContentsMargins(0, 40, 0, 40)

        icon_lbl = label("◈", f"font-size:58px;color:{C['accent']};")
        icon_lbl.setAlignment(Qt.AlignCenter)
        title_lbl = label("DROPLINK", f"font-size:36px;font-weight:bold;color:{C['accent']};letter-spacing:8px;")
        title_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl = label("LOCAL FILE SYNC  ·  v2.1", f"font-size:12px;color:{C['muted']};letter-spacing:4px;")
        sub_lbl.setAlignment(Qt.AlignCenter)

        for w in [icon_lbl, title_lbl, sub_lbl]: wl.addWidget(w)

        mode_lbl = label("SELECT MODE", f"font-size:11px;color:{C['muted']};letter-spacing:3px;")
        mode_lbl.setAlignment(Qt.AlignCenter)
        wl.addWidget(mode_lbl)

        cards = QHBoxLayout()
        cards.setSpacing(24)

        srv_card = QFrame()
        srv_card.setObjectName("glass_panel_accent")
        scl = QVBoxLayout(srv_card)
        scl.setSpacing(16)
        scl.setContentsMargins(30, 40, 30, 40)
        scl.addWidget(label("🖥", "font-size:48px;"), alignment=Qt.AlignCenter)
        scl.addWidget(label("NETWORK HOST", f"font-size:16px;font-weight:bold;color:#FFF;letter-spacing:1px;"), alignment=Qt.AlignCenter)
        desc1 = label("Host secure file folders from this machine. Manage access and local sync sessions.", f"font-size:12px;color:{C['muted']};text-align:center;line-height:1.4;", wrap=True)
        desc1.setAlignment(Qt.AlignCenter)
        scl.addWidget(desc1)
        scl.addStretch()
        srv_btn = QPushButton("START LOCAL HOST")
        srv_btn.setObjectName("btn_server")
        srv_btn.clicked.connect(self.chose_server)
        scl.addWidget(srv_btn)

        cli_card = QFrame()
        cli_card.setObjectName("glass_panel_accent")
        ccl = QVBoxLayout(cli_card)
        ccl.setSpacing(16)
        ccl.setContentsMargins(30, 40, 30, 40)
        ccl.addWidget(label("💻", "font-size:48px;"), alignment=Qt.AlignCenter)
        ccl.addWidget(label("FILE CLIENT", f"font-size:16px;font-weight:bold;color:#FFF;letter-spacing:1px;"), alignment=Qt.AlignCenter)
        desc2 = label("Connect to an active network host to access and synchronize shared files.", f"font-size:12px;color:{C['muted']};text-align:center;line-height:1.4;", wrap=True)
        desc2.setAlignment(Qt.AlignCenter)
        ccl.addWidget(desc2)
        ccl.addStretch()
        cli_btn = QPushButton("CONNECT TO HOST")
        cli_btn.setObjectName("btn_client")
        cli_btn.clicked.connect(self.chose_client)
        ccl.addWidget(cli_btn)

        cards.addWidget(srv_card)
        cards.addWidget(cli_card)
        wl.addLayout(cards)

        foot = label("Self-signed HTTPS enabled  |  Local network only", f"font-size:11px;color:{C['accent']};")
        foot.setAlignment(Qt.AlignCenter)
        wl.addWidget(foot)
        root.addWidget(wrap, alignment=Qt.AlignCenter)


class ServerWidget(QWidget):
    server_log = pyqtSignal(str)
    go_back    = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._server_thread = None
        self._discovery_advertiser = None
        self._running = False
        self.server_log.connect(self._append_log)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(18)
        root.setContentsMargins(22, 22, 22, 22)

        # Top bar
        bar = QWidget()
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Forces bar to stick to top
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(0, 0, 0, 0)
        back_btn = QPushButton("← BACK")
        back_btn.setObjectName("btn_subtle")
        back_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        back_btn.setMinimumSize(90, 34)
        back_btn.clicked.connect(self._confirm_back)
        bl.addWidget(back_btn)
        bl.addSpacing(16)
        bl.addWidget(label("SERVER MODE", f"font-size:14px;font-weight:bold;color:{C['accent2']};letter-spacing:3px;"))
        bl.addStretch()
        self._status_dot = label("● OFFLINE", f"font-size:12px;color:{C['danger']};letter-spacing:1px;font-weight:bold;")
        bl.addWidget(self._status_dot)
        root.addWidget(bar)

        # Main Layout
        body = QWidget()
        bl2 = QHBoxLayout(body)
        bl2.setSpacing(16)
        bl2.setContentsMargins(0, 0, 0, 0)

        # LEFT panel
        left = QFrame()
        left.setObjectName("glass_panel")
        left.setMinimumWidth(260)
        left.setMaximumWidth(350)
        ll = QVBoxLayout(left)
        ll.setSpacing(18)
        ll.setContentsMargins(24, 24, 24, 24)

        ll.addWidget(label("CONFIGURATION", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))

        ll.addWidget(label("Port", f"font-size:12px;color:{C['muted']};"))
        self._port_input = QLineEdit("5000")
        self._port_input.setValidator(QIntValidator(1, 65535, self))
        ll.addWidget(self._port_input)

        ll.addWidget(label("Password", f"font-size:12px;color:{C['muted']};"))
        pw_row = QHBoxLayout()
        pw_row.setSpacing(8)
        self._pw_input = QLineEdit("dropbox123")
        self._pw_input.setEchoMode(QLineEdit.Password)
        self._show_pw = QPushButton("👁")
        self._show_pw.setFixedSize(38, 38)
        self._show_pw.setObjectName("btn_field")
        self._show_pw.setCheckable(True)
        self._show_pw.toggled.connect(lambda c: self._pw_input.setEchoMode(QLineEdit.Normal if c else QLineEdit.Password))
        pw_row.addWidget(self._pw_input)
        pw_row.addWidget(self._show_pw)
        ll.addLayout(pw_row)

        ll.addWidget(label("Sync Folder", f"font-size:12px;color:{C['muted']};"))
        fol_row = QHBoxLayout()
        fol_row.setSpacing(8)
        self._folder_input = QLineEdit(str(SYNC_FOLDER.resolve()))
        self._folder_input.setReadOnly(True)
        self._folder_btn = QPushButton("📁")
        self._folder_btn.setFixedSize(38, 38)
        self._folder_btn.setObjectName("btn_field")
        self._folder_btn.clicked.connect(self._pick_folder)
        fol_row.addWidget(self._folder_input)
        fol_row.addWidget(self._folder_btn)
        ll.addLayout(fol_row)

        ll.addSpacing(10)
        self._start_btn = QPushButton("▶  START SERVER")
        self._start_btn.setObjectName("btn_accent")
        self._start_btn.setMinimumHeight(44)
        self._start_btn.clicked.connect(self._start_server)

        self._stop_btn = QPushButton("■  STOP SERVER")
        self._stop_btn.setObjectName("btn_stop")
        self._stop_btn.setMinimumHeight(44)
        self._stop_btn.clicked.connect(self._stop_server)
        self._stop_btn.hide()

        ll.addWidget(self._start_btn)
        ll.addWidget(self._stop_btn)

        ll.addSpacing(10)
        ll.addWidget(label("SERVER INFO", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))

        self._info_local   = label("Local:    —", f"font-size:12px;color:{C['text']};")
        self._info_net     = label("Network:  —", f"font-size:12px;color:{C['text']};")
        self._info_clients = label("Clients:  0", f"font-size:12px;color:{C['muted']};")
        self._info_files   = label("Files:    0", f"font-size:12px;color:{C['muted']};")
        for w in [self._info_local, self._info_net, self._info_clients, self._info_files]:
            w.setWordWrap(True)
            ll.addWidget(w)
        ll.addStretch()

        # RIGHT panel
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setSpacing(16)
        rl.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Vertical)

        log_panel = QFrame()
        log_panel.setObjectName("glass_panel")
        lpl = QVBoxLayout(log_panel)
        lpl.setSpacing(12)
        lpl.setContentsMargins(20, 20, 20, 20)
        log_hdr = QHBoxLayout()
        log_hdr.addWidget(label("ACTIVITY LOG", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))
        log_hdr.addStretch()
        clr_btn = QPushButton("···")
        clr_btn.setFixedSize(40, 26)
        clr_btn.setObjectName("btn_subtle")
        clr_btn.clicked.connect(lambda: self._log_box.clear())
        log_hdr.addWidget(clr_btn)
        self._log_box = QTextEdit()
        self._log_box.setReadOnly(True)
        self._log_box.setFont(QFont("Consolas", 12))
        lpl.addLayout(log_hdr)
        lpl.addWidget(self._log_box)

        file_panel = QFrame()
        file_panel.setObjectName("glass_panel")
        fpl = QVBoxLayout(file_panel)
        fpl.setSpacing(12)
        fpl.setContentsMargins(20, 20, 20, 20)
        file_hdr = QHBoxLayout()
        file_hdr.addWidget(label("SYNCED FILES", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))
        file_hdr.addStretch()
        ref_btn = QPushButton("⟳")
        ref_btn.setFixedSize(30, 30)
        ref_btn.setObjectName("btn_icon")
        ref_btn.clicked.connect(self._refresh_server_files)
        file_hdr.addWidget(ref_btn)
        self._srv_file_table = QTableWidget()
        self._srv_file_table.setColumnCount(3)
        self._srv_file_table.setHorizontalHeaderLabels(["FILENAME", "SIZE", "MODIFIED"])
        self._srv_file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._srv_file_table.setColumnWidth(1, 100)
        self._srv_file_table.setColumnWidth(2, 160)
        self._srv_file_table.verticalHeader().setVisible(False)
        self._srv_file_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._srv_file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        fpl.addLayout(file_hdr)
        fpl.addWidget(self._srv_file_table)

        splitter.addWidget(log_panel)
        splitter.addWidget(file_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        rl.addWidget(splitter)
        bl2.addWidget(left)
        bl2.addWidget(right, 1)
        root.addWidget(body)

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

    def _set_status(self, text: str, color: str):
        self._status_dot.setText(text)
        self._status_dot.setStyleSheet(f"font-size:12px;color:{color};letter-spacing:1px;font-weight:bold;")

    def _set_server_controls(self, enabled: bool):
        self._port_input.setEnabled(enabled)
        self._pw_input.setEnabled(enabled)
        self._show_pw.setEnabled(enabled)
        self._folder_btn.setEnabled(enabled)

    def _start_server(self):
        if self._running: return
        pw = self._pw_input.text().strip()
        if not pw or len(pw) < 10:
            QMessageBox.warning(self, "Error", "Use a stronger password (at least 10 characters).")
            return
        try:
            port = int(self._port_input.text().strip())
            if not 1 <= port <= 65535: raise ValueError
        except:
            QMessageBox.warning(self, "Error", "Enter a valid port (1–65535).")
            return

        with _state_lock:
            _server_state["password_hash"] = _hash_password(pw)
            _server_state["tokens"].clear()
            _server_state["clients"].clear()
            _server_state["log_cb"] = self.server_log.emit

        self._server_thread = UvicornThread(port)
        self._server_thread.started_ok.connect(lambda p=port: self._on_server_started(p))
        self._server_thread.failed.connect(self._on_server_failed)
        self._server_thread.finished.connect(self._on_server_stopped)

        self._set_server_controls(False)
        self._start_btn.setEnabled(False)
        self._set_status("● STARTING…", C["warn"])
        self._append_log(f"⏳  Starting server on port {port}…")
        self._server_thread.start()

    def _on_server_started(self, port: int):
        self._running = True
        ip = get_local_ip()
        self._info_local.setText(f"Local:    https://localhost:{port}")
        self._info_net.setText(f"Network:  https://{ip}:{port}")
        self._set_status("● ONLINE", C["success"])
        self._start_btn.hide()
        self._stop_btn.setEnabled(True)
        self._stop_btn.show()
        try:
            self._discovery_advertiser = ZeroconfAdvertiser(local_ip=ip, port=port, fingerprint=_cert_fingerprint_sha256(TLS_CERT_FILE))
            self._discovery_advertiser.start()
            self._append_log("📡  mDNS discovery active (_droplink._tcp.local)")
        except Exception as e:
            self._append_log(f"⚠  mDNS unavailable: {e}")
        self._append_log(f"🚀  Server ready on port {port}")
        self._append_log(f"🔒  HTTPS (self-signed): {TLS_CERT_FILE.resolve()}")
        self._append_log(f"📁  Sync folder: {SYNC_FOLDER.resolve()}")
        self._refresh_server_files()

    def _on_server_failed(self, err: str):
        self._append_log(f"✗  Server failed: {err}")
        self._set_server_controls(True)
        self._start_btn.setEnabled(True)
        self._set_status("● OFFLINE", C["danger"])

    def _on_server_stopped(self):
        self._running = False
        if self._discovery_advertiser:
            self._discovery_advertiser.stop()
            self._discovery_advertiser = None
        with _state_lock: _server_state["log_cb"] = None
        self._set_status("● OFFLINE", C["danger"])
        self._set_server_controls(True)
        self._start_btn.setEnabled(True)
        self._start_btn.show()
        self._stop_btn.hide()
        self._info_clients.setText("Clients:  0")
        self._server_thread = None

    def _stop_server(self):
        if not self._server_thread: return self._on_server_stopped()
        self._stop_btn.setEnabled(False)
        self._set_status("● STOPPING…", C["warn"])
        self._append_log("⏹  Stopping server…")
        self._server_thread.stop()

    def _append_log(self, msg: str):
        self._log_box.append(f'<span style="color:{C["muted"]}">{msg}</span>')
        self._log_box.moveCursor(QTextCursor.End)

    def _update_stats(self):
        if not self._running: return
        with _state_lock: client_times = list(_server_state["clients"].values())
        active = sum(1 for t in client_times if time.time() - t < 30)
        self._info_clients.setText(f"Clients:  {active} active")
        cnt = sum(1 for p in SYNC_FOLDER.rglob("*") if p.is_file())
        self._info_files.setText(f"Files:    {cnt}")

    def _refresh_server_files(self):
        files = sorted([{"name": str(p.relative_to(SYNC_FOLDER)), "size": p.stat().st_size, "modified": p.stat().st_mtime} for p in SYNC_FOLDER.rglob("*") if p.is_file()], key=lambda f: f["modified"], reverse=True)
        t = self._srv_file_table
        t.setRowCount(len(files))
        for i, f in enumerate(files):
            t.setItem(i, 0, QTableWidgetItem(f["name"]))
            si = QTableWidgetItem(fmt_size(f["size"]))
            si.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            t.setItem(i, 1, si)
            mi = QTableWidgetItem(fmt_time(f["modified"]))
            mi.setTextAlignment(Qt.AlignCenter)
            t.setItem(i, 2, mi)
            t.setRowHeight(i, 40)

    def _confirm_back(self):
        if self._running:
            if QMessageBox.question(self, "Go Back", "Stop server and return?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes: return
            self._stop_server()
        self.go_back.emit()


class ClientLoginWidget(QWidget):
    login_ok = pyqtSignal(str, str)
    go_back  = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._settings = QSettings("Droplink", "DroplinkApp")
        self._server_fingerprints = self._load_pinned_fingerprints()
        self._discovery_thread = None
        self._discovered_services = {}
        self._login_worker = None

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(20, 20, 20, 20)

        # Top bar
        bar = QWidget()
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Stick to top
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(0, 0, 0, 0)
        back = QPushButton("← BACK")
        back.setMinimumSize(90, 34)
        back.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        back.setObjectName("btn_subtle")
        back.clicked.connect(self._go_back)
        bl.addWidget(back)
        bl.addSpacing(16)
        bl.addWidget(label("CLIENT MODE", f"font-size:14px;font-weight:bold;color:{C['accent']};letter-spacing:3px;"))
        bl.addStretch()
        root.addWidget(bar)

        # Centered Layout
        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter) # FIXED: Perfectly centered
        center.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setMaximumWidth(500)
        card.setMinimumSize(340, 420) # FIXED: Enforced minimum size so contents won't clip
        card.setObjectName("glass_panel_accent")
        cl = QVBoxLayout(card)
        cl.setSpacing(18)
        cl.setContentsMargins(40, 48, 40, 48)

        cl.addWidget(label("◈", f"font-size:46px;color:{C['accent']};"), alignment=Qt.AlignCenter)
        cl.addWidget(label("CONNECT TO SERVER", f"font-size:16px;font-weight:bold;color:{C['text']};letter-spacing:2px;", wrap=True), alignment=Qt.AlignCenter)
        cl.addWidget(hline())

        cl.addWidget(label("SERVER ADDRESS", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))
        last_server = self._settings.value("client/last_server", "https://localhost:5000")
        self._srv = QLineEdit(str(last_server))
        self._srv.setPlaceholderText("https://192.168.x.x:5000")
        cl.addWidget(self._srv)

        cl.addWidget(label("DISCOVERED SERVERS", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))
        disc_row = QHBoxLayout()
        disc_row.setSpacing(10)
        self._discovered_combo = QComboBox()
        self._scan_btn = QPushButton("RESCAN")
        self._scan_btn.setObjectName("btn_subtle")
        self._scan_btn.setMinimumHeight(38)
        self._scan_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._scan_btn.clicked.connect(self._restart_discovery)
        disc_row.addWidget(self._discovered_combo)
        disc_row.addWidget(self._scan_btn)
        cl.addLayout(disc_row)

        self._discover_status = label("LAN discovery: idle", f"font-size:11px;color:{C['muted']};", wrap=True)
        cl.addWidget(self._discover_status)

        cl.addWidget(label("PASSWORD", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))
        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.Password)
        self._pw.setPlaceholderText("Server password")
        self._pw.returnPressed.connect(self._do_login)
        cl.addWidget(self._pw)

        self._err = label("", f"color:{C['danger']};font-size:12px;font-weight:bold;")
        self._err.setAlignment(Qt.AlignCenter)
        cl.addWidget(self._err)

        self._btn = QPushButton("CONNECT")
        self._btn.setObjectName("btn_accent")
        self._btn.setMinimumHeight(48)
        self._btn.clicked.connect(self._do_login)
        cl.addWidget(self._btn)

        center.addWidget(card)
        root.addLayout(center)
        
        self._discovered_combo.currentIndexChanged.connect(self._on_discovered_selected)
        self._refresh_discovered_combo()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_discovery()
    def hideEvent(self, event):
        self._stop_discovery()
        super().hideEvent(event)
    def _go_back(self):
        self._stop_discovery()
        self.go_back.emit()

    def _load_pinned_fingerprints(self):
        raw = self._settings.value("client/pinned_fingerprints", "{}")
        try:
            data = json.loads(raw) if isinstance(raw, str) else {}
            if isinstance(data, dict): return {str(k): _normalize_fingerprint(str(v)) for k, v in data.items() if v}
        except: pass
        return {}
    def _save_pinned_fingerprints(self):
        self._settings.setValue("client/pinned_fingerprints", json.dumps(self._server_fingerprints))

    def _selected_discovery_fingerprint(self):
        idx = self._discovered_combo.currentIndex()
        if idx < 0: return ""
        service_id = self._discovered_combo.itemData(idx)
        data = self._discovered_services.get(service_id) if service_id else None
        return _normalize_fingerprint(data.get("fingerprint", "")) if data else ""

    def _start_discovery(self):
        if self._discovery_thread and self._discovery_thread.isRunning(): return
        self._discover_status.setText("LAN discovery: scanning…")
        self._discovery_thread = DiscoveryBrowserThread()
        self._discovery_thread.service_upsert.connect(self._on_discovered_service)
        self._discovery_thread.service_remove.connect(self._on_removed_service)
        self._discovery_thread.status.connect(lambda msg: self._discover_status.setText(f"LAN discovery: {msg}"))
        self._discovery_thread.finished.connect(lambda: self._discover_status.setText("LAN discovery: no servers found" if not self._discovered_services else self._discover_status.text()))
        self._discovery_thread.start()

    def _stop_discovery(self):
        if not self._discovery_thread: return
        if self._discovery_thread.isRunning():
            self._discovery_thread.stop()
            self._discovery_thread.wait(1200)
        self._discovery_thread = None

    def _restart_discovery(self):
        self._discovered_services.clear()
        self._refresh_discovered_combo()
        self._stop_discovery()
        self._start_discovery()

    def _refresh_discovered_combo(self, selected_id=None):
        self._discovered_combo.blockSignals(True)
        current_id = selected_id if selected_id is not None else self._discovered_combo.currentData()
        self._discovered_combo.clear()
        if not self._discovered_services:
            self._discovered_combo.addItem("No LAN servers found", "")
            self._discovered_combo.setEnabled(False)
        else:
            self._discovered_combo.setEnabled(True)
            for sid in sorted(self._discovered_services.keys()): self._discovered_combo.addItem(self._discovered_services[sid]["display"], sid)
            idx = self._discovered_combo.findData(current_id) if current_id else -1
            self._discovered_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._discovered_combo.blockSignals(False)
        if self._discovered_combo.isEnabled(): self._on_discovered_selected(self._discovered_combo.currentIndex())

    def _on_discovered_service(self, payload: dict):
        sid = payload.get("id", "")
        if not sid: return
        self._discovered_services[sid] = payload
        self._refresh_discovered_combo(selected_id=sid)
        self._discover_status.setText(f"LAN discovery: {len(self._discovered_services)} server(s) found")
        current = self._srv.text().strip()
        if current in ("", "https://localhost:5000"): self._srv.setText(payload.get("url", current))

    def _on_removed_service(self, service_id: str):
        self._discovered_services.pop(service_id, None)
        self._refresh_discovered_combo()
        count = len(self._discovered_services)
        self._discover_status.setText(f"LAN discovery: {count} server(s) found" if count else "LAN discovery: no servers found")

    def _on_discovered_selected(self, index: int):
        if index < 0: return
        sid = self._discovered_combo.itemData(index)
        data = self._discovered_services.get(sid)
        if data and data.get("url"): self._srv.setText(data["url"])

    def _do_login(self):
        if self._login_worker and self._login_worker.isRunning(): return
        srv, pw = self._srv.text().strip().rstrip("/"), self._pw.text()
        srv_lower = srv.lower()
        if srv_lower.startswith("http://"): srv = f"https://{srv[7:]}"; self._srv.setText(srv)
        elif srv and not srv_lower.startswith("https://"): srv = f"https://{srv}"; self._srv.setText(srv)

        if not srv or not pw: return self._err.setText("⚠  Fill in all fields")
        try: authority = _authority_key(srv)
        except: return self._err.setText("✗  Invalid server address")

        discovered_fp = self._selected_discovery_fingerprint()
        stored_fp = _normalize_fingerprint(self._server_fingerprints.get(authority, ""))
        if discovered_fp and stored_fp and discovered_fp != stored_fp:
            warning_text = (
                "Server identity has changed.\n\n"
                f"Old fingerprint:\n{stored_fp}\n\n"
                f"New fingerprint:\n{discovered_fp}\n\n"
                "This could indicate a security risk.\n"
                "Do you want to trust this new server?"
            )
            choice = QMessageBox.question(
                self,
                "Security Warning",
                warning_text,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if choice != QMessageBox.Yes:
                return self._err.setText("Connection cancelled (untrusted server)")
            self._server_fingerprints[authority] = discovered_fp
            self._save_pinned_fingerprints()
            stored_fp = discovered_fp

        pin_to_use, allow_untrusted = stored_fp or discovered_fp, not bool(stored_fp or discovered_fp)
        self._btn.setText("CONNECTING…")
        self._btn.setEnabled(False)
        self._err.setText("")

        self._login_worker = LoginWorker(srv, pw, pin_to_use, allow_untrusted)
        self._login_worker.success.connect(self._on_login_success)
        self._login_worker.failure.connect(self._err.setText)
        self._login_worker.finished.connect(lambda: (self._btn.setText("CONNECT"), self._btn.setEnabled(True)))
        self._login_worker.start()

    def _on_login_success(self, srv: str, token: str, learned_fp: str):
        self._stop_discovery()
        self._settings.setValue("client/last_server", srv)
        authority = _authority_key(srv)
        if learned_fp:
            self._server_fingerprints[authority] = learned_fp
            self._save_pinned_fingerprints()
        self.login_ok.emit(srv, token)


class ClientDashWidget(QWidget):
    go_back = pyqtSignal()

    def __init__(self, server: str, token: str):
        super().__init__()
        self.server, self.token = server, token
        self.files, self._all_files, self._workers = [], [], []
        self._fetch_inflight = False
        self._last_preview = None
        self._btn_fx = {}
        self._btn_anim = {}
        self._ext_filter = "All files"
        self._sort_mode = "Newest first"
        self._build_ui()
        self._install_shortcuts()
        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._refresh)
        self._sync_timer.start(10000)
        self._refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(20, 20, 20, 20)

        # Top bar
        bar = QWidget()
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Stick to top
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(0, 0, 0, 0)
        back = QPushButton("⏏  DISCONNECT")
        back.setObjectName("btn_danger")
        back.setMinimumSize(140, 36)
        back.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        back.clicked.connect(self._disconnect)
        bl.addWidget(back)
        bl.addSpacing(16)
        
        srv_label = label(f"● {self.server}", f"font-size:12px;color:{C['success']};letter-spacing:1px;font-weight:bold;")
        srv_label.setMinimumWidth(100)
        bl.addWidget(srv_label)
        bl.addStretch()
        
        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setObjectName("btn_icon")
        self._refresh_btn.setFixedSize(38, 38)
        self._refresh_btn.clicked.connect(self._refresh)
        bl.addWidget(self._refresh_btn)
        bl.addSpacing(8)
        self._sync_label = label("Syncing…", f"font-size:12px;color:{C['muted']};")
        bl.addWidget(self._sync_label)
        self._sync_fx = QGraphicsOpacityEffect(self._sync_label)
        self._sync_label.setGraphicsEffect(self._sync_fx)
        self._sync_pulse = QPropertyAnimation(self._sync_fx, b"opacity", self)
        self._sync_pulse.setDuration(1800)
        self._sync_pulse.setStartValue(0.62)
        self._sync_pulse.setEndValue(1.0)
        self._sync_pulse.setEasingCurve(QEasingCurve.InOutQuad)
        self._sync_pulse.setLoopCount(-1)
        self._sync_pulse.start()
        root.addWidget(bar)

        splitter = QSplitter(Qt.Horizontal)

        # LEFT panel
        left = QFrame()
        left.setObjectName("glass_panel_accent")
        left.setMinimumWidth(350) 
        ll = QVBoxLayout(left)
        ll.setSpacing(18)
        ll.setContentsMargins(22, 22, 22, 22)

        # Toolbar responsive
        ar = QHBoxLayout()
        ar.setSpacing(12)
        
        self._upload_btn = QPushButton("↑ UPLOAD")
        self._upload_btn.setObjectName("btn_accent")
        self._upload_btn.setMinimumHeight(42)
        self._upload_btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._upload_btn.clicked.connect(self._upload)
        
        self._dl_btn = QPushButton("↓ DOWNLOAD")
        self._dl_btn.setObjectName("btn_subtle")
        self._dl_btn.setMinimumHeight(42)
        self._dl_btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._dl_btn.clicked.connect(self._download)
        
        self._prev_btn = QPushButton("◉ PREVIEW")
        self._prev_btn.setObjectName("btn_subtle")
        self._prev_btn.setMinimumHeight(42)
        self._prev_btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._prev_btn.clicked.connect(self._preview)
        
        self._del_btn = QPushButton("✕ DELETE")
        self._del_btn.setObjectName("btn_danger")
        self._del_btn.setMinimumHeight(42)
        self._del_btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._del_btn.clicked.connect(self._delete)
        
        ar.addWidget(self._upload_btn)
        ar.addWidget(self._dl_btn)
        ar.addWidget(self._prev_btn)
        ar.addWidget(self._del_btn)
        ll.addLayout(ar)

        flt = QHBoxLayout()
        flt.setSpacing(12)
        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Filter files by name…")
        self._filter_input.textChanged.connect(self._apply_filter)
        self._type_filter = QComboBox()
        self._type_filter.addItems(["All files", "Images", "Documents", "Text/Code", "Archives"])
        self._type_filter.currentTextChanged.connect(self._on_type_filter_changed)
        self._type_filter.setMinimumHeight(36)
        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["Newest first", "Oldest first", "Name A-Z", "Size largest"])
        self._sort_combo.currentTextChanged.connect(self._on_sort_mode_changed)
        self._sort_combo.setMinimumHeight(36)
        clr_flt = QPushButton("CLEAR")
        clr_flt.setObjectName("btn_subtle")
        clr_flt.setMinimumSize(70, 36)
        clr_flt.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        clr_flt.clicked.connect(lambda: self._filter_input.clear())
        flt.addWidget(self._filter_input)
        flt.addWidget(self._type_filter)
        flt.addWidget(self._sort_combo)
        flt.addWidget(clr_flt)
        ll.addLayout(flt)

        self._prog_label = label("", f"font-size:12px;color:{C['muted']};", wrap=True)
        self._prog_label.hide()
        self._prog_bar = QProgressBar()
        self._prog_bar.setFixedHeight(8)
        self._prog_bar.hide()
        ll.addWidget(self._prog_label)
        ll.addWidget(self._prog_bar)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["FILENAME", "SIZE", "MODIFIED"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.setColumnWidth(1, 100)
        self._table.setColumnWidth(2, 160)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAcceptDrops(True)
        self._table.viewport().setAcceptDrops(True)
        self._table.viewport().installEventFilter(self)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.doubleClicked.connect(self._preview)
        self._table_fx = QGraphicsOpacityEffect(self._table)
        self._table.setGraphicsEffect(self._table_fx)
        self._table_fx.setOpacity(1.0)
        self._table_flash = QPropertyAnimation(self._table_fx, b"opacity", self)
        self._table_flash.setDuration(140)
        self._table_flash.setStartValue(0.84)
        self._table_flash.setEndValue(1.0)
        self._table_flash.setEasingCurve(QEasingCurve.OutQuad)
        ll.addWidget(self._table)

        self._stats_label = label("0 files", f"font-size:12px;color:{C['muted']};")
        ll.addWidget(self._stats_label)

        # RIGHT panel
        right = QFrame()
        right.setObjectName("glass_panel")
        right.setMinimumWidth(200) # Reduced constraint
        rl = QVBoxLayout(right)
        rl.setSpacing(18)
        rl.setContentsMargins(22, 22, 22, 22)

        ph = QHBoxLayout()
        ph.addWidget(label("PREVIEW PANEL", f"font-size:11px;color:{C['muted']};letter-spacing:2px;font-weight:bold;"))
        ph.addStretch()
        self._pop_btn = QPushButton("⤢")
        self._pop_btn.setObjectName("btn_icon")
        self._pop_btn.setFixedSize(30, 30)
        self._pop_btn.clicked.connect(self._popup_preview)
        self._pop_btn.setEnabled(False)
        ph.addWidget(self._pop_btn)
        rl.addLayout(ph)
        rl.addWidget(hline())

        self._prev_stack = QStackedWidget()
        placeholder = QWidget()
        phl = QVBoxLayout(placeholder)
        phl.addWidget(label("◈", f"font-size:42px;color:rgba(255,255,255,0.1);"), alignment=Qt.AlignCenter)
        phl.addWidget(label("Select a file and click\nPREVIEW to inspect it", f"font-size:12px;color:{C['dim']};text-align:center;", wrap=True), alignment=Qt.AlignCenter)
        
        self._img_scroll = QScrollArea()
        self._img_scroll.setWidgetResizable(True)
        self._img_scroll.setStyleSheet("background:transparent;border:none;")
        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignCenter)
        self._img_scroll.setWidget(self._img_label)
        
        self._txt_view = QTextEdit()
        self._txt_view.setReadOnly(True)
        self._txt_view.setFont(QFont("Consolas", 12))
        
        self._unsup = QLabel()
        self._unsup.setAlignment(Qt.AlignCenter)
        self._unsup.setWordWrap(True)
        self._unsup.setStyleSheet(f"font-size:13px;color:{C['muted']};")
        
        self._loading = QLabel("Loading preview…")
        self._loading.setAlignment(Qt.AlignCenter)
        self._loading.setStyleSheet(f"font-size:13px;color:{C['muted']};")

        self._prev_stack.addWidget(placeholder)
        self._prev_stack.addWidget(self._img_scroll)
        self._prev_stack.addWidget(self._txt_view)
        self._prev_stack.addWidget(self._unsup)
        self._prev_stack.addWidget(self._loading)
        rl.addWidget(self._prev_stack)

        self._prev_filename = label("", f"font-size:11px;color:{C['muted']};", wrap=True)
        rl.addWidget(self._prev_filename)

        splitter.addWidget(left)
        splitter.addWidget(right)
        # Instead of strict pixel sizes, use stretch factors for responsiveness
        splitter.setStretchFactor(0, 3) 
        splitter.setStretchFactor(1, 2)
        
        root.addWidget(splitter)
        self._set_action_state(False)
        self._bind_button_feedback([
            back, self._refresh_btn, self._upload_btn, self._dl_btn,
            self._prev_btn, self._del_btn, self._pop_btn, clr_flt
        ])

    def _install_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self._refresh)
        QShortcut(QKeySequence("Ctrl+U"), self, activated=self._upload)
        QShortcut(QKeySequence("Delete"), self, activated=self._delete)

    def _on_type_filter_changed(self, text: str):
        self._ext_filter = text
        self._apply_filter(selected_name=self._sel_file())

    def _on_sort_mode_changed(self, text: str):
        self._sort_mode = text
        self._apply_filter(selected_name=self._sel_file())

    def _match_type_filter(self, filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        if self._ext_filter == "All files":
            return True
        if self._ext_filter == "Images":
            return ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
        if self._ext_filter == "Documents":
            return ext in {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}
        if self._ext_filter == "Text/Code":
            return ext in {".txt", ".md", ".json", ".xml", ".csv", ".py", ".js", ".ts", ".html", ".css"}
        if self._ext_filter == "Archives":
            return ext in {".zip", ".rar", ".7z", ".tar", ".gz"}
        return True

    def _sort_files(self, files: list) -> list:
        if self._sort_mode == "Oldest first":
            return sorted(files, key=lambda f: f["modified"])
        if self._sort_mode == "Name A-Z":
            return sorted(files, key=lambda f: f["name"].lower())
        if self._sort_mode == "Size largest":
            return sorted(files, key=lambda f: f["size"], reverse=True)
        return sorted(files, key=lambda f: f["modified"], reverse=True)

    def eventFilter(self, obj, event):
        if obj is self._table.viewport():
            if event.type() == QEvent.DragEnter and event.mimeData().hasUrls():
                event.acceptProposedAction()
                return True
            if event.type() == QEvent.Drop and event.mimeData().hasUrls():
                local_paths = []
                for url in event.mimeData().urls():
                    p = url.toLocalFile()
                    if p and os.path.isfile(p):
                        local_paths.append(p)
                if local_paths:
                    self._upload_paths(local_paths)
                    event.acceptProposedAction()
                return True
        return super().eventFilter(obj, event)

    def _track_worker(self, w: QThread):
        self._workers.append(w)
        w.finished.connect(lambda worker=w: (self._workers.remove(worker) if worker in self._workers else None, worker.deleteLater()))

    def _bind_button_feedback(self, buttons):
        for btn in buttons:
            fx = QGraphicsOpacityEffect(btn)
            fx.setOpacity(1.0)
            btn.setGraphicsEffect(fx)
            self._btn_fx[btn] = fx
            btn.pressed.connect(lambda b=btn: self._animate_button_feedback(b, 0.82))
            btn.released.connect(lambda b=btn: self._animate_button_feedback(b, 1.0))

    def _animate_button_feedback(self, btn: QPushButton, opacity: float):
        fx = self._btn_fx.get(btn)
        if not fx:
            return
        anim = QPropertyAnimation(fx, b"opacity", self)
        anim.setDuration(70 if opacity < 1.0 else 110)
        anim.setStartValue(fx.opacity())
        anim.setEndValue(opacity)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        self._btn_anim[btn] = anim
        anim.start()

    def _set_action_state(self, has_sel: bool):
        self._dl_btn.setEnabled(has_sel)
        self._prev_btn.setEnabled(has_sel)
        self._del_btn.setEnabled(has_sel)
    def _on_selection_changed(self):
        self._set_action_state(self._sel_file() is not None)
        if self._table_flash.state() == QPropertyAnimation.Running:
            self._table_flash.stop()
        self._table_flash.start()

    def _refresh(self):
        if self._fetch_inflight: return
        self._fetch_inflight = True
        self._refresh_btn.setEnabled(False)
        self._sync_label.setText("⟳ Syncing…")
        w = FileFetchWorker(self.server, self.token)
        w.result.connect(self._populate)
        w.error.connect(lambda err: self._sync_label.setText(f"✗ {err}"))
        w.finished.connect(lambda: (setattr(self, '_fetch_inflight', False), self._refresh_btn.setEnabled(True)))
        self._track_worker(w)
        w.start()

    def _populate(self, files: list):
        selected_name = self._sel_file()
        self._all_files = list(files)
        self._apply_filter(selected_name=selected_name)
        self._sync_label.setText("✓ Synced")

    def _apply_filter(self, _text=None, selected_name=None):
        query = self._filter_input.text().strip().lower()
        filtered = [f for f in self._all_files if self._match_type_filter(f["name"])]
        if query:
            filtered = [f for f in filtered if query in f["name"].lower()]
        self.files = self._sort_files(filtered)
        self._render_table(selected_name=selected_name)

    def _render_table(self, selected_name=None):
        t = self._table
        t.setRowCount(len(self.files))
        selected_row = -1
        for i, f in enumerate(self.files):
            ni = QTableWidgetItem(f["name"])
            ni.setData(Qt.UserRole, f["name"])
            si, mi = QTableWidgetItem(fmt_size(f["size"])), QTableWidgetItem(fmt_time(f["modified"]))
            si.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            mi.setTextAlignment(Qt.AlignCenter)
            si.setForeground(QColor(C["muted"]))
            mi.setForeground(QColor(C["muted"]))
            t.setItem(i, 0, ni); t.setItem(i, 1, si); t.setItem(i, 2, mi)
            t.setRowHeight(i, 40)
            if selected_name and f["name"] == selected_name: selected_row = i
        if selected_row >= 0: t.selectRow(selected_row)
        else: t.clearSelection()
        shown, total, total_size = len(self.files), len(self._all_files), sum(f["size"] for f in self._all_files)
        self._stats_label.setText(f"{shown}/{total} shown  ·  {fmt_size(total_size)} total" if shown != total else f"{total} files  ·  {fmt_size(total_size)}")
        self._on_selection_changed()

    def _sel_file(self) -> Optional[str]:
        row = self._table.currentRow()
        item = self._table.item(row, 0) if row >= 0 else None
        return item.data(Qt.UserRole) if item else None

    def _upload(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files to Upload")
        self._upload_paths(paths)

    def _upload_paths(self, paths):
        for p in paths:
            if not os.path.isfile(p):
                continue
            self._prog_label.setText(f"Uploading: {os.path.basename(p)}")
            self._prog_label.show(); self._prog_bar.setValue(0); self._prog_bar.show()
            w = UploadWorker(self.server, self.token, p)
            w.progress.connect(self._prog_bar.setValue)
            w.done.connect(lambda ok, msg: (self._prog_bar.setValue(100), self._prog_label.setText(f"{'✓ Uploaded' if ok else '✗ Upload failed'}: {msg}"), QTimer.singleShot(2500, self._hide_prog), self._refresh() if ok else None))
            self._track_worker(w)
            w.start()

    def _download(self):
        name = self._sel_file()
        if not name: return
        save, _ = QFileDialog.getSaveFileName(self, "Save As", os.path.basename(name))
        if not save: return
        self._prog_label.setText(f"Downloading: {os.path.basename(name)}")
        self._prog_label.show(); self._prog_bar.setValue(0); self._prog_bar.show()
        w = DownloadWorker(self.server, self.token, name, save)
        w.progress.connect(self._prog_bar.setValue)
        w.done.connect(lambda ok, msg: (self._prog_bar.setValue(100 if ok else 0), self._prog_label.setText(f"{'✓ Saved to' if ok else '✗ Failed'}: {msg}"), QTimer.singleShot(3000, self._hide_prog)))
        self._track_worker(w)
        w.start()

    def _preview(self):
        name = self._sel_file()
        if not name: return
        self._prev_stack.setCurrentIndex(4)
        self._prev_filename.setText(f"Loading {os.path.basename(name)}…")
        w = PreviewWorker(self.server, self.token, name)
        w.done.connect(lambda data, mime: self._show_inline(name, data, mime))
        w.error.connect(lambda msg: (setattr(self, '_last_preview', None), self._pop_btn.setEnabled(False), self._unsup.setText(f"✗  Preview error:\n{msg}"), self._prev_stack.setCurrentIndex(3)))
        self._track_worker(w)
        w.start()

    def _show_inline(self, name: str, data: bytes, mime: str):
        self._last_preview = (name, data, mime)
        self._pop_btn.setEnabled(True)
        self._prev_filename.setText(f"{os.path.basename(name)}  ·  {fmt_size(len(data))}")
        if mime.startswith("image/"):
            px = QPixmap(); px.loadFromData(QByteArray(data))
            avail = max(self._img_scroll.width() - 20, 100)
            if px.width() > avail: px = px.scaledToWidth(avail, Qt.SmoothTransformation)
            self._img_label.setPixmap(px)
            self._prev_stack.setCurrentIndex(1)
        elif mime.startswith("text/") or mime in ("application/json", "application/xml", "application/javascript"):
            try: txt = data.decode("utf-8")
            except: txt = data.decode("latin-1", errors="replace")
            self._txt_view.setPlainText(txt)
            self._prev_stack.setCurrentIndex(2)
        else:
            self._unsup.setText(f"⚠  Cannot preview this file type.\n\nType: {mime}\nSize: {fmt_size(len(data))}")
            self._prev_stack.setCurrentIndex(3)

    def _popup_preview(self):
        if self._last_preview: PreviewDialog(*self._last_preview, parent=self).exec_()

    def _delete(self):
        name = self._sel_file()
        if not name: return
        if QMessageBox.question(self, "Confirm Delete", f"Delete '{name}'?", QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes: return
        try:
            if _api_request("DELETE", f"{self.server}/delete/{name}", headers={"X-Auth-Token": self.token}, timeout=5).ok:
                self._refresh()
                if self._last_preview and self._last_preview[0] == name:
                    self._last_preview = None; self._pop_btn.setEnabled(False); self._prev_stack.setCurrentIndex(0); self._prev_filename.setText("")
        except Exception as e: self._stats_label.setText(f"✗ {e}")

    def _hide_prog(self): self._prog_bar.hide(); self._prog_label.hide()

    def _disconnect(self):
        self._sync_timer.stop()
        try: _api_request("POST", f"{self.server}/logout", headers={"X-Auth-Token": self.token}, timeout=3)
        except: pass
        self.go_back.emit()

class PreviewDialog(QDialog):
    def __init__(self, filename: str, data: bytes, mime: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Preview — {filename}")
        self.resize(860, 660)
        lay = QVBoxLayout(self)
        hdr = QHBoxLayout()
        hdr.addWidget(label(f"📄  {filename}", f"font-size:14px;color:{C['text']};font-weight:bold;", wrap=True))
        hdr.addStretch()
        hdr.addWidget(label(mime, f"font-size:11px;color:{C['muted']};"))
        lay.addLayout(hdr)
        lay.addWidget(hline())
        if mime.startswith("image/"):
            scroll = QScrollArea()
            scroll.setStyleSheet(f"background:rgba(0,0,0,0.2);border:1px solid {C['border_s']};border-radius:12px;")
            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignCenter)
            px = QPixmap(); px.loadFromData(QByteArray(data))
            if px.width() > 800: px = px.scaledToWidth(800, Qt.SmoothTransformation)
            img_lbl.setPixmap(px)
            scroll.setWidget(img_lbl)
            lay.addWidget(scroll)
        elif mime.startswith("text/") or mime in ("application/json", "application/xml", "application/javascript"):
            txt = QTextEdit()
            txt.setReadOnly(True)
            try: txt.setPlainText(data.decode("utf-8"))
            except: txt.setPlainText(data.decode("latin-1", errors="replace"))
            txt.setFont(QFont("Consolas", 12))
            lay.addWidget(txt)
        btn = QPushButton("CLOSE")
        btn.setObjectName("btn_accent")
        btn.setMinimumHeight(40)
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Droplink v2.1")
        self.resize(1100, 750)
        # FIXED: Enforced a strong global minimum size so panels never squish/clip
        self.setMinimumSize(850, 600) 
        self._page_anim = None
        
        self._stack = QStackedWidget()
        self._launcher, self._srv_widget, self._cli_login = LauncherWidget(), ServerWidget(), ClientLoginWidget()
        
        self._stack.addWidget(self._launcher)
        self._stack.addWidget(self._srv_widget)
        self._stack.addWidget(self._cli_login)
        self.setCentralWidget(self._stack)
        
        self._launcher.chose_server.connect(lambda: self._switch_page(1))
        self._launcher.chose_client.connect(lambda: self._switch_page(2))
        self._srv_widget.go_back.connect(lambda: self._switch_page(0))
        self._cli_login.go_back.connect(lambda: self._switch_page(0))
        self._cli_login.login_ok.connect(self._on_login)
        
        sb = self.statusBar()
        sb.setStyleSheet(f"background:rgba(0,0,0,0.4);color:{C['muted']};border-top:1px solid rgba(255,255,255,0.05);")
        sb.showMessage("  Welcome to Droplink v2.1")

    def _switch_page(self, index: int):
        current = self._stack.currentWidget()
        if not current or self._stack.currentIndex() == index:
            self._stack.setCurrentIndex(index)
            return
        if self._page_anim and self._page_anim.state() == QPropertyAnimation.Running:
            self._page_anim.stop()
        fade_out = QPropertyAnimation(current.graphicsEffect() or QGraphicsOpacityEffect(current), b"opacity", self)
        if current.graphicsEffect() is None:
            current.setGraphicsEffect(fade_out.targetObject())
        fade_out.setDuration(120)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.14)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)

        def _activate_next():
            self._stack.setCurrentIndex(index)
            nxt = self._stack.currentWidget()
            if not nxt:
                return
            fx = QGraphicsOpacityEffect(nxt)
            nxt.setGraphicsEffect(fx)
            fade_in = QPropertyAnimation(fx, b"opacity", self)
            fade_in.setDuration(170)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.OutQuad)

            def _clear_effect():
                nxt.setGraphicsEffect(None)

            fade_in.finished.connect(_clear_effect)
            self._page_anim = fade_in
            fade_in.start()

        fade_out.finished.connect(_activate_next)
        self._page_anim = fade_out
        fade_out.start()

    def _on_login(self, server: str, token: str):
        dash = ClientDashWidget(server, token)
        dash.go_back.connect(self._on_client_back)
        self._stack.addWidget(dash)
        self._switch_page(self._stack.indexOf(dash))
        self.statusBar().showMessage(f"  Connected to {server}")

    def _on_client_back(self):
        w = self._stack.currentWidget()
        self._switch_page(2)
        self._stack.removeWidget(w); w.deleteLater()
        self.statusBar().showMessage("  Disconnected")

    def closeEvent(self, event):
        if self._srv_widget._running:
            self._srv_widget._stop_server()
            if self._srv_widget._server_thread: self._srv_widget._server_thread.wait(2000)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    app.setApplicationName("Droplink")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
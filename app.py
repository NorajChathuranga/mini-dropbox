"""
Droplink v2 — Unified Launcher
Run: python app.py
Choose Server or Client mode from the launcher screen.

Dependencies: pip install fastapi uvicorn python-multipart requests PyQt5 bcrypt cryptography
"""

import sys, os, time, socket, secrets, mimetypes, ssl, ipaddress
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import uvicorn
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

# ── FastAPI (server side) ──────────────────────────────────────────────────────
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

# ── Qt ─────────────────────────────────────────────────────────────────────────
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QFileDialog, QMessageBox, QFrame, QHeaderView,
    QStackedWidget, QAbstractItemView, QTextEdit, QSplitter,
    QScrollArea, QSizePolicy, QSpacerItem, QDialog, QDialogButtonBox,
    QComboBox
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QByteArray, QSettings
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QPixmap, QImage, QTextCursor, QIntValidator
)

# ══════════════════════════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════════════════════════
C = {
    "bg":       "#080A10",
    "panel":    "#0F1422",
    "card":     "#161C2D",
    "hover":    "#202942",
    "border":   "#2A3553",
    "accent":   "#00F5C3",
    "accent2":  "#5B7FFF",
    "purple":   "#A855F7",
    "text":     "#E5ECFA",
    "muted":    "#9AA8C8",
    "dim":      "#5B698D",
    "danger":   "#FF4D6A",
    "warn":     "#FFB020",
    "success":  "#00F5C3",
}

QSS = f"""
* {{ font-family: 'Consolas', 'Courier New', monospace; }}
QMainWindow, QWidget, QDialog {{ background: {C['bg']}; color: {C['text']}; }}
QFrame {{ background: transparent; }}
QLabel {{ color: {C['text']}; }}

QLineEdit {{
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    padding: 9px 12px;
    font-size: 13px;
    selection-background-color: {C['accent2']};
}}
QLineEdit::placeholder {{ color: {C['dim']}; }}
QLineEdit:read-only {{ background: {C['panel']}; color: {C['text']}; }}
QLineEdit:focus {{ border-color: {C['accent']}; }}

QComboBox {{
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    padding: 8px 12px;
    font-size: 12px;
}}
QComboBox:focus {{ border-color: {C['accent']}; }}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
}}
QComboBox QAbstractItemView {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    color: {C['text']};
    selection-background-color: {C['hover']};
    selection-color: {C['text']};
}}

QPushButton {{
    background: {C['card']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    padding: 9px 18px;
    font-size: 12px;
    letter-spacing: 1px;
}}
QPushButton:hover {{ background: {C['hover']}; border-color: {C['accent2']}; color: {C['text']}; }}
QPushButton:pressed {{ background: {C['panel']}; }}
QPushButton:disabled {{ color: {C['dim']}; border-color: {C['border']}; background: {C['panel']}; }}

QPushButton#btn_subtle {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    color: {C['muted']};
}}
QPushButton#btn_subtle:hover {{
    border-color: {C['accent2']};
    color: {C['text']};
    background: {C['hover']};
}}

QPushButton#btn_icon,
QPushButton#btn_field {{
    background: {C['panel']};
    border: 1px solid {C['border']};
    color: {C['muted']};
    padding: 0;
    font-size: 13px;
    letter-spacing: 0;
}}
QPushButton#btn_icon:hover,
QPushButton#btn_field:hover {{
    border-color: {C['accent']};
    color: {C['accent']};
    background: {C['hover']};
}}

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
    background: #2A1119;
    border: 1px solid {C['danger']};
    color: #FF8CA1;
}}
QPushButton#btn_danger:hover {{ background: {C['danger']}; color: white; }}

QPushButton#btn_stop {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #7B0020, stop:1 #5B0015);
    border: 1px solid {C['danger']};
    color: #FFD2DB;
    font-weight: bold;
}}
QPushButton#btn_stop:hover {{ background: {C['danger']}; color: white; }}

QTableWidget {{
    background: #11192B;
    alternate-background-color: #0D1322;
    border: 1px solid {C['border']};
    border-radius: 8px;
    gridline-color: {C['border']};
    color: {C['text']};
    font-size: 12px;
    outline: none;
}}
QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {C['border']}; }}
QTableWidget::item:selected {{ background: #263452; color: #F2F8FF; }}
QTableWidget::item:hover {{ background: #1E2A44; }}
QHeaderView::section {{
    background: #1A2236;
    color: #B8C5E3;
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
    background: #10182A;
    border: 1px solid {C['border']};
    border-radius: 8px;
    color: {C['text']};
    font-size: 12px;
    padding: 8px;
    selection-background-color: {C['accent2']};
}}

QScrollBar:vertical {{
    background: #0D1322; width: 6px; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {C['dim']}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: #0D1322; height: 6px; border-radius: 3px;
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


def _hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=13))


def _verify_password(password: str, password_hash: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)
    except ValueError:
        return False


TLS_DIR = Path("certs")
TLS_CERT_FILE = TLS_DIR / "droplink-cert.pem"
TLS_KEY_FILE = TLS_DIR / "droplink-key.pem"

DISCOVERY_SERVICE_TYPE = "_droplink._tcp.local."


def _cert_fingerprint_sha256(cert_file: Path) -> str:
    try:
        cert = x509.load_pem_x509_certificate(cert_file.read_bytes())
        return cert.fingerprint(hashes.SHA256()).hex()
    except Exception:
        return ""


def _ensure_self_signed_cert(cert_file: Path, key_file: Path):
    if cert_file.exists() and key_file.exists():
        return

    cert_file.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Droplink Local Server"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Droplink"),
    ])

    san_entries = [
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
    ]
    local_ip = get_local_ip()
    try:
        san_entries.append(x509.IPAddress(ipaddress.ip_address(local_ip)))
    except ValueError:
        pass

    now = datetime.utcnow()
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

    key_file.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    try:
        os.chmod(key_file, 0o600)
    except OSError:
        pass


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", Path(name or "").name)
    return cleaned.strip("._")


# ══════════════════════════════════════════════════════════════════════════════
#  FASTAPI BACKEND (runs in a thread)
# ══════════════════════════════════════════════════════════════════════════════
SYNC_FOLDER = Path("synced")
SYNC_FOLDER.mkdir(exist_ok=True)
_api_app = FastAPI(title="Droplink API", version="2.0")
_server_state = {
    "password_hash": _hash_password("dropbox123"),
    "tokens": {},          # token -> expiry
    "log_cb": None,        # callable(msg) — GUI log callback
    "clients": {},         # ip -> last_seen timestamp
}


class LoginPayload(BaseModel):
    password: str = ""


def _log(msg):
    ts = time.strftime("%H:%M:%S")
    full = f"[{ts}]  {msg}"
    if _server_state["log_cb"]:
        _server_state["log_cb"](full)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _resolve_within_sync(path_str: str) -> Path:
    root = SYNC_FOLDER.resolve()
    full = (root / path_str).resolve()
    try:
        full.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden path")
    return full


def _require_auth(
    request: Request,
    x_auth_token: Optional[str] = Header(default=None, alias="X-Auth-Token"),
) -> str:
    tok = (x_auth_token or "").strip()
    if tok not in _server_state["tokens"]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if time.time() > _server_state["tokens"][tok]:
        _server_state["tokens"].pop(tok, None)
        raise HTTPException(status_code=401, detail="Session expired")
    _server_state["clients"][_client_ip(request)] = time.time()
    return tok


@_api_app.get("/ping")
async def _ping():
    return {"status": "ok", "version": "2.0"}


@_api_app.post("/login")
async def _login(data: LoginPayload, request: Request):
    if not _verify_password(data.password, _server_state["password_hash"]):
        _log(f"❌  Failed login from {_client_ip(request)}")
        raise HTTPException(status_code=403, detail="Invalid password")
    tok = secrets.token_hex(24)
    _server_state["tokens"][tok] = time.time() + 86400
    _log(f"✅  Client connected: {_client_ip(request)}")
    return {"token": tok}


@_api_app.post("/logout")
async def _logout(request: Request, tok: str = Depends(_require_auth)):
    _server_state["tokens"].pop(tok, None)
    _log(f"👋  Client disconnected: {_client_ip(request)}")
    return {"status": "ok"}


@_api_app.get("/files")
async def _files(_tok: str = Depends(_require_auth)):
    out = []
    for p in SYNC_FOLDER.rglob("*"):
        if p.is_file():
            st = p.stat()
            out.append({
                "name": str(p.relative_to(SYNC_FOLDER)),
                "size": st.st_size,
                "modified": st.st_mtime,
            })
    return {"files": out}


@_api_app.post("/upload")
async def _upload(
    request: Request,
    _tok: str = Depends(_require_auth),
    file: UploadFile = File(...),
    path: str = Form(default=""),
):
    name = _safe_filename(file.filename or "")
    if not name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    relative_dest = str(Path(path) / name) if path else name
    dest = _resolve_within_sync(relative_dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    with dest.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    await file.close()

    _log(f"↑  Uploaded: {name}  ({fmt_size(dest.stat().st_size)})  from {_client_ip(request)}")
    return {"status": "ok", "file": name}


@_api_app.get("/download/{fp:path}")
async def _download(fp: str, request: Request, _tok: str = Depends(_require_auth)):
    full = _resolve_within_sync(fp)
    if not full.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    mime, _ = mimetypes.guess_type(str(full))
    _log(f"↓  Downloaded: {fp}  by {_client_ip(request)}")
    return FileResponse(
        path=str(full),
        media_type=mime or "application/octet-stream",
        filename=full.name,
    )


@_api_app.get("/preview/{fp:path}")
async def _preview(fp: str, _tok: str = Depends(_require_auth)):
    full = _resolve_within_sync(fp)
    if not full.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    mime, _ = mimetypes.guess_type(str(full))
    return FileResponse(path=str(full), media_type=mime or "application/octet-stream")


@_api_app.delete("/delete/{fp:path}")
async def _delete(fp: str, request: Request, _tok: str = Depends(_require_auth)):
    full = _resolve_within_sync(fp)
    if not full.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    full.unlink()
    _log(f"🗑  Deleted: {fp}  by {_client_ip(request)}")
    return {"status": "ok"}


class UvicornThread(QThread):
    started_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self._server = None
        self.cert_file = TLS_CERT_FILE
        self.key_file = TLS_KEY_FILE

    def run(self):
        import logging

        logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
        logging.getLogger("uvicorn.access").setLevel(logging.ERROR)

        try:
            _ensure_self_signed_cert(self.cert_file, self.key_file)
            config = uvicorn.Config(
                _api_app,
                host="0.0.0.0",
                port=self.port,
                access_log=False,
                log_level="error",
                ssl_certfile=str(self.cert_file),
                ssl_keyfile=str(self.key_file),
            )
            self._server = uvicorn.Server(config)
            self.started_ok.emit()
            self._server.run()
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            self._server = None

    def stop(self):
        if self._server is not None:
            self._server.should_exit = True

# ══════════════════════════════════════════════════════════════════════════════
#  WORKER THREADS (client side)
# ══════════════════════════════════════════════════════════════════════════════
import requests as _req
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


def _api_request(method, url, **kwargs):
    if url.lower().startswith("https://"):
        kwargs.setdefault("verify", False)
    return _req.request(method, url, **kwargs)


class ZeroconfAdvertiser:
    def __init__(self, *, local_ip: str, port: int, fingerprint: str):
        self.local_ip = local_ip
        self.port = port
        self.fingerprint = fingerprint
        self._zeroconf = None
        self._service_info = None

    def start(self):
        host = socket.gethostname() or "droplink"
        service_name = f"Droplink-{host}-{self.port}.{DISCOVERY_SERVICE_TYPE}"
        properties = {
            "name": host,
            "proto": "https",
            "ver": "2",
            "fp": self.fingerprint,
        }
        encoded_props = {k.encode("utf-8"): v.encode("utf-8") for k, v in properties.items()}
        self._service_info = ServiceInfo(
            type_=DISCOVERY_SERVICE_TYPE,
            name=service_name,
            addresses=[socket.inet_aton(self.local_ip)],
            port=self.port,
            properties=encoded_props,
            server=f"{host}.local.",
        )
        self._zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self._zeroconf.register_service(self._service_info)

    def stop(self):
        try:
            if self._zeroconf and self._service_info:
                self._zeroconf.unregister_service(self._service_info)
        except Exception:
            pass
        try:
            if self._zeroconf:
                self._zeroconf.close()
        except Exception:
            pass
        self._service_info = None
        self._zeroconf = None


class _DiscoveryListener(ServiceListener):
    def __init__(self, owner):
        self.owner = owner

    def add_service(self, zc, type_, name):
        self.owner._emit_service(name)

    def update_service(self, zc, type_, name):
        self.owner._emit_service(name)

    def remove_service(self, zc, type_, name):
        self.owner.service_remove.emit(name)


class DiscoveryBrowserThread(QThread):
    service_upsert = pyqtSignal(object)
    service_remove = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self._zeroconf = None
        self._browser = None

    def run(self):
        self._running = True
        try:
            self._zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
            listener = _DiscoveryListener(self)
            self._browser = ServiceBrowser(self._zeroconf, DISCOVERY_SERVICE_TYPE, listener)
            self.status.emit("Scanning LAN for Droplink servers...")
            while self._running:
                self.msleep(200)
        except Exception as e:
            self.status.emit(f"Discovery unavailable: {e}")
        finally:
            try:
                if self._browser:
                    self._browser.cancel()
            except Exception:
                pass
            try:
                if self._zeroconf:
                    self._zeroconf.close()
            except Exception:
                pass
            self._browser = None
            self._zeroconf = None

    def stop(self):
        self._running = False

    def _emit_service(self, service_name: str):
        if not self._zeroconf:
            return
        info = self._zeroconf.get_service_info(DISCOVERY_SERVICE_TYPE, service_name, timeout=2000)
        if not info or not info.addresses:
            return
        ip = socket.inet_ntoa(info.addresses[0])
        props = {}
        for k, v in (info.properties or {}).items():
            key = k.decode("utf-8", errors="ignore") if isinstance(k, bytes) else str(k)
            val = v.decode("utf-8", errors="ignore") if isinstance(v, bytes) else str(v)
            props[key] = val

        proto = props.get("proto", "https")
        url = f"{proto}://{ip}:{info.port}"
        display = f"{props.get('name', 'Droplink')} ({ip}:{info.port})"
        self.service_upsert.emit(
            {
                "id": service_name,
                "display": display,
                "url": url,
                "fingerprint": props.get("fp", ""),
            }
        )

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
            this = self

            with open(self.path, "rb") as orig:
                class Wrapped:
                    def read(self_, n=-1):
                        chunk = orig.read(n)
                        uploaded[0] += len(chunk)
                        if size:
                            this.progress.emit(int(uploaded[0] / size * 100))
                        return chunk

                    def __getattr__(self_, k):
                        return getattr(orig, k)

                r = _api_request(
                    "POST",
                    f"{self.srv}/upload",
                    headers={"X-Auth-Token": self.tok},
                    files={"file": (name, Wrapped())},
                    timeout=120,
                )

            if r.ok:
                self.done.emit(True, name)
            else:
                self.done.emit(False, f"{name} (HTTP {r.status_code})")
        except Exception as e: self.done.emit(False, str(e))

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(bool, str)
    def __init__(self, srv, tok, rp, sp):
        super().__init__(); self.srv=srv; self.tok=tok; self.rp=rp; self.sp=sp
    def run(self):
        try:
            r = _api_request("GET", f"{self.srv}/download/{self.rp}",
                headers={"X-Auth-Token":self.tok}, stream=True, timeout=120)
            if not r.ok:
                self.done.emit(False, f"HTTP {r.status_code}")
                return
            total = int(r.headers.get("content-length",0))
            done = 0
            with open(self.sp,"wb") as f:
                for chunk in r.iter_content(65536):
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
            r = _api_request("GET", f"{self.srv}/preview/{self.rp}",
                headers={"X-Auth-Token":self.tok}, timeout=30)
            if not r.ok:
                self.error.emit(f"HTTP {r.status_code}")
                return
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
            r = _api_request("GET", f"{self.srv}/files",
                headers={"X-Auth-Token":self.tok}, timeout=8)
            if not r.ok:
                self.error.emit(f"HTTP {r.status_code}")
                return
            self.result.emit(r.json().get("files",[]))
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

        foot = label("Local network only  ·  Self-signed HTTPS enabled",
            f"font-size:10px;color:{C['muted']};")
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
        self._server_thread = None
        self._discovery_advertiser = None
        self._running = False
        self._folder_btn = None
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
        back_btn.setObjectName("btn_subtle")
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
        self._port_input.setValidator(QIntValidator(1, 65535, self))
        self._port_input.setPlaceholderText("1 - 65535")
        ll.addWidget(self._port_input)

        # Password
        ll.addWidget(label("Password", f"font-size:11px;color:{C['muted']};"))
        pw_row = QHBoxLayout(); pw_row.setSpacing(6)
        self._pw_input = QLineEdit("dropbox123")
        self._pw_input.setEchoMode(QLineEdit.Password)
        self._show_pw = QPushButton("👁"); self._show_pw.setFixedSize(36,36)
        self._show_pw.setObjectName("btn_field")
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
        self._folder_btn = QPushButton("…"); self._folder_btn.setFixedSize(36,36)
        self._folder_btn.setObjectName("btn_field")
        self._folder_btn.clicked.connect(self._pick_folder)
        fol_row.addWidget(self._folder_input); fol_row.addWidget(self._folder_btn)
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

        self._info_local  = label("Local:  —", f"font-size:11px;color:{C['text']};")
        self._info_net    = label("Network:  —", f"font-size:11px;color:{C['text']};")
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
        clr_btn.setObjectName("btn_subtle")
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
        ref_btn.setObjectName("btn_icon")
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
        self._srv_file_table.setAlternatingRowColors(True)
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

    def _set_status(self, text, color):
        self._status_dot.setText(text)
        self._status_dot.setStyleSheet(f"font-size:11px;color:{color};letter-spacing:1px;")

    def _set_server_controls(self, enabled):
        self._port_input.setEnabled(enabled)
        self._pw_input.setEnabled(enabled)
        self._show_pw.setEnabled(enabled)
        if self._folder_btn:
            self._folder_btn.setEnabled(enabled)

    def _start_server(self):
        if self._running:
            return

        pw = self._pw_input.text().strip()
        if not pw:
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return
        if len(pw) < 10:
            QMessageBox.warning(self, "Error", "Use a stronger password (at least 10 characters).")
            return

        port_text = self._port_input.text().strip()
        if not port_text:
            QMessageBox.warning(self, "Error", "Enter a valid port (1-65535).")
            return

        try:
            port = int(port_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Port must be a number.")
            return

        if not 1 <= port <= 65535:
            QMessageBox.warning(self, "Error", "Port must be between 1 and 65535.")
            return

        _server_state["password_hash"] = _hash_password(pw)
        _server_state["tokens"].clear()
        _server_state["clients"].clear()
        _server_state["log_cb"] = self._append_log

        self._server_thread = UvicornThread(port)
        self._server_thread.started_ok.connect(lambda p=port: self._on_server_started(p))
        self._server_thread.failed.connect(self._on_server_failed)
        self._server_thread.finished.connect(self._on_server_stopped)

        self._set_server_controls(False)
        self._start_btn.setEnabled(False)
        self._set_status("● STARTING…", C["warn"])
        self._append_log(f"⏳  Starting server on port {port}...")
        self._server_thread.start()

    def _on_server_started(self, port):
        self._running = True
        ip = get_local_ip()
        self._info_local.setText(f"Local:  https://localhost:{port}")
        self._info_net.setText(f"Network:  https://{ip}:{port}")
        self._set_status("● ONLINE", C["success"])
        self._start_btn.hide()
        self._stop_btn.setEnabled(True)
        self._stop_btn.show()

        try:
            self._discovery_advertiser = ZeroconfAdvertiser(
                local_ip=ip,
                port=port,
                fingerprint=_cert_fingerprint_sha256(TLS_CERT_FILE),
            )
            self._discovery_advertiser.start()
            self._append_log("📡  mDNS discovery enabled (_droplink._tcp.local)")
        except Exception as e:
            self._append_log(f"⚠  mDNS discovery unavailable: {e}")

        self._append_log(f"🚀  Server started on port {port}")
        self._append_log(f"🔒  HTTPS enabled (self-signed): {TLS_CERT_FILE.resolve()}")
        self._append_log(f"📁  Sync folder: {SYNC_FOLDER.resolve()}")
        self._refresh_server_files()

    def _on_server_failed(self, err):
        self._append_log(f"✗  Server failed to start: {err}")
        QMessageBox.critical(self, "Server Error", f"Could not start server:\n{err}")

    def _on_server_stopped(self):
        self._running = False

        if self._discovery_advertiser:
            self._discovery_advertiser.stop()
            self._discovery_advertiser = None

        self._set_status("● OFFLINE", C["danger"])
        self._set_server_controls(True)
        self._start_btn.setEnabled(True)
        self._start_btn.show()
        self._stop_btn.hide()
        self._info_clients.setText("Clients:  0")
        self._server_thread = None

    def _stop_server(self):
        if not self._server_thread:
            self._on_server_stopped()
            return
        self._stop_btn.setEnabled(False)
        self._set_status("● STOPPING…", C["warn"])
        self._append_log("⏹  Stopping server...")
        self._server_thread.stop()

    def _append_log(self, msg):
        self._log_box.append(
            f'<span style="color:{C["muted"]}">{msg}</span>')
        self._log_box.moveCursor(QTextCursor.End)

    def _update_stats(self):
        if not self._running:
            return
        active = sum(1 for t in _server_state["clients"].values()
                     if time.time()-t < 30)
        self._info_clients.setText(f"Clients:  {active} active")
        cnt = sum(1 for p in SYNC_FOLDER.rglob("*") if p.is_file())
        self._info_files.setText(f"Files:  {cnt}")

    def _refresh_server_files(self):
        files = sorted(
            [{"name": str(p.relative_to(SYNC_FOLDER)),
              "size": p.stat().st_size,
              "modified": p.stat().st_mtime}
             for p in SYNC_FOLDER.rglob("*") if p.is_file()],
            key=lambda f: f["modified"],
            reverse=True,
        )
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
            r = QMessageBox.question(
                self,
                "Go Back",
                "Server is running. Stop server and return to launcher?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if r != QMessageBox.Yes:
                return
            self._stop_server()
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
        self._settings = QSettings("Droplink", "DroplinkApp")
        self._discovery_thread = None
        self._discovered_services = {}
        root = QVBoxLayout(self)
        root.setSpacing(0); root.setContentsMargins(0,0,0,0)

        # Top bar
        bar = QFrame(); bar.setFixedHeight(58)
        bar.setStyleSheet(f"background:{C['panel']};border-bottom:1px solid {C['border']};")
        bl = QHBoxLayout(bar); bl.setContentsMargins(20,0,20,0)
        back = QPushButton("← BACK"); back.setFixedSize(90,32)
        back.setObjectName("btn_subtle")
        back.clicked.connect(self._go_back)
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
        last_server = self._settings.value("client/last_server", "https://localhost:5000")
        self._srv = QLineEdit(str(last_server))
        self._srv.setPlaceholderText("https://192.168.x.x:5000")
        cl.addWidget(self._srv)

        cl.addWidget(label("DISCOVERED SERVERS", f"font-size:10px;color:{C['muted']};letter-spacing:2px;"))
        disc_row = QHBoxLayout(); disc_row.setSpacing(8)
        self._discovered_combo = QComboBox()
        self._discovered_combo.currentIndexChanged.connect(self._on_discovered_selected)
        self._scan_btn = QPushButton("RESCAN")
        self._scan_btn.setObjectName("btn_subtle")
        self._scan_btn.setFixedHeight(34)
        self._scan_btn.clicked.connect(self._restart_discovery)
        disc_row.addWidget(self._discovered_combo)
        disc_row.addWidget(self._scan_btn)
        cl.addLayout(disc_row)

        self._discover_status = label("LAN discovery: idle", f"font-size:10px;color:{C['muted']};")
        cl.addWidget(self._discover_status)

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

    def _start_discovery(self):
        if self._discovery_thread and self._discovery_thread.isRunning():
            return
        self._discover_status.setText("LAN discovery: scanning...")
        self._discovery_thread = DiscoveryBrowserThread()
        self._discovery_thread.service_upsert.connect(self._on_discovered_service)
        self._discovery_thread.service_remove.connect(self._on_removed_service)
        self._discovery_thread.status.connect(self._on_discovery_status)
        self._discovery_thread.finished.connect(self._on_discovery_finished)
        self._discovery_thread.start()

    def _stop_discovery(self):
        if not self._discovery_thread:
            return
        if self._discovery_thread.isRunning():
            self._discovery_thread.stop()
            self._discovery_thread.wait(1200)
        self._discovery_thread = None

    def _restart_discovery(self):
        self._discovered_services.clear()
        self._refresh_discovered_combo()
        self._stop_discovery()
        self._start_discovery()

    def _on_discovery_status(self, message):
        self._discover_status.setText(f"LAN discovery: {message}")

    def _on_discovery_finished(self):
        if not self._discovered_services:
            self._discover_status.setText("LAN discovery: no servers found")

    def _refresh_discovered_combo(self, selected_id=None):
        self._discovered_combo.blockSignals(True)
        current_id = selected_id if selected_id is not None else self._discovered_combo.currentData()
        self._discovered_combo.clear()
        if not self._discovered_services:
            self._discovered_combo.addItem("No LAN servers found", "")
            self._discovered_combo.setEnabled(False)
        else:
            self._discovered_combo.setEnabled(True)
            for service_id in sorted(self._discovered_services.keys()):
                data = self._discovered_services[service_id]
                self._discovered_combo.addItem(data["display"], service_id)
            if current_id:
                idx = self._discovered_combo.findData(current_id)
                self._discovered_combo.setCurrentIndex(idx if idx >= 0 else 0)
            else:
                self._discovered_combo.setCurrentIndex(0)
        self._discovered_combo.blockSignals(False)
        if self._discovered_combo.isEnabled():
            self._on_discovered_selected(self._discovered_combo.currentIndex())

    def _on_discovered_service(self, payload):
        service_id = payload.get("id", "")
        if not service_id:
            return
        self._discovered_services[service_id] = payload
        self._refresh_discovered_combo(selected_id=service_id)
        self._discover_status.setText(
            f"LAN discovery: {len(self._discovered_services)} server(s) found"
        )
        current = self._srv.text().strip()
        if current in ("", "https://localhost:5000"):
            self._srv.setText(payload.get("url", current))

    def _on_removed_service(self, service_id):
        if service_id in self._discovered_services:
            self._discovered_services.pop(service_id, None)
            self._refresh_discovered_combo()
        if self._discovered_services:
            self._discover_status.setText(
                f"LAN discovery: {len(self._discovered_services)} server(s) found"
            )
        else:
            self._discover_status.setText("LAN discovery: no servers found")

    def _on_discovered_selected(self, index):
        if index < 0:
            return
        service_id = self._discovered_combo.itemData(index)
        if not service_id:
            return
        data = self._discovered_services.get(service_id)
        if data and data.get("url"):
            self._srv.setText(data["url"])

    def _do_login(self):
        srv = self._srv.text().strip().rstrip("/")
        srv_lower = srv.lower()
        if srv_lower.startswith("http://"):
            srv = f"https://{srv[7:]}"
            self._srv.setText(srv)
        elif srv and not srv_lower.startswith(("http://", "https://")):
            srv = f"https://{srv}"
            self._srv.setText(srv)
        pw  = self._pw.text()
        if not srv and self._discovered_services:
            first = next(iter(self._discovered_services.values()))
            srv = first.get("url", "")
            self._srv.setText(srv)
        if not srv or not pw:
            self._err.setText("⚠  Fill in all fields"); return
        self._btn.setText("CONNECTING…"); self._btn.setEnabled(False)
        self._err.setText("")
        try:
            r = _api_request("POST", f"{srv}/login", json={"password":pw}, timeout=5)
            if r.status_code == 200:
                self._stop_discovery()
                self._settings.setValue("client/last_server", srv)
                self.login_ok.emit(srv, r.json()["token"])
            elif r.status_code == 403:
                self._err.setText("✗  Invalid password")
            else:
                self._err.setText(f"✗  Login failed (HTTP {r.status_code})")
        except Exception as e:
            self._err.setText(f"✗  Cannot reach server ({e})")
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
        self.files = []
        self._all_files = []
        self._workers = []
        self._fetch_inflight = False
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
        self._refresh_btn = QPushButton("⟳")
        self._refresh_btn.setObjectName("btn_icon")
        self._refresh_btn.setFixedSize(32, 28)
        self._refresh_btn.setToolTip("Refresh now")
        self._refresh_btn.clicked.connect(self._refresh)
        bl.addWidget(self._refresh_btn)
        bl.addSpacing(8)
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
        self._dl_btn = QPushButton("↓ DOWNLOAD")
        self._dl_btn.setObjectName("btn_subtle")
        self._dl_btn.setFixedHeight(36)
        self._dl_btn.clicked.connect(self._download)
        self._prev_btn = QPushButton("◉ PREVIEW")
        self._prev_btn.setObjectName("btn_subtle")
        self._prev_btn.setFixedHeight(36)
        self._prev_btn.clicked.connect(self._preview)
        self._del_btn = QPushButton("✕ DELETE")
        self._del_btn.setObjectName("btn_danger"); self._del_btn.setFixedHeight(36)
        self._del_btn.clicked.connect(self._delete)
        ar.addWidget(self._upload_btn); ar.addWidget(self._dl_btn)
        ar.addWidget(self._prev_btn); ar.addStretch()
        ar.addWidget(self._del_btn)
        ll.addLayout(ar)

        # Filter row
        flt = QHBoxLayout(); flt.setSpacing(8)
        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Filter files by name…")
        self._filter_input.textChanged.connect(self._apply_filter)
        self._clear_filter_btn = QPushButton("CLEAR")
        self._clear_filter_btn.setObjectName("btn_subtle")
        self._clear_filter_btn.setFixedSize(64, 30)
        self._clear_filter_btn.clicked.connect(lambda: self._filter_input.clear())
        flt.addWidget(self._filter_input)
        flt.addWidget(self._clear_filter_btn)
        ll.addLayout(flt)

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
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
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
        self._pop_btn = QPushButton("⤢")
        self._pop_btn.setObjectName("btn_icon")
        self._pop_btn.setFixedSize(28,24)
        self._pop_btn.setToolTip("Open in popup")
        self._pop_btn.clicked.connect(self._popup_preview)
        self._pop_btn.setEnabled(False)
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
        self._set_action_state(False)

    # ── Actions ──
    def _track_worker(self, worker):
        self._workers.append(worker)
        worker.finished.connect(lambda w=worker: self._on_worker_finished(w))

    def _on_worker_finished(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()

    def _set_action_state(self, has_selection):
        self._dl_btn.setEnabled(has_selection)
        self._prev_btn.setEnabled(has_selection)
        self._del_btn.setEnabled(has_selection)

    def _on_selection_changed(self):
        self._set_action_state(self._sel_file() is not None)

    def _refresh(self):
        if self._fetch_inflight:
            return
        self._fetch_inflight = True
        self._refresh_btn.setEnabled(False)
        self._sync_label.setText("⟳ Syncing…")
        w = FileFetchWorker(self.server, self.token)
        w.result.connect(self._populate)
        w.error.connect(self._on_refresh_error)
        w.finished.connect(self._on_refresh_finished)
        self._track_worker(w)
        w.start()

    def _on_refresh_finished(self):
        self._fetch_inflight = False
        self._refresh_btn.setEnabled(True)

    def _on_refresh_error(self, err):
        self._sync_label.setText(f"✗ {err}")

    def _populate(self, files):
        selected_name = self._sel_file()
        self._all_files = sorted(files, key=lambda f: f["modified"], reverse=True)
        self._apply_filter(selected_name=selected_name)
        self._sync_label.setText("✓ Synced")

    def _apply_filter(self, _text=None, selected_name=None):
        query = self._filter_input.text().strip().lower()
        if query:
            self.files = [f for f in self._all_files if query in f["name"].lower()]
        else:
            self.files = list(self._all_files)
        self._render_table(selected_name=selected_name)

    def _render_table(self, selected_name=None):
        t = self._table
        t.setRowCount(len(self.files))
        selected_row = -1
        for i, f in enumerate(self.files):
            ni = QTableWidgetItem(f["name"])
            ni.setForeground(QColor(C["text"]))
            ni.setData(Qt.UserRole, f["name"])

            si = QTableWidgetItem(fmt_size(f["size"]))
            si.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            si.setForeground(QColor(C["muted"]))

            mi = QTableWidgetItem(fmt_time(f["modified"]))
            mi.setTextAlignment(Qt.AlignCenter)
            mi.setForeground(QColor(C["muted"]))

            t.setItem(i, 0, ni)
            t.setItem(i, 1, si)
            t.setItem(i, 2, mi)
            t.setRowHeight(i, 38)
            if selected_name and f["name"] == selected_name:
                selected_row = i

        if selected_row >= 0:
            t.selectRow(selected_row)
        else:
            t.clearSelection()

        shown = len(self.files)
        total_files = len(self._all_files)
        total_size = sum(f["size"] for f in self._all_files)
        if shown == total_files:
            self._stats_label.setText(
                f"{total_files} file{'s' if total_files != 1 else ''}  ·  {fmt_size(total_size)}"
            )
        else:
            self._stats_label.setText(
                f"{shown}/{total_files} shown  ·  {fmt_size(total_size)} total"
            )
        self._on_selection_changed()

    def _sel_file(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _upload(self):
        paths,_ = QFileDialog.getOpenFileNames(self,"Select Files to Upload")
        for p in paths:
            self._do_upload(p)

    def _do_upload(self, path):
        self._prog_label.setText(f"Uploading: {os.path.basename(path)}")
        self._prog_label.show(); self._prog_bar.setValue(0); self._prog_bar.show()
        w = UploadWorker(self.server, self.token, path)
        w.progress.connect(self._prog_bar.setValue)
        w.done.connect(lambda ok,m: self._upload_done(ok,m))
        self._track_worker(w)
        w.start()

    def _upload_done(self, ok, msg):
        self._prog_bar.setValue(100)
        self._prog_label.setText(f"{'✓ Uploaded' if ok else '✗ Upload failed'}: {msg}")
        QTimer.singleShot(2500, self._hide_prog)
        if ok:
            self._refresh()

    def _download(self):
        name = self._sel_file()
        if not name:
            self._stats_label.setText("Select a file to download")
            return
        save,_ = QFileDialog.getSaveFileName(self,"Save As", os.path.basename(name))
        if not save: return
        self._prog_label.setText(f"Downloading: {os.path.basename(name)}")
        self._prog_label.show(); self._prog_bar.setValue(0); self._prog_bar.show()
        w = DownloadWorker(self.server, self.token, name, save)
        w.progress.connect(self._prog_bar.setValue)
        w.done.connect(lambda ok,m: self._dl_done(ok,m))
        self._track_worker(w)
        w.start()

    def _dl_done(self, ok, msg):
        self._prog_bar.setValue(100)
        self._prog_label.setText(f"{'✓ Saved' if ok else '✗ Failed'}: {msg}")
        QTimer.singleShot(3000, self._hide_prog)

    def _preview(self):
        name = self._sel_file()
        if not name:
            self._stats_label.setText("Select a file to preview")
            return
        self._prev_stack.setCurrentIndex(4)  # loading
        self._prev_filename.setText(f"Loading {os.path.basename(name)}…")
        w = PreviewWorker(self.server, self.token, name)
        w.done.connect(lambda data,mime: self._show_inline(name, data, mime))
        w.error.connect(lambda e: self._show_error(e))
        self._track_worker(w)
        w.start()

    def _show_inline(self, name, data, mime):
        self._last_preview = (name, data, mime)
        self._pop_btn.setEnabled(True)
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
        self._last_preview = None
        self._pop_btn.setEnabled(False)
        self._unsup.setText(f"✗ Preview error:\n{msg}")
        self._prev_stack.setCurrentIndex(3)

    def _popup_preview(self):
        if not self._last_preview: return
        dlg = PreviewDialog(*self._last_preview, parent=self)
        dlg.exec_()

    def _delete(self):
        name = self._sel_file()
        if not name:
            self._stats_label.setText("Select a file to delete")
            return
        r = QMessageBox.question(self,"Confirm",f"Delete '{name}' from server?",
            QMessageBox.Yes|QMessageBox.No)
        if r != QMessageBox.Yes: return
        try:
            resp = _api_request("DELETE", f"{self.server}/delete/{name}",
                headers={"X-Auth-Token":self.token}, timeout=5)
            if resp.ok:
                self._refresh()
            else:
                self._stats_label.setText(f"✗ Delete failed (HTTP {resp.status_code})")
        except Exception as e:
            self._stats_label.setText(f"✗ {e}")

    def _hide_prog(self):
        self._prog_bar.hide(); self._prog_label.hide()

    def _disconnect(self):
        self._sync_timer.stop()
        self._last_preview = None
        self._pop_btn.setEnabled(False)
        try: _api_request("POST", f"{self.server}/logout",
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

    def closeEvent(self, event):
        if self._srv_widget._running:
            self._srv_widget._stop_server()
            if self._srv_widget._server_thread:
                self._srv_widget._server_thread.wait(2000)
        super().closeEvent(event)

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
"""
Mini Dropbox - Server
Run this on your host machine: python server.py
"""

import os
import hashlib
import secrets
from pathlib import Path
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from functools import wraps
import time

app = Flask(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
SYNC_FOLDER = Path("synced")
SYNC_FOLDER.mkdir(exist_ok=True)

PASSWORD = "dropbox123"          # Change this!
SECRET_KEY = secrets.token_hex(32)
VALID_TOKENS = {}                # token -> expiry timestamp
TOKEN_TTL = 60 * 60 * 24        # 24 hours

# ── Auth helpers ──────────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

HASHED_PASSWORD = hash_password(PASSWORD)

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Auth-Token")
        if not token or token not in VALID_TOKENS:
            abort(401)
        if time.time() > VALID_TOKENS[token]:
            del VALID_TOKENS[token]
            abort(401)
        return f(*args, **kwargs)
    return decorated

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or hash_password(data.get("password", "")) != HASHED_PASSWORD:
        return jsonify({"error": "Invalid password"}), 403
    token = secrets.token_hex(24)
    VALID_TOKENS[token] = time.time() + TOKEN_TTL
    return jsonify({"token": token})

@app.route("/logout", methods=["POST"])
@require_token
def logout():
    token = request.headers.get("X-Auth-Token")
    VALID_TOKENS.pop(token, None)
    return jsonify({"status": "logged out"})

@app.route("/files", methods=["GET"])
@require_token
def list_files():
    files = []
    for path in SYNC_FOLDER.rglob("*"):
        if path.is_file():
            stat = path.stat()
            rel = path.relative_to(SYNC_FOLDER)
            files.append({
                "name": str(rel),
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
    return jsonify({"files": files})

@app.route("/upload", methods=["POST"])
@require_token
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    sub = request.form.get("path", "")
    filename = secure_filename(f.filename)
    dest_dir = SYNC_FOLDER / sub if sub else SYNC_FOLDER
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    f.save(str(dest))
    return jsonify({"status": "uploaded", "file": filename})

@app.route("/download/<path:filepath>", methods=["GET"])
@require_token
def download(filepath):
    full = SYNC_FOLDER / filepath
    if not full.exists() or not full.is_file():
        abort(404)
    # Security check — prevent path traversal
    try:
        full.resolve().relative_to(SYNC_FOLDER.resolve())
    except ValueError:
        abort(403)
    return send_file(str(full.resolve()), as_attachment=True, download_name=full.name)

@app.route("/delete/<path:filepath>", methods=["DELETE"])
@require_token
def delete_file(filepath):
    full = SYNC_FOLDER / filepath
    if not full.exists():
        abort(404)
    try:
        full.resolve().relative_to(SYNC_FOLDER.resolve())
    except ValueError:
        abort(403)
    full.unlink()
    return jsonify({"status": "deleted"})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "version": "1.0.0"})

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n{'='*50}")
    print(f"  🗂  Mini Dropbox Server")
    print(f"{'='*50}")
    print(f"  Local:    http://localhost:5000")
    print(f"  Network:  http://{local_ip}:5000")
    print(f"  Password: {PASSWORD}")
    print(f"  Folder:   {SYNC_FOLDER.resolve()}")
    print(f"{'='*50}\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
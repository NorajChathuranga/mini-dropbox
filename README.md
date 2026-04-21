# Droplink v2 — Unified Desktop App

One app. Choose your role. Share files over your local network.

---

## 🚀 Install & Run

```bash
pip install -r requirements.txt
python app.py
```

---

## 🖥 Screens

### 1. Launcher
Choose **SERVER** or **CLIENT** mode when the app starts.

### 2. Server Mode
- Set port (default: 5000) and password
- Choose your sync folder (default: `./synced/`)
- Click **START SERVER**
- See live activity log, connected clients count, and file list
- Your LAN IP is shown — share it with clients
- Server runs on **HTTPS** with an auto-generated self-signed certificate

### 3. Client Mode — Login
- Enter the server's IP (shown on the server screen)
- Enter the password
- Click **CONNECT**
- Use `https://` address (example: `https://192.168.x.x:5000`)

### 4. Client Mode — Dashboard
| Feature | How |
|---|---|
| Upload files | Click ↑ UPLOAD |
| Download files | Select a file → ↓ DOWNLOAD |
| Preview (inline) | Select a file → ◉ PREVIEW |
| Preview (popup) | After preview → click ⤢ icon |
| Delete files | Select a file → ✕ DELETE |
| Auto-sync | File list refreshes every 10 seconds |

### Preview support
| File type | Supported |
|---|---|
| Images (PNG, JPG, GIF, BMP, WebP) | ✅ Inline + popup |
| Text, JSON, XML, JS, CSV | ✅ Inline + popup |
| PDF, video, audio, binary | ⚠ Not supported (download to view) |

---

## ⚠️ Notes
- LAN only — do not expose to the internet
- HTTPS is enabled using a self-signed certificate generated on first start
- The certificate/key are stored in `./certs/`
- Passwords are stored as bcrypt hashes in memory (never plaintext)
- The `synced/` folder is created next to `app.py` by default
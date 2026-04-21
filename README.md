# Droplink — Mini Dropbox

A local network file sync app with a desktop GUI. Built with Python, Flask, and PyQt5.

---

## 📁 Project Structure

```
mini-dropbox/
├── server.py         ← Run on your host machine
├── client_gui.py     ← Run on any device on same network
├── requirements.txt
└── synced/           ← Created automatically (shared folder)
```

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Change the password (important!)

Open `server.py` and edit line:
```python
PASSWORD = "dropbox123"   # ← change this
```

---

## 🚀 Run

### On the host machine (server):
```bash
python server.py
```
It will print your local IP, e.g.:
```
  Local:    http://localhost:5000
  Network:  http://192.168.1.10:5000
```

### On any device on the same WiFi (client):
```bash
python client_gui.py
```
- Enter the server IP shown above
- Enter the password
- Click **CONNECT**

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 Password protection | Token-based auth, 24hr session |
| ↑ Upload | Single or multiple files with progress bar |
| ↓ Download | Save files to local machine with progress bar |
| 🗑 Delete | Remove files from server |
| 🔄 Auto-sync | File list refreshes every 10 seconds |
| 🌐 LAN access | Any device on same WiFi can connect |

---

## ⚠️ Notes

- Only use on **trusted local networks** — no HTTPS
- Do **not** expose to the internet
- The `synced/` folder is created next to `server.py`
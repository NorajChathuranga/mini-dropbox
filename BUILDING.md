# Building executable files on Windows, Linux, and macOS

If you only have a Windows PC, you can still produce Linux and macOS binaries by using GitHub Actions.

## 1) Build locally on Windows (optional)

```bash
pip install -r requirements.txt
pip install "pyinstaller>=6.10,<7"
python -m py_compile app.py
python -c "import app; print('Import check: OK')"
pyinstaller --clean --noconfirm app.spec
```

Your local executable will be in `dist/` (`app.exe` on Windows).

To run it locally:

```bash
./dist/app
```

On Windows PowerShell:

```powershell
.\dist\app.exe
```

## 2) Build all OS binaries in GitHub Actions

This repository now includes `.github/workflows/build-binaries.yml`.

### What it does
- Runs on `ubuntu-latest`, `windows-latest`, and `macos-latest`.
- Installs app dependencies and a pinned PyInstaller major range.
- Installs Linux GUI runtime libraries on Ubuntu runner.
- Runs sanity checks before packaging:
  - `python -m py_compile app.py`
  - `python -c "import app"`
- Builds a single-file executable from `app.spec`.
- Verifies output file exists before upload.
- Uploads each executable as a workflow artifact:
  - `droplink-linux`
  - `droplink-windows`
  - `droplink-macos`

### How to use it
1. Push your code to GitHub.
2. Open the **Actions** tab in your repository.
3. Run **Build Desktop Binaries** manually (or let it run automatically on push/PR).
4. Open the workflow run and download artifacts.

## 3) Notes
- Keep `app.spec` in sync with imports and packaging needs; CI uses it directly.
- macOS builds require Apple Silicon/Intel compatibility decisions for distribution outside your own use.
- Windows/macOS may show warnings for unsigned binaries.
- Cross-compiling GUI Python apps is less reliable than native-per-OS builds; this workflow uses native cloud runners for each OS.

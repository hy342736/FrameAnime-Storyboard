from pathlib import Path
import os

from PyInstaller.utils.hooks import collect_all, collect_submodules


root = Path(SPECPATH)
browser_root = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", root / ".build-browsers"))
if not browser_root.is_dir():
    raise SystemExit(f"Playwright Chromium not found: {browser_root}")

playwright_datas, playwright_binaries, playwright_hidden = collect_all("playwright")
ffmpeg_datas, ffmpeg_binaries, ffmpeg_hidden = collect_all("imageio_ffmpeg")
datas = playwright_datas + ffmpeg_datas + [
    (str(root / "web"), "web"),
    (str(root / "assets"), "assets"),
    (str(browser_root), "ms-playwright"),
]
hiddenimports = list(dict.fromkeys(
    playwright_hidden
    + collect_submodules("uvicorn")
    + collect_submodules("webview")
))
icon_path = root / "assets" / "app.ico"

a = Analysis(
    [str(root / "desktop_launcher.py")],
    pathex=[str(root)],
    binaries=playwright_binaries + ffmpeg_binaries,
    datas=datas,
    hiddenimports=list(dict.fromkeys(hiddenimports + ffmpeg_hidden)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FrameAnimeDesk",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.is_file() else None,
)

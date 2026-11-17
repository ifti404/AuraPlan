# PyInstaller build definition. Build on Windows with Python 3.12 x64.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

project = Path(SPECPATH)
datas = [
    (str(project / "app" / "backend" / "schema.sql"), "app/backend"),
    (str(project / "app" / "assets" / "icons"), "app/assets/icons"),
]
datas += collect_data_files("customtkinter")
binaries = collect_dynamic_libs("vosk")
hiddenimports = (
    collect_submodules("customtkinter")
    + collect_submodules("vosk")
    + ["_cffi_backend", "pyaudio", "sounddevice"]
)

a = Analysis(
    [str(project / "main.py")],
    pathex=[
        str(project),
        str(project / "app" / "ui"),
        str(project / "app" / "backend"),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AuraPlan",
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
    icon=str(project / "app" / "assets" / "icons" / "auraplan.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AuraPlan",
)

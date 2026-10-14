# PyInstaller spec for the agentstack native bootstrapper (onefile, console).
# Build from the repo root:  pyinstaller installer/agentstack-setup.spec
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("wizard")

a = Analysis(
    ["bootstrap.py"],
    pathex=[".."],  # repo root, so the bundled `wizard` package is importable
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "test"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="agentstack-setup",
    console=True,
    disable_windowed_traceback=False,
    strip=False,
    upx=False,
)

import os
import platform
import tomllib

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_submodules

with open("pyproject.toml", "rb") as f:
    app_name = tomllib.load(f)["project"]["name"]
build_os = os.environ.get("BUILD_OS", platform.system().lower())
build_arch = os.environ.get("BUILD_ARCH", platform.machine())

name = f"{app_name}-{build_os}-{build_arch}"
datas = [("src/staticgallerybuilder/files", "files"), ("src/staticgallerybuilder/templates", "templates"), ("themes", "themes")]
hiddenimports = collect_submodules("modules")

a = Analysis(
    ["src/staticgallerybuilder/main.py"],
    pathex=[],
    binaries=[],
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
    a.binaries,
    a.datas,
    [],
    name=name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

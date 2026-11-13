# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for DaycoNetCollector.
# Bundles pydivert native binaries (WinDivert.dll, WinDivert64.sys) and psycopg binary.

from PyInstaller.utils.hooks import collect_all

pydivert_datas, pydivert_binaries, pydivert_hidden = collect_all("pydivert")
psycopg_datas, psycopg_binaries, psycopg_hidden = collect_all("psycopg_binary")
psycopg_pool_datas, psycopg_pool_binaries, psycopg_pool_hidden = collect_all("psycopg_pool")
psycopg_datas2, psycopg_binaries2, psycopg_hidden2 = collect_all("psycopg")

datas = pydivert_datas + psycopg_datas + psycopg_pool_datas + psycopg_datas2
binaries = pydivert_binaries + psycopg_binaries + psycopg_pool_binaries + psycopg_binaries2
hiddenimports = pydivert_hidden + psycopg_hidden + psycopg_pool_hidden + psycopg_hidden2 + [
    "config",
    "db",
    "psutil",
]

a = Analysis(
    ["service.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["bridge"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DaycoNetCollector",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

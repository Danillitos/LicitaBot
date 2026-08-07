# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

uc_datas, uc_binaries, uc_hiddenimports = collect_all('undetected_chromedriver')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=uc_binaries,
    datas=[('assets', 'assets'), ('logic', 'logic'), ('ui', 'ui')] + uc_datas,
    hiddenimports=['main'] + uc_hiddenimports,
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
    name='LicitaBot',
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

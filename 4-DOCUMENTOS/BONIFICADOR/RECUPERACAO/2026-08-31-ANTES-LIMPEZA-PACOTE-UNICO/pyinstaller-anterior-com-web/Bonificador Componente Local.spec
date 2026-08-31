# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/Luis Fernando/Downloads/ClubEFootball--main/ClubEFootball--main/2-MOTORES/BONIFICADOR/interface/servidor.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/Luis Fernando/Downloads/ClubEFootball--main/ClubEFootball--main/2-MOTORES/BONIFICADOR/motor_bonus.py', '.'), ('C:/Users/Luis Fernando/Downloads/ClubEFootball--main/ClubEFootball--main/2-MOTORES/BONIFICADOR/interface', 'interface')],
    hiddenimports=[],
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
    name='Bonificador Componente Local',
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

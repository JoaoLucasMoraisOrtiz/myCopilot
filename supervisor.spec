# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_submodules

# Caminho para o script principal
script_path = os.path.join(os.path.dirname(SPEC), 'scripts', 'supervisor_server.py')

src_path = os.path.join(os.path.dirname(SPEC), 'src')

codingos_hidden = collect_submodules('codingos')

a = Analysis(
    [script_path],
    pathex=[src_path],
    binaries=[],
    datas=[],
    hiddenimports=list(set([
        *codingos_hidden,
        'mcp.server.fastmcp',
        'mcp.server.models',
        'mcp.server.session',
        'mcp.server.stdio',
        'mcp.types',
    ])),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='supervisor',
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
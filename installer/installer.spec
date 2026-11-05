# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for WordMaster Setup installer."""

import sys
import os
from pathlib import Path

_block_cipher = None

ROOT = Path(SPECPATH)
import shutil, tempfile, hashlib, json, atexit
PROJECT = ROOT.parent
release_dist = Path(os.environ.get('WORDMASTER_RELEASE_DIST', PROJECT / 'dist')).resolve()
MAIN_EXE = release_dist / 'WordMaster.exe'
metadata = json.loads((release_dist / 'WordMaster.build.json').read_text(encoding='utf-8'))
if hashlib.sha256(MAIN_EXE.read_bytes()).hexdigest() != metadata['exe_sha256']:
    raise RuntimeError('EXE checksum mismatch; rebuild WordMaster first')
sys.path.insert(0, str(PROJECT / 'server'))
from frontend_assets import FrontendBundle
if FrontendBundle(PROJECT / 'web/dist').build_id != metadata['build_id']:
    raise RuntimeError('EXE uses an old frontend; rebuild WordMaster first')
# Fresh staging eliminates silently reused executable/resources from bundle/.
(ROOT / 'build').mkdir(exist_ok=True)
bundle_owner = tempfile.TemporaryDirectory(prefix='bundle-', dir=ROOT / 'build')
atexit.register(bundle_owner.cleanup)
BUNDLE = Path(bundle_owner.name)
shutil.copy2(MAIN_EXE, BUNDLE / 'WordMaster.exe')
shutil.copy2(release_dist / 'WordMaster.build.json', BUNDLE / 'WordMaster.build.json')
UNINSTALL = ROOT / 'dist/uninstall.exe'
if not UNINSTALL.is_file():
    raise RuntimeError('Build uninstall.spec before installer.spec')
shutil.copy2(UNINSTALL, BUNDLE / 'uninstall.exe')
RESOURCES = PROJECT / 'resources'
shutil.copytree(RESOURCES, BUNDLE, dirs_exist_ok=True)

# ── Collect installer data files ──
installer_datas = []
for f in BUNDLE.rglob('*'):
    if f.is_file():
        installer_datas.append((str(f), str(Path('bundle') / f.relative_to(BUNDLE).parent)))
installer_datas.extend([
    (str(ROOT / 'installer_assets/welcome_logo.png'), 'installer_assets'),
    (str(ROOT / 'installer_assets/window_icon.png'), 'installer_assets'),
    (str(PROJECT / 'resources/icon.ico'), 'installer_assets'),
    (str(PROJECT / 'license_agreement.txt'), '.'),
])

a = Analysis(
    [str(ROOT / 'installer.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=installer_datas,
    hiddenimports=['tkinter', 'json', 'shutil', 'subprocess',
                   'win32com', 'win32com.client', 'pythoncom', 'pywintypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=_block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=_block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WordMaster_Setup',
    icon=str(PROJECT / 'resources/icon.ico'),
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
bundle_owner.cleanup()

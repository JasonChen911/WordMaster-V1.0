# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for WordMaster Desktop.
Builds a standalone Windows .exe that:
- Uses PyWebView for native Windows window
- Includes FastAPI backend (server/)
- Includes React frontend (web/dist/)
- Includes word bank data (data/vocabulary/)
- Includes resources (icon, license)
- Auto-initializes AppData at runtime
"""

import sys
from pathlib import Path

_block_cipher = None

ROOT = Path(SPECPATH)
SERVER = ROOT / 'server'
WEB_DIST = ROOT / 'web' / 'dist'
RESOURCES = ROOT / 'resources'

# ── Collect frontend dist files → web/ ──
frontend_datas = []
if WEB_DIST.exists():
    for f in WEB_DIST.rglob('*'):
        if f.is_file():
            frontend_datas.append(
                (str(f), str(Path('web') / f.relative_to(WEB_DIST).parent))
            )

# ── Collect server Python files → server/ ──
server_datas = []
for f in SERVER.glob('*.py'):
    server_datas.append((str(f), 'server'))

# ── Pre-initialized seed database → server/ (fast first launch) ──
seed_db = SERVER / 'wordmaster_seed.db'
if seed_db.exists():
    server_datas.append((str(seed_db), 'server'))

# ── Collect built-in word bank TXT files → 内置词库请勿删除/ ──
vocab_datas = []
VOCAB_DIR = ROOT / '内置词库请勿删除'
if VOCAB_DIR.exists():
    for f in VOCAB_DIR.glob('*.txt'):
        vocab_datas.append((str(f), '内置词库请勿删除'))

# ── Collect resources → resources/ (recursively, for illustrations etc.) ──
resource_datas = []
if RESOURCES.exists():
    for f in RESOURCES.rglob('*'):
        if f.is_file():
            resource_datas.append(
                (str(f), str(Path('resources') / f.relative_to(RESOURCES).parent))
            )

# ── Root-level files ──
root_datas = []
for filename in ['version_info.txt', '.env.example']:
    path = ROOT / filename
    if path.exists():
        root_datas.append((str(path), '.'))

# ── Icon (from resources/) ──
icon_path = RESOURCES / 'icon.ico'
if icon_path.exists():
    root_datas.append((str(icon_path), '.'))

# ── Merge, deduplicate ──
all_datas = frontend_datas + server_datas + vocab_datas + resource_datas + root_datas
seen = set()
unique_datas = []
for src, dest in all_datas:
    if (src, dest) not in seen:
        seen.add((src, dest))
        unique_datas.append((src, dest))

version_path = ROOT / 'version_info.txt'

# ═══════════════════════════════════════════════════════════════════
a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT), str(SERVER)],
    binaries=[],
    datas=unique_datas,
    hiddenimports=[
        # Uvicorn / FastAPI internals
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols.http.auto',
        'sqlalchemy.sql.default_comparator',
        'pydantic',
        'dotenv',
        'httpx',
        # WebView
        'webview',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'clr',
        # Keyring (Windows Credential Manager)
        'keyring',
        'keyring.backends.Windows',
        # Edge TTS
        'edge_tts',
        'edge_tts.communicate',
        'aiohttp',
        # FSRS adaptive review
        'fsrs',
        # Server modules
        'app',
        'srs',
        'srs.engine',
        # AI Gateway + services
        'ai',
        'ai.gateway',
        'ai.schemas',
        'ai.providers',
        'ai.providers.deepseek',
        'ai.services',
        'ai.services.material_service',
        'ai.services.analysis_service',
        'ai.services.exercise_service',
        'ai.services.example_service',
        'config_manager',
        'database',
        'models',
        'schemas',
        'seed',
        'confusion_seed',
        'teacher_seed',
        'study_summary',
        'mistakes',
        'ai_service',
        'audio_service',
        'logging_config',
        'mdx_reader',
        'core',
        'db_init',
        # Router modules
        'routers',
        'routers.words',
        'routers.stats',
        'routers.ai',
        'routers.books',
        'routers.dictionary',
        'routers.search',
        'routers.audio',
        'routers.games',
        'routers.media',
        'routers.material',
        'routers.insights',
        'routers.reading',
        'routers.teacher',
        'routers.mistakes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'gtk',
        'curses',
    ],
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
    name='WordMaster',
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
    icon=str(icon_path) if icon_path else None,
    version=str(version_path) if version_path.exists() else None,
)

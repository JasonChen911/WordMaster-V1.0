"""Validated, immutable per-process frontend; never serve a half-published build."""
import hashlib
import json
import logging
import mimetypes
import os
import re
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

APP_VERSION = '0.1.0'
NO_CACHE = 'no-cache, no-store, must-revalidate'
BUILD_RE = re.compile(r'<meta\s+name="wordmaster-build"\s+content="([A-Za-z0-9_-]+)"')


def frontend_log(event, **fields):
    logger = logging.getLogger('wordmaster.frontend')
    if not logger.handlers:
        root = Path(os.getenv('WORDMASTER_DATA_DIR') or (Path(os.getenv('APPDATA', Path.home())) / 'WordMaster'))
        (root / 'logs').mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(root / 'logs/frontend.log', maxBytes=2_000_000, backupCount=2, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    logger.info('%s %s', event, json.dumps(fields, ensure_ascii=False))


def frontend_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'web'
    return Path(__file__).resolve().parents[1] / 'web/dist'


class FrontendBundle:
    def __init__(self, root):
        self.root = Path(root).resolve()
        try:
            index = (self.root / 'index.html').read_bytes()
            match = BUILD_RE.search(index.decode('utf-8'))
            if not match:
                raise RuntimeError('index.html lacks build ID; run npm run build')
            self.build_id = match[1]
            manifest = json.loads((self.root / f'build-{self.build_id}.json').read_text(encoding='utf-8'))
            if manifest['build_id'] != self.build_id or hashlib.sha256(index).hexdigest() != manifest['index_sha256']:
                raise RuntimeError('index.html/build manifest mismatch')
            self.files = {'index.html': index}
            for name, digest in manifest['files'].items():
                path = (self.root / name).resolve()
                if not path.is_relative_to(self.root):
                    raise RuntimeError('invalid frontend asset path')
                if not path.is_file():
                    raise RuntimeError(f'missing asset: {name}')
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != digest:
                    raise RuntimeError(f'corrupt asset: {name}')
                self.files[name] = data
            if not any(name.startswith('assets/') and name.endswith('.js') for name in self.files):
                raise RuntimeError('assets directory has no JavaScript')
            # Manifest cannot omit an import while leaving the main file valid.
            for name, data in self.files.items():
                if name.endswith(('.html', '.js', '.css')):
                    for ref in re.findall(r'''["']((?:/assets/|\./)[A-Za-z0-9_./-]+\.(?:js|css))["']''', data.decode('utf-8')):
                        target = ref.lstrip('/') if ref.startswith('/') else (Path(name).parent / ref).as_posix()
                        if target not in self.files:
                            raise RuntimeError(f'missing asset dependency: {target}')
        except (OSError, KeyError, ValueError) as exc:
            raise RuntimeError(f'Invalid frontend at {self.root}: {exc}') from exc


def mount_frontend(app, bundle):
    from fastapi import Request
    from fastapi.responses import Response, JSONResponse

    @app.get('/{full_path:path}')
    async def serve_frontend(full_path: str, request: Request):
        key = full_path or 'index.html'
        public_key = f'builds/{bundle.build_id}/{key}'
        if key not in bundle.files and public_key in bundle.files:
            key = public_key
        if key not in bundle.files:
            if key.startswith(('assets/', 'api/', 'src/')) or Path(key).suffix:
                # Only log an asset filename, never a route/query/user input.
                asset = Path(key).name
                if re.fullmatch(r'[A-Za-z0-9_-]+\.(js|css)', asset):
                    frontend_log('missing_asset', build=bundle.build_id, asset=asset)
                return JSONResponse({'detail': 'Not Found'}, status_code=404, headers={'Cache-Control': NO_CACHE})
            key = 'index.html'
        mime = {'js': 'text/javascript', 'css': 'text/css', 'html': 'text/html'}.get(key.rsplit('.', 1)[-1]) or mimetypes.guess_type(key)[0] or 'application/octet-stream'
        hashed = key.startswith('assets/') and key.endswith(('.js', '.css', '.woff', '.woff2'))
        return Response(bundle.files[key], media_type=mime, headers={
            'Cache-Control': 'public, max-age=31536000, immutable' if hashed else NO_CACHE,
            'X-Frontend-Build': bundle.build_id,
            'X-Content-Type-Options': 'nosniff',
        })

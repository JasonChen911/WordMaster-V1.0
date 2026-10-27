"""WordMaster FastAPI application entry point.

Responsibilities (kept deliberately narrow):
- FastAPI app creation + CORS middleware
- Environment loading, logging, and path resolution
- Database initialisation (``db_init.init_db()``) + startup log
- Router registration (business APIs live in ``routers/``)
- Static frontend serving + SPA fallback
- The ``start_server`` entry point used by ``main.py``
"""

import sys
import os
import logging
import webbrowser
import uuid
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal
from frontend_assets import FrontendBundle, frontend_path, mount_frontend, frontend_log, APP_VERSION, NO_CACHE
from fastapi.middleware.cors import CORSMiddleware

from database import DATA_DIR
from logging_config import setup_logging, startup_log
from db_init import init_db
from routers import words, stats, ai, books, dictionary, search, audio, games, media, material, insights, reading, teacher, mistakes

# ─── Load environment ───────────────────────────────────────────
load_dotenv()

# ─── Logging ────────────────────────────────────────────────────
log_dir = DATA_DIR / "logs" if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent / "logs"  # server/logs/
setup_logging(log_dir)
logger = logging.getLogger(__name__)

# ─── Paths ──────────────────────────────────────────────────────
BASE_DIR = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
FRONTEND_DIR = frontend_path()
# A running server owns one verified generation, even during a development build.
frontend = FrontendBundle(FRONTEND_DIR)
frontend_log('frontend_validated', version=APP_VERSION, build=frontend.build_id,
             dist=str(FRONTEND_DIR), static=str(FRONTEND_DIR / 'assets'))

logger.info(f"BASE_DIR={BASE_DIR}, FRONTEND_DIR={FRONTEND_DIR}, DATA_DIR={DATA_DIR}")

# ─── FastAPI App ────────────────────────────────────────────────
app = FastAPI(
    title="WordMaster API",
    description="AI-powered English vocabulary learning assistant",
    version="0.1.0",
)

app.state.instance_id = uuid.uuid4().hex
app.state.frontend = frontend

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Database Init ──────────────────────────────────────────────
init_db()
startup_log(f"database initialized: migrations + built-in word books (DATA_DIR={DATA_DIR})")


@app.get("/health")
def health():
    """Lightweight readiness probe — no expensive work.

    Only reachable once uvicorn is serving, which happens after init_db()
    has completed migrations and loaded built-in word books. The desktop
    launcher polls this endpoint to decide when the backend is ready.
    """
    from fastapi.responses import JSONResponse
    return JSONResponse({"status": "ok", "application": "WordMaster", "version": APP_VERSION,
            "instance_id": app.state.instance_id, "frontend_build": frontend.build_id}, headers={"Cache-Control": NO_CACHE})


# ─── Router registration ────────────────────────────────────────
app.include_router(words.router)
app.include_router(stats.router)
app.include_router(ai.router)
app.include_router(books.router)
app.include_router(dictionary.router)
app.include_router(search.router)
app.include_router(audio.router)
app.include_router(games.router)
app.include_router(media.router)
app.include_router(material.router)
app.include_router(insights.router)
app.include_router(reading.router)
app.include_router(teacher.router)
app.include_router(mistakes.router)


# ─── Frontend diagnostics (allowlisted, no business content) ──────
class FrontendEvent(BaseModel):
    event: Literal['dynamic_import', 'auto_reload', 'recovery_failed', 'entry_load_failed']
    build: str = Field(default='', max_length=100)
    asset: str = Field(default='', max_length=160)


@app.get('/api/frontend/status')
def frontend_status():
    from fastapi.responses import JSONResponse
    return JSONResponse({'build_id': frontend.build_id, 'version': APP_VERSION}, headers={'Cache-Control': NO_CACHE})


@app.post('/api/frontend/log')
def log_frontend_event(event: FrontendEvent):
    # Never persist arbitrary error messages, stack traces, URLs or query strings.
    build = event.build if re.fullmatch(r'[A-Za-z0-9_-]{1,100}', event.build) else 'unknown'
    asset = event.asset if re.fullmatch(r'[A-Za-z0-9_-]+\.(js|css)', event.asset) else ''
    frontend_log(event.event, build=build, asset=asset)
    return {'ok': True}


mount_frontend(app, frontend)


# ─── Entry Point ────────────────────────────────────────────────

def start_server(host=None, port=None, open_browser=False):
    import uvicorn

    host = host or os.getenv("HOST", "0.0.0.0")
    port = port or int(os.getenv("PORT", "8000"))

    logger.info(f"Starting WordMaster on http://{host}:{port}")

    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="info"))
    if open_browser:
        import threading, time
        def show_when_ready():
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline and not server.should_exit:
                if server.started:
                    webbrowser.open(f"http://127.0.0.1:{port}/?wm-build={frontend.build_id}")
                    return
                time.sleep(.1)
        threading.Thread(target=show_when_ready, daemon=True).start()
    frontend_log('http_server_starting', port=port, build=frontend.build_id)
    try:
        server.run()
    finally:
        frontend_log('http_server_stopped', port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WordMaster Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--browser", action="store_true", help="Open browser on startup")
    args = parser.parse_args()
    start_server(args.host, args.port, args.browser)

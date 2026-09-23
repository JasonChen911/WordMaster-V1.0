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
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    FRONTEND_DIR = BASE_DIR / "web"
else:
    BASE_DIR = Path(__file__).resolve().parent  # server/
    PROJECT_DIR = BASE_DIR.parent  # WordMaster/
    FRONTEND_DIR = PROJECT_DIR / "web" / "dist"
    # Fallback: if dist not built yet, try serving from web/ directly
    if not (FRONTEND_DIR / "index.html").exists():
        FRONTEND_DIR = PROJECT_DIR / "web"

logger.info(f"BASE_DIR={BASE_DIR}, FRONTEND_DIR={FRONTEND_DIR}, DATA_DIR={DATA_DIR}")

# ─── FastAPI App ────────────────────────────────────────────────
app = FastAPI(
    title="WordMaster API",
    description="AI-powered English vocabulary learning assistant",
    version="0.1.0",
)

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
    return {"status": "ok"}


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


# ─── Serve Frontend Static Files ────────────────────────────────

if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "message": "WordMaster API is running",
            "docs": "/docs",
            "frontend": "Run: cd web && npm run build",
        }


# ─── Entry Point ────────────────────────────────────────────────

def start_server(host=None, port=None, open_browser=False):
    import uvicorn

    host = host or os.getenv("HOST", "0.0.0.0")
    port = port or int(os.getenv("PORT", "8000"))

    logger.info(f"Starting WordMaster on http://{host}:{port}")

    if open_browser:
        webbrowser.open(f"http://localhost:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WordMaster Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--browser", action="store_true", help="Open browser on startup")
    args = parser.parse_args()
    start_server(args.host, args.port, args.browser)

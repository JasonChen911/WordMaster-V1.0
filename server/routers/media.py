"""Media routes: illustration images."""

import sys
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response as FastAPIResponse

router = APIRouter()

BASE_DIR = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent

ILLUSTRATIONS_DIR = (
    BASE_DIR / "resources" / "illustrations"
    if getattr(sys, "frozen", False)
    else PROJECT_DIR / "resources" / "illustrations"
)


@router.get("/api/illustrations/{filename}")
def get_illustration(filename: str):
    """Serve an illustration image. Returns default placeholder if not found."""
    # Sanitize filename to prevent path traversal
    safe_name = Path(filename).name
    file_path = ILLUSTRATIONS_DIR / safe_name

    if not file_path.exists():
        file_path = ILLUSTRATIONS_DIR / "default.svg"

    if not file_path.exists():
        # Ultimate fallback: return a tiny inline SVG
        return FastAPIResponse(
            content='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160"><rect width="240" height="160" rx="16" fill="#1c1c1e"/><text x="120" y="85" text-anchor="middle" fill="#636366" font-size="10">No Image</text></svg>',
            media_type="image/svg+xml",
        )

    media_type = "image/svg+xml" if file_path.suffix == ".svg" else "image/png"
    return FileResponse(str(file_path), media_type=media_type)

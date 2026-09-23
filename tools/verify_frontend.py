"""Verify the built frontend (web/dist) is internally consistent.

Catches "old hash pollution" — the failure mode where index.html / the main JS
bundle reference a chunk hash that isn't present on disk (HTML from build A,
assets from build B). Parses index.html and recursively resolves every dynamic
import() across the JS chunks, then confirms each referenced asset exists.

Run:  python tools/verify_frontend.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE.parent / "web" / "dist"

# Files referenced with an absolute /assets/... or /name.ext URL from HTML.
HTML_ASSET_RE = re.compile(r'(?:src|href)="(/[A-Za-z0-9._/-]+\.(?:js|css|png|jpe?g|svg|ico|woff2?|ttf))"')
# Static or dynamic import("...") / import "..." of a relative module path.
JS_IMPORT_RE = re.compile(r'import\s*\(?\s*"(\./[A-Za-z0-9._/-]+\.(?:js|css))"\s*\)?')

MISSING = []


def check(path_rel: str, kind: str):
    """Verify a dist-relative path exists; record if not."""
    p = DIST / path_rel
    if not p.exists():
        MISSING.append(f"{kind}: {path_rel}")
        return False
    return True


def resolve_js_deps(js_rel: str, seen: set):
    """Recursively collect ./... imports reachable from a JS chunk."""
    js_rel = js_rel.lstrip("/")
    if js_rel in seen:
        return
    seen.add(js_rel)
    p = DIST / js_rel
    if not p.exists():
        MISSING.append(f"chunk: {js_rel}")
        return
    content = p.read_text(encoding="utf-8", errors="ignore")
    base = Path(js_rel).parent
    for m in JS_IMPORT_RE.findall(content):
        # m e.g. "./Games-BIvwo6ei.js" — resolve relative to this chunk's dir.
        resolved = (base / m).as_posix()
        if not check(resolved, "import"):
            continue
        resolve_js_deps(resolved, seen)


def main():
    index = DIST / "index.html"
    if not index.exists():
        print("FAIL: web/dist/index.html missing — run `npm run build` first")
        return 1

    html = index.read_text(encoding="utf-8")

    # 1. Assets referenced directly by index.html.
    html_refs = set()
    for m in HTML_ASSET_RE.findall(html):
        if m.startswith("/assets/"):
            html_refs.add(m)
        else:
            # root-level public asset e.g. /wordmaster-logo.png
            html_refs.add(m)
    for ref in sorted(html_refs):
        check(ref.lstrip("/"), "index.html")

    # 2. Main JS bundles and their transitive dynamic imports.
    main_bundles = {m for m in html_refs if m.endswith(".js")}
    seen = set()
    for bundle in main_bundles:
        resolve_js_deps(bundle, seen)

    # 3. Explicit Games chunk check (the reported production bug).
    games_refs = sorted({r for r in seen if "Games" in r})
    games_on_disk = sorted(p.name for p in (DIST / "assets").glob("Games-*.js")) if (DIST / "assets").exists() else []

    print(f"index.html asset refs : {len(html_refs)}")
    print(f"JS chunks reached      : {len(seen)}")
    print(f"Games referenced       : {games_refs}")
    print(f"Games on disk          : {games_on_disk}")

    if MISSING:
        print("FAIL — referenced assets missing (hash pollution):")
        for m in MISSING:
            print(f"  - {m}")
        return 1

    if not games_refs or not games_on_disk:
        print("FAIL — Games chunk missing from references or disk")
        return 1

    print("OK — all referenced frontend assets are present (no hash pollution)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

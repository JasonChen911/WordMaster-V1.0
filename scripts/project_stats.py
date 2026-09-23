"""Reproducible WordMaster project-fact generator.

Produces the single source of truth for every number quoted in contest
materials. It scans the real source tree (not hand-written values) and writes
``docs/PROJECT_FACTS.md``.

Counting conventions (documented so results stay reproducible):
- API routes: ``@app.<method>`` / ``@router.<method>`` decorators in source.
  ``/health`` is counted separately from the 47 ``/api/*`` routes.
- Database tables: SQLite tables excluding the internal ``sqlite_sequence``.
  ``schema_version`` is reported as a migration-tracking table, not a
  business table.
- Frontend: "一级用户页面" = primary functional pages (routes excluding the
  ``/settings/ai`` sub-page and the ``/agreement`` / ``/about`` info pages).
  "页面组件" = every file in ``web/src/pages/``.
- Code lines: physical lines (``\n`` count) per file, excluding
  ``__pycache__``, ``_archived``, ``node_modules``, ``.venv``, ``dist``,
  ``build``.

Run:  python scripts/project_stats.py
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "server"
WEB_SRC = ROOT / "web" / "src"
PAGES = WEB_SRC / "pages"
TESTS = ROOT / "tests"
SCRIPTS = ROOT / "scripts"
INSTALLER = ROOT.parent / "installer"

ROUTE_RE = re.compile(r"@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*\"([^\"]+)\"")


def _count_lines(paths):
    """Sum physical lines across an iterable of Paths."""
    total = 0
    n = 0
    for p in paths:
        if not p.is_file():
            continue
        try:
            total += sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
            n += 1
        except OSError:
            continue
    return n, total


def _py_files(directory, exclude=("__pycache__", "_archived")):
    out = []
    for p in sorted(directory.rglob("*.py")):
        if any(part in exclude for part in p.parts):
            continue
        out.append(p)
    return out


# ── A. FastAPI routes ──────────────────────────────────────────
def collect_routes():
    api_total = 0
    health = 0
    static = 0
    per_module = {}
    # routers/
    routers_dir = SERVER / "routers"
    for p in sorted(routers_dir.glob("*.py")):
        if p.name == "__init__.py":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        routes = ROUTE_RE.findall(text)
        n = len(routes)
        per_module[f"routers/{p.name}"] = n
        api_total += n
    # app.py (health + static/SPA fallbacks)
    app_text = (SERVER / "app.py").read_text(encoding="utf-8", errors="ignore")
    app_routes = ROUTE_RE.findall(app_text)
    for _method, path in app_routes:
        if path == "/health":
            health += 1
        elif path.startswith("/api/"):
            api_total += 1
        else:
            static += 1
    return api_total, health, static, per_module


# ── B. SQLite tables ───────────────────────────────────────────
def collect_tables():
    import sqlite3
    db_path = SERVER / "wordmaster.db"
    if not db_path.exists():
        return None, []
    db = sqlite3.connect(str(db_path))
    try:
        tables = sorted(
            r[0] for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        )
    finally:
        db.close()
    business = [t for t in tables if t != "sqlite_sequence"]
    return business, [t for t in business if t != "schema_version"]


# ── C. Frontend pages ──────────────────────────────────────────
def collect_pages():
    app_jsx = (WEB_SRC / "App.jsx").read_text(encoding="utf-8", errors="ignore")
    routes = re.findall(r'path="([^"]+)"\s+element=\{<(\w+)', app_jsx)
    page_files = sorted(p.name for p in PAGES.glob("*.jsx"))
    secondary = {"/settings/ai", "/agreement", "/about"}
    primary = [r for r in routes if r[0] not in secondary]
    return page_files, primary, routes


# ── D. Code lines ──────────────────────────────────────────────
def collect_code():
    server_py = _py_files(SERVER)
    _, server_lines = _count_lines(server_py)
    root_py = [ROOT / "main.py", ROOT / "convert_wordbanks.py", ROOT / "generate_examples.py"]
    _, root_lines = _count_lines(root_py)
    test_py = _py_files(TESTS, exclude=("__pycache__",))
    test_n, test_lines = _count_lines(test_py)
    script_py = _py_files(SCRIPTS, exclude=("__pycache__",))
    _, script_lines = _count_lines(script_py)
    installer_py = _py_files(INSTALLER, exclude=("__pycache__", "build", "dist", "bundle", "test_uninstall"))
    _, installer_lines = _count_lines(installer_py)

    js_files = sorted(WEB_SRC.rglob("*.jsx")) + sorted(WEB_SRC.rglob("*.js"))
    _, js_lines = _count_lines(js_files)
    css_files = sorted(WEB_SRC.rglob("*.css"))
    _, css_lines = _count_lines(css_files)

    return {
        "server": (len(server_py), server_lines),
        "root": (len(root_py), root_lines),
        "tests": (test_n, test_lines),
        "scripts": (len(script_py), script_lines),
        "installer": (len(installer_py), installer_lines),
        "js": (len(js_files), js_lines),
        "css": (len(css_files), css_lines),
    }


def main():
    api_total, health, static, per_module = collect_routes()
    business_tables, core_tables = collect_tables()
    page_files, primary_routes, all_routes = collect_pages()
    code = collect_code()

    # Review schedule — read from the single source of truth.
    core_text = (SERVER / "core.py").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"EBBINGHAUS_INTERVALS = \{(.*?)\n\}", core_text, re.DOTALL)
    schedule_raw = m.group(1) if m else ""
    hours = [int(x) for x in re.findall(r":\s*(\d+),", schedule_raw)]
    hour_label = {
        4: "4小时", 24: "1天", 48: "2天", 96: "4天",
        168: "7天", 360: "15天", 720: "30天",
    }
    schedule = " → ".join(hour_label.get(h, f"{h}h") for h in hours)

    lines = []
    a = lines.append
    a("# WordMaster 项目事实报告 (PROJECT FACTS)")
    a("")
    a("> 本文件由 `scripts/project_stats.py` 自动生成，是所有参赛材料数字的唯一事实来源。")
    a("> 任何材料中的统计数字与本文件冲突时，以本文件为准。")
    a("")
    a(f"- **生成日期**：{date.today().isoformat()}")
    a("- **版本**：v0.1.0 Beta")
    a("- **技术栈**：React 18 + Vite + Tailwind CSS ｜ Python FastAPI + SQLAlchemy ｜ SQLite ｜ PyWebView ｜ PyInstaller")
    a("")
    a("## 1. 后端路由")
    a("")
    a(f"- **Router 模块数量**：{len(per_module)} 个（`server/routers/`）")
    a(f"- **API 路由总数**：{api_total} 个 `/api/*` 路由 + 1 个 `/health` 探针 = {api_total + health} 个 HTTP 路由")
    a(f"- **静态/SPA 兜底路由**（`app.py`）：{static} 个")
    a("")
    a("| 模块 | 路由数 |")
    a("|------|-------|")
    for mod, n in per_module.items():
        a(f"| `{mod}` | {n} |")
    a("")
    a("## 2. 数据库")
    a("")
    if business_tables is not None:
        a(f"- **SQLite 表总数（不含内部表 `sqlite_sequence`）**：{len(business_tables)}")
        a(f"- **业务表数量**：{len(core_tables)}（另有 1 张 `schema_version` 迁移追踪表）")
        a("")
        a("业务表：")
        for t in core_tables:
            a(f"  - `{t}`")
        a("")
        a("迁移追踪表：`schema_version`")
    else:
        a("- 未找到 `server/wordmaster.db`，无法统计表。")
    a("")
    a("## 3. 前端页面")
    a("")
    a(f"- **一级用户页面数量**：{len(primary_routes)}")
    a(f"- **页面组件数量**（`web/src/pages/*.jsx`）：{len(page_files)}")
    a("")
    a("一级用户页面：")
    for path, comp in primary_routes:
        a(f"  - `{path}` → {comp}")
    a("")
    a("全部路由：")
    for path, comp in all_routes:
        a(f"  - `{path}` → {comp}")
    a("")
    a("## 4. 代码量（物理行数）")
    a("")
    a("| 类别 | 文件数 | 行数 |")
    a("|------|-------|------|")
    a(f"| Python 后端（server/） | {code['server'][0]} | {code['server'][1]} |")
    a(f"| Python 根脚本（main.py 等） | {code['root'][0]} | {code['root'][1]} |")
    a(f"| Python 测试（tests/） | {code['tests'][0]} | {code['tests'][1]} |")
    a(f"| Python 脚本（scripts/） | {code['scripts'][0]} | {code['scripts'][1]} |")
    a(f"| 安装器（installer/） | {code['installer'][0]} | {code['installer'][1]} |")
    a(f"| 前端 JS/JSX（web/src/） | {code['js'][0]} | {code['js'][1]} |")
    a(f"| 前端 CSS（web/src/） | {code['css'][0]} | {code['css'][1]} |")
    py_total = sum(code[k][1] for k in ("server", "root", "tests", "scripts", "installer"))
    a(f"| **Python 合计** | — | **{py_total}** |")
    a(f"| **前端合计（JS/JSX+CSS）** | — | **{code['js'][1] + code['css'][1]}** |")
    a("")
    a("## 5. 复习算法")
    a("")
    a(f"- **阶段数**：{len(hours)} 个阶段（stage 0–{len(hours) - 1}）")
    a(f"- **复习间隔**：{schedule}")
    a("- **单一事实来源**：`server/core.py` 的 `EBBINGHAUS_INTERVALS`")
    a("")
    a("## 6. AI 模块")
    a("")
    a("- **大模型服务**：DeepSeek API（`deepseek-chat` 模型）")
    a("- **API Key 存储**：Windows 凭据管理器（keyring），非明文、不嵌入源码")
    a("- **能力**：AI 导师对话、AI 阅读生成、AI 查词、AI 测验、AI 学习报告、错词分析")
    a("")
    a("## 7. 打包方式")
    a("")
    a("- **主程序**：PyInstaller（`wordmaster.spec`）→ `dist/WordMaster.exe`")
    a("- **安装器**：PyInstaller（`installer/installer.spec`，per-user，无需管理员）→ `WordMaster_Setup.exe`")
    a("- **卸载**：`uninstall.exe`，保留用户 AppData 数据")

    out = ROOT / "docs" / "PROJECT_FACTS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── Console summary ──
    print(f"API routes: {api_total} (/api/*) + {health} health + {static} static")
    print(f"Router modules: {len(per_module)}")
    print(f"Business tables: {len(core_tables)} (+schema_version)")
    print(f"Primary pages: {len(primary_routes)}, page components: {len(page_files)}")
    print(f"Python lines: {py_total}, JS/JSX: {code['js'][1]}, CSS: {code['css'][1]}")
    print(f"Review stages: {len(hours)} -> {schedule}")
    print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

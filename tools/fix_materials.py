"""One-off consistency fix for the contest .docx materials.

Rewrites the specific stale numbers/descriptions in the WordMaster contest
documents so they match the real source code (see docs/PROJECT_FACTS.md).

This script is idempotent and reports every replacement it makes.

Run from the project root:
    python tools/fix_materials.py
"""
import sys
from pathlib import Path

import docx

MATERIALS_DIR = Path(__file__).resolve().parent.parent.parent / "相关材料"

# old -> new. Keys are matched as literal substrings; full-width punctuation is
# preserved exactly.
MAPPING = {
    # ── Review algorithm (P0-2): 90天 → 4小时/1天/2天/4天/7天/15天/30天 ──
    "1天/2天/4天/7天/15天/30天/90天": "4小时/1天/2天/4天/7天/15天/30天",

    # ── License (P0-3): proprietary, not MIT / "开源" ──
    "开源协议": "授权协议",
    "内部 Beta 测试": "专有软件（保留所有权利）",

    # ── Database tables (P0-4): 7 → 8 business tables ──
    "包含 7 张核心数据表": "包含 8 张核心数据表",
    "7 张核心数据表": "8 张核心数据表",
    "7 张数据表设计": "8 张数据表设计",
    "SQLAlchemy 数据模型 (7 tables)": "SQLAlchemy 数据模型 (8 tables)",
    "user_settings（用户设置）。设计数据库迁移机制":
        "user_settings（用户设置）、word_ai_explanations（AI 单词解析缓存）。设计数据库迁移机制",

    # ── Frontend pages (P0-4): 12 → 13 page components ──
    "规划 12 个功能页面": "规划 13 个功能页面",
    "12 个功能页面": "13 个功能页面",
    "12 个前端页面": "13 个前端页面",
    "12 个页面设计": "13 个页面设计",
    "前端页面 12 个": "前端页面 13 个",

    # ── Code lines (P0-4): ~11,000 → ~16,100 ──
    "代码总量约 11,000 行": "代码总量约 16,100 行",
    "~11,000 行 (Python 4,500 + React 6,500)": "~16,100 行 (Python 7,982 + JS/JSX 8,415 + CSS 747)",
    "~11,000 行": "~16,100 行",
    "约 11,000 行代码": "约 16,100 行代码",
    "React 代码": "JS/JSX 代码",
    "~6,500 行": "8,415 行",

    # ── Backend modules (P0-1): app.py single file → 9 router modules ──
    "13 个后端模块": "9 个路由模块",
    "Python 模块 13 个 (server/)": "路由模块 9 个 (server/routers/)",
    "（12 个前端页面 + 13 个后端模块 + 47 个 API 端点）": "（13 个前端页面 + 9 个路由模块 + 47 个 API 端点）",
    "app.py (47 endpoints)": "app.py + routers/ (47 API 路由)",
    "主应用 (47 API endpoints, 路由, 迁移)": "入口 + 9 个路由模块 (47 API 路由)",

    # ── Installer (item 18): Inno Setup → per-user installer ──
    "配置 Inno Setup 安装程序制作工具，生成带安装向导的标准 Windows 安装包":
        "配置 per-user 安装程序（tkinter GUI，无需管理员权限），生成标准 Windows 安装包",
    "3. (可选) Inno Setup (setup.iss) → installer_output/WordMaster_Setup.exe":
        "3. per-user 安装程序 (installer/installer.py) → WordMaster_Setup.exe",
}


def replace_in_runs(paragraph, mapping):
    """Replace mapping keys inside a paragraph's runs (preserves formatting)."""
    changed = 0
    for run in paragraph.runs:
        if not run.text:
            continue
        new = run.text
        for old, newv in mapping.items():
            if old in new:
                new = new.replace(old, newv)
        if new != run.text:
            changed += 1
            run.text = new
    return changed


def replace_in_paragraph(paragraph, mapping):
    """Run-aware replace; falls back to a whole-paragraph rebuild for spans."""
    changed = replace_in_runs(paragraph, mapping)
    # Fallback: text split across multiple runs.
    if any(old in paragraph.text for old in mapping):
        new_text = paragraph.text
        for old, newv in mapping.items():
            new_text = new_text.replace(old, newv)
        if new_text != paragraph.text and paragraph.runs:
            paragraph.runs[0].text = new_text
            for r in paragraph.runs[1:]:
                r.text = ""
            changed += 1
    return changed


def process_doc(path, mapping):
    doc = docx.Document(str(path))
    total = 0
    for p in doc.paragraphs:
        total += replace_in_paragraph(p, mapping)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    total += replace_in_paragraph(p, mapping)
    if total:
        doc.save(str(path))
    return total


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    targets = [
        "WordMaster架构分析报告（第二次发布版）.docx",
        "WordMaster软件开发人工投入与自主研发说明.docx",
    ]
    for name in targets:
        path = MATERIALS_DIR / name
        if not path.exists():
            print(f"SKIP (missing): {name}")
            continue
        n = process_doc(path, MAPPING)
        print(f"{'UPDATED' if n else 'unchanged'}: {name} ({n} replacements)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

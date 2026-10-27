# WordMaster 项目事实报告 (PROJECT FACTS)

> 本文件由 `scripts/project_stats.py` 自动生成，是所有参赛材料数字的唯一事实来源。
> 任何材料中的统计数字与本文件冲突时，以本文件为准。

- **生成日期**：2026-09-26
- **版本**：v0.1.0 Beta
- **技术栈**：React 18 + Vite + Tailwind CSS ｜ Python FastAPI + SQLAlchemy ｜ SQLite ｜ PyWebView ｜ PyInstaller

## 1. 后端路由

- **Router 模块数量**：14 个（`server/routers/`）
- **API 路由总数**：72 个 `/api/*` 路由 + 1 个 `/health` 探针 = 73 个 HTTP 路由
- **静态/SPA 兜底路由**（`app.py`）：0 个

| 模块 | 路由数 |
|------|-------|
| `routers/ai.py` | 14 |
| `routers/audio.py` | 5 |
| `routers/books.py` | 5 |
| `routers/dictionary.py` | 9 |
| `routers/games.py` | 1 |
| `routers/insights.py` | 5 |
| `routers/material.py` | 2 |
| `routers/media.py` | 1 |
| `routers/mistakes.py` | 5 |
| `routers/reading.py` | 2 |
| `routers/search.py` | 3 |
| `routers/stats.py` | 5 |
| `routers/teacher.py` | 3 |
| `routers/words.py` | 12 |

## 2. 数据库

- **SQLite 表总数（不含内部表 `sqlite_sequence`）**：19
- **业务表数量**：18（另有 1 张 `schema_version` 迁移追踪表）

业务表：
  - `ai_content_cache`
  - `book_words`
  - `books`
  - `confusion_sets`
  - `courses`
  - `daily_stats`
  - `dictionary`
  - `learning_events`
  - `mistake_records`
  - `source_documents`
  - `source_words`
  - `student_word_stats`
  - `students`
  - `study_records`
  - `user_settings`
  - `word_ai_explanations`
  - `word_memory_state`
  - `words`

迁移追踪表：`schema_version`

## 3. 前端页面

- **一级用户页面数量**：13
- **页面组件数量**（`web/src/pages/*.jsx`）：16

一级用户页面：
  - `/` → Dashboard
  - `/study` → Study
  - `/analytics` → Analytics
  - `/search` → Search
  - `/favorites` → Favorites
  - `/dictionary` → Dictionary
  - `/settings` → Settings
  - `/ai-tutor` → AITutor
  - `/reading` → Reading
  - `/games` → Games
  - `/material` → MaterialImport
  - `/teacher` → Teacher
  - `/mistakes` → MistakeBook

全部路由：
  - `/` → Dashboard
  - `/study` → Study
  - `/analytics` → Analytics
  - `/search` → Search
  - `/favorites` → Favorites
  - `/dictionary` → Dictionary
  - `/settings` → Settings
  - `/settings/ai` → AISettings
  - `/ai-tutor` → AITutor
  - `/reading` → Reading
  - `/agreement` → Agreement
  - `/about` → About
  - `/games` → Games
  - `/material` → MaterialImport
  - `/teacher` → Teacher
  - `/mistakes` → MistakeBook

## 4. 代码量（物理行数）

| 类别 | 文件数 | 行数 |
|------|-------|------|
| Python 后端（server/） | 47 | 8536 |
| Python 根脚本（main.py 等） | 3 | 1129 |
| Python 测试（tests/） | 22 | 2542 |
| Python 脚本（scripts/） | 2 | 323 |
| 安装器（installer/） | 4 | 725 |
| 前端 JS/JSX（web/src/） | 47 | 10296 |
| 前端 CSS（web/src/） | 1 | 756 |
| **Python 合计** | — | **13255** |
| **前端合计（JS/JSX+CSS）** | — | **11052** |

## 5. 复习算法

- **阶段数**：7 个阶段（stage 0–6）
- **复习间隔**：4小时 → 1天 → 2天 → 4天 → 7天 → 15天 → 30天
- **单一事实来源**：`server/core.py` 的 `EBBINGHAUS_INTERVALS`

## 6. AI 模块

- **大模型服务**：DeepSeek API（`deepseek-chat` 模型）
- **API Key 存储**：Windows 凭据管理器（keyring），非明文、不嵌入源码
- **能力**：AI 导师对话、AI 阅读生成、AI 查词、AI 测验、AI 学习报告、错词分析

## 7. 打包方式

- **主程序**：PyInstaller（`wordmaster.spec`）→ `dist/WordMaster.exe`
- **安装器**：PyInstaller（`installer/installer.spec`，per-user，无需管理员）→ `WordMaster_Setup.exe`
- **卸载**：`uninstall.exe`，保留用户 AppData 数据

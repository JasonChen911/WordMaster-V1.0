# 01 · 当前架构 (CURRENT ARCHITECTURE)

> 基于实际代码审计生成。本文档是 `docs/core-upgrade/` 系列的事实基线。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 + Vite + Tailwind CSS + Recharts + React Router 6（`web/src/`，14 页面） |
| 桌面壳 | PyWebView（`main.py`，原生 Windows 窗口，自动启动/停止后端） |
| 后端 | FastAPI + SQLAlchemy 2.x + uvicorn（`server/`，14 个路由模块，62 个 API） |
| 数据库 | SQLite（`server/database.py`，WAL + busy_timeout，本地 `%APPDATA%\WordMaster\`） |
| AI | DeepSeek（`server/ai/` Gateway + provider，`deepseek-chat`） |
| FSRS | MIT `fsrs` 库 v6.3.2（`server/srs/engine.py` 封装） |
| TTS | edge-tts（LGPL）+ pyttsx3 兜底（`server/audio_service.py`） |
| 打包 | PyInstaller（`wordmaster.spec` → `dist/WordMaster.exe`；installer 目录） |

## 后端分层

```
server/
├── app.py              # FastAPI 入口，注册 14 个 router
├── database.py         # 引擎/会话/WAL pragma
├── models.py           # SQLAlchemy 模型（16+ 表）
├── db_init.py          # 迁移 + 种子（schema_version 追踪 + 迁移前备份）
├── core.py             # 领域逻辑（学习队列/词书映射/进度统计/来源溯源）
├── srs/engine.py       # FSRS 封装（rating 映射/review/可解释性）
├── ai/
│   ├── gateway.py      # 统一 AI 入口（retry/JSON 校验/日志/token）
│   ├── schemas.py      # pydantic 结构化输出契约
│   ├── providers/deepseek.py
│   └── services/       # material / analysis / exercise / example
├── routers/            # words/stats/ai/books/dictionary/search/audio/games/media/material/insights/reading/teacher
├── ai_service.py       # 旧 AI 服务（兼容层，部分功能已迁 gateway）
├── config_manager.py   # API Key（keyring 安全存储）
├── seed.py             # 内置词库解析
├── confusion_seed.py   # 易混词种子
├── teacher_seed.py     # 教师 Demo 种子
└── mdx_reader.py       # MDX 词典解析
```

## 核心数据流（现状）

```
学习队列生成（core._generate_study_queue_sql）
  → 前端 Study 页 /api/words/study-queue
  → 作答 /api/study（record_study）
    → 更新 word.review_count/correct_count/accuracy/proficiency
    → FSRS review（srs.engine.review_card）→ word_memory_state
    → StudyRecord（薄：word_id/book_id/result/review_stage/studied_at）
    → DailyStats（按天聚合）
  → 下次 due 由 word_memory_state.due 决定
```

## 关键差距（本阶段要补）

1. **无统一 Learning Event 系统**：`study_records` 字段过薄，缺少 activity_type、session_id、response_time_ms、user_answer/correct_answer、error_type、source_type、FSRS 前后状态。
2. **首页未重构**：仍是以卡片/热力图/入口堆叠为主，未突出「今天学什么」。
3. **Material 引擎 schema 偏简**：缺 document_summary/lemma/tags/importance(0-1 浮点)。
4. **Diagnosis 输出偏简**：缺 problem_type/confused_with/recommended_exercise_type。
5. **教师端命名**：现为「教师端」，需改为「Teacher Preview」并强化 Demo 标注。
6. **练习结果未进入统一事件系统**：针对性练习作答后未写 Learning Event。

# 05 · 数据库迁移说明 (DATABASE MIGRATION)

## 迁移机制

- 所有 schema 变更通过 `server/db_init.py` 的 `_apply_migration(version, sql)` 执行。
- `schema_version` 表追踪已应用的迁移，保证幂等（同一库不会重复迁移）。
- 迁移前自动备份 `wordmaster.db`（`wordmaster.bak-<YYYYMMDD>.db`，保留最近 3 份）。
- 迁移失败：`try/except → rollback + 跳过`，不中断启动，不删数据。

## 本轮新增迁移

| 版本 | 内容 |
|---|---|
| v14.0 | `learning_events` 表（统一学习行为记录）+ 3 个索引 |

（前序 v9.0–v13.2 为上阶段已建：word_memory_state、ai_content_cache、confusion_sets、source_documents/source_words、courses/students/student_word_stats。）

## 迁移安全原则

1. **只加表/列，不改列名、不删表**——避免破坏旧数据。
2. 保留 `study_records`（旧记录表），新增 `learning_events`（新事实层），两者并存。
3. `legacy → FSRS` 迁移策略：旧复习记录保留原样；新词首次学习时按 FSRS 默认参数初始化（保守），不强行换算旧固定间隔。
4. `builtin_books_version` 标记内置词库版本，避免每次启动重解析 4.2 万词。

## 测试

`tests/test_migration.py`（6 项）验证：新库创建全部表、重复 init_db 幂等、已有学习记录在二次迁移后保留、schema_version 记录 v14.0。

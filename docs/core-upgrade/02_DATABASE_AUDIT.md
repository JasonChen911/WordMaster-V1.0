# 02 · 数据库审计 (DATABASE AUDIT)

> 基于 `server/models.py` 与 `server/db_init.py` 迁移的实际表结构。

## 现有表（18 张）

| 表 | 用途 | 关键字段 | 索引 |
|---|---|---|---|
| `words` | 词汇实体 | english(unique), phonetic, chinese, example_en/cn, review_count, correct_count, accuracy_rate, proficiency, is_mastered, study_status, next_review, last_reviewed_at | english |
| `book_words` | 词书↔词 多对多 | book_id, word_id | book_id, word_id |
| `books` | 词书 | book_name, word_count, is_active, is_builtin | id |
| `dictionary` | 词典条目 | book_id, word, definition_cn/en, part_of_speech, example | word, book_id |
| `word_memory_state` | **FSRS 记忆状态** | word_id(unique), state, step, stability, difficulty, due, last_review, reps, lapses | word_id, due |
| `study_records` | 学习记录（**过薄**） | word_id, book_id, result, review_stage, studied_at | book_id |
| `daily_stats` | 按天聚合 | date(unique), words_studied, correct_count, total_reviews, minutes_studied | date |
| `word_ai_explanations` | AI 详解缓存 | word(unique), explanation | word |
| `ai_content_cache` | 分级 AI 内容缓存 | word, level, exam_type, content_type, payload, model, version | word, uq(word,level,exam_type,content_type) |
| `confusion_sets` | 易混词 | word_a, word_b, distinction_cn, memory_tip_cn, mastered, source | word_a, word_b, uq(word_a,word_b) |
| `source_documents` | 来源材料 | title, content | title |
| `source_words` | 词↔来源溯源 | word_id, source_document_id, source_sentence | word_id, source_document_id, uq(word_id,doc_id) |
| `courses` | 教师课程 | name, description, book_id, is_demo | id |
| `students` | 教师学生（Demo） | name, class_name, is_demo, words_studied/many stats | id |
| `student_word_stats` | 学生↔词表现（Demo） | student_id, word, wrong_count, accuracy_rate, lapses | word, uq(student_id,word) |
| `user_settings` | 用户设置 | key(pk), value | key |
| `schema_version` | 迁移追踪 | version(unique) | version |

## 审计结论

### ✅ 已满足本阶段要求的部分
- FSRS 状态表 `word_memory_state` 完整（difficulty/stability/due/reps/lapses/state）。
- 来源溯源 `source_documents` + `source_words` 已建立。
- AI 内容缓存 `ai_content_cache` 已按 (word, level, exam_type, content_type) 分级。
- 易混词 `confusion_sets` 已建立。
- 迁移体系完善（schema_version 追踪 + 迁移前备份）。

### ❌ 需要补齐的部分
1. **`study_records` 不是真正的 Learning Event**：缺 `activity_type`、`session_id`、`response_time_ms`、`user_answer`、`correct_answer`、`error_type`、`source_type`、`source_id`、FSRS 前后状态。
   - 决策：**新增 `learning_events` 表**（保留 `study_records` 兼容旧逻辑，不删数据）。
2. `source_documents` 缺 `type` / `original_filename` / `content_hash`（去重需要）。
3. `confusion_sets` 缺 `detected_from` / `confidence` / `status`（识别来源）。

### 迁移安全原则
- 所有新表走 `schema_version` 迁移，迁移前自动备份 `wordmaster.db`。
- 不删除 `study_records`，不重命名现有列（避免破坏旧数据）。

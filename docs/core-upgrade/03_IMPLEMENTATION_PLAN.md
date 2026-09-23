# 03 · 实施计划 (IMPLEMENTATION PLAN)

> 目标：把 WordMaster 从「背单词 + AI 功能」升级为「基于真实材料、记忆状态与学习行为的 AI 自适应词汇学习系统」。核心闭环：Input → Understand → Learn → Remember → Observe → Diagnose → Intervene → Adapt → Insight。

## 分阶段计划

### Phase 0 — 稳定性
- [x] SQLite WAL + busy_timeout（上轮已完成）。
- [x] 迁移前备份（上轮已完成）。
- [x] 前端 fetch 超时 + AbortController（上轮已完成）。
- [x] get_word 500→404（上轮已完成）。
- [x] 首启种子库（上轮已完成）。
- 本轮：验证无回归，确认旧数据库可升级。

### Phase 1 — 数据基础：Learning Event System
- 新增 `learning_events` 表（activity_type / session_id / timestamp / result / rating / response_time_ms / user_answer / correct_answer / error_type / source_type / source_id / fsrs_before / fsrs_after / client_version / algorithm_version）。
- 保留 `study_records`（兼容），record_study 同时写 LearningEvent。
- 练习 / 阅读 / 易混词作答统一写 LearningEvent。
- 迁移安全 + 测试。

### Phase 2 — FSRS Memory Engine
- [x] `word_memory_state` + FSRS 调度（上轮已完成）。
- [x] 四级反馈 + 键盘 1-4 + Memory Explanation（上轮已完成）。
- 本轮：确认 retrievability 显示可靠（enable_fuzzing=False 已保证确定性）。
- legacy → FSRS 迁移策略（保守初始化，migration_version 幂等）。

### Phase 3 — AI Material Engine
- [x] 材料导入 / 清洗 / tokenize / AI 提取 / 确认生成词书（上轮已完成）。
- 本轮对齐：AI 输出加 document_summary / lemma / importance(0-1 浮点) / tags。
- 候选排序结合学习历史（已掌握降权 / 未学升权 / 历史易错升权）——可解释推荐原因。
- source_documents 加 type / original_filename / content_hash（去重）。

### Phase 4 — AI Learning Diagnosis
- [x] 「为什么总记不住」基于真实记录（上轮已完成）。
- 本轮对齐：输出加 problem_type / confused_with / recommended_exercise_type。
- 输入最小化（只传必要学习摘要），不做医学诊断。

### Phase 5 — Confusion + Targeted Practice
- [x] confusion_sets + 针对性练习（上轮已完成）。
- 本轮：练习作答结果写入 LearningEvent；confusion 表加 detected_from/confidence/status。
- 练习质量：规则校验（目标词出现/答案在选项/无重复/answer 有效），失败 fallback。

### Phase 6 — Reading Loop
- [x] 阅读点词 → 加入生词 → 来源溯源 → 复习展示来源（上轮已完成）。

### Phase 7 — Home + Insights
- Insights 页 [x] 上轮已重构（真实统计 + AI 洞察 + FSRS 高风险 + 薄弱词 + 易混词 + 练习）。
- 首页：本轮重构，突出「今天学什么」。

### Phase 8 — Teacher Preview
- [x] 教师端 MVP（上轮已完成）。
- 本轮：重命名为 Teacher Preview，强化 Demo 标注。

### Phase 9 — Tests
- 补齐：Learning Event / migration / confusion detection / cache / timeout / insights 聚合 / material 解析 / source document。

### Phase 10 — Release Build
- 前端 build + PyInstaller + installer，实测 EXE，生成 core-upgrade 05-12 文档。

## 执行原则
- 每阶段完成即验证（测试 + 手工流程）。
- 不删除用户数据，迁移前备份。
- AI 挂掉基础学习照常；不伪造统计。
- 每阶段本地 commit（不 push）。

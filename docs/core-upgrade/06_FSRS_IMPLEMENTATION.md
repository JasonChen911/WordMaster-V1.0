# 06 · FSRS 实现说明 (FSRS IMPLEMENTATION)

## 采用方案

- 使用 MIT 许可的 `fsrs` 库（py-fsrs，v6.3.2，Open Spaced Repetition，2022），封装于 `server/srs/engine.py`。
- 不复制 Anki(AGPL)/LibreLingo(AGPL) 代码。许可证记录于 `THIRD_PARTY_LICENSES.md`。

## 数据结构

`word_memory_state`（每词一行）：
- `state`：1=learning / 2=review / 3=relearning
- `step`：学习步数
- `stability`：记忆稳定度（天）
- `difficulty`：FSRS 难度（1-10）
- `due`：下次复习时间（**单一事实来源**）
- `last_review`、`reps`、`lapses`

## 四级反馈映射

| 前端按钮 | result 字段 | FSRS Rating |
|---|---|---|
| 忘记 | unknown | Again (1) |
| 困难 | fuzzy | Hard (2) |
| 一般 | know | Good (3) |
| 简单 | too_easy | Easy (4) |

键盘快捷键：1 / 2 / 3 / 4。

## 调度

- `srs.engine.review_card(word_id, state, result)` → 调用 `fsrs.Scheduler.review_card`，返回新的 FSRS 状态（含 due）。
- `enable_fuzzing=False` 保证间隔确定性（「预计 X 天后复习」精确、可测试）。
- `record_study` 用 FSRS 结果更新 `word_memory_state` 与 `word.next_review`。

## 可解释性（Memory Explanation）

`explain_state()` 返回：
- `retrievability`：预计记忆保持率（0-1，由 FSRS 真实计算）
- `stability_days`：稳定度（天）
- `difficulty`：难度
- `lapses` / `reps`：遗忘/复习次数
- `forgetting_risk`：高/中/低（由 retrievability 阈值推导）
- `next_review`：下次复习时间

学习页「为什么今天复习」面板展示这些真实数据，不伪造百分比。

## 掌握判定

`is_mastered()`：state=Review 且 stability ≥ 21 天。`proficiency_from_state()` 映射到 0-5 熟练度。

## 测试

`tests/test_fsrs.py`（25 项）：映射、新词调度、遗忘 lapse、难度上升、稳定度增长、掌握阈值、可解释性字段。

# WordMaster AI — 实施计划 (IMPLEMENTATION PLAN)

> 依据 `docs/AUDIT_REPORT.md`。执行原则：复用现有架构、不删用户数据、不重写技术栈、每阶段运行测试验证。

## 总路线

```
P0 稳定性  →  P1 FSRS  →  P2 AI Material Engine  →  P3 AI Learning Analysis
→  P4 Reading 闭环  →  P5 Teacher MVP  →  P6 Competition Demo  →  P7 Release Build
```

---

## P0 — 稳定性（先行，不改变功能语义）

| 项 | 动作 | 文件 |
|---|---|---|
| 0.1 | 开启 SQLite WAL + `busy_timeout`，加 `connect_args` | `server/database.py` |
| 0.2 | 迁移前自动备份 `wordmaster.db`（`*.bak-<ts>`，保留最近 3 份） | `server/db_init.py` |
| 0.3 | 修复 `get_word` 找不到词返回 404（消除 500） | `server/routers/words.py` |
| 0.4 | 前端统一 fetch timeout + AbortController；AI 失败统一降级文案 | `web/src/api.js` |
| 0.5 | 打包脚本生成 `wordmaster_seed.db`（消除首启 4.2 万词解析） | `scripts/build_seed_db.py` + `wordmaster.spec` |

**验证**：启动后端 → 建库 → 导入词书 → 学习 → 退出重启数据仍在；console/Python 无异常。

---

## P1 — FSRS 自适应复习（核心）

| 项 | 动作 | 文件 |
|---|---|---|
| 1.1 | 新增 `word_memory_state` 表（difficulty/stability/retrievability/last_review/next_review/review_count/lapse_count/state JSON） | `server/models.py` |
| 1.2 | 实现 MIT 许可的 FSRS-5 调度器（自研实现 + 版权注明），四级反馈映射 忘记/困难/一般/简单 → again/hard/good/easy | `server/fsrs/scheduler.py` |
| 1.3 | `record_study` 改用 FSRS 计算 next_review；保留 `review_stage` 兼容字段 | `server/routers/words.py` |
| 1.4 | 提供可解释性接口：预计保持率/遗忘风险/下次复习/为什么今天复习 | `server/routers/words.py` + 学习页 |
| 1.5 | 学习页 UI：四级按钮 + 完成提示「预计 X 天后复习 / 遗忘风险较高」+ Why? + 键盘 1/2/3/4 | `web/src/pages/Study.jsx` |
| 1.6 | `reset` 同步清 FSRS 状态 | `server/routers/words.py` |

**验证**：`tests/test_fsrs.py` 通过；学习页能显示下一次复习与保持率。

---

## P2 — AI Material Engine（比赛关键）

| 项 | 动作 | 文件 |
|---|---|---|
| 2.1 | AI Gateway 分层：`gateway.py` + `providers/deepseek.py` + `services/*.py`，统一 model/key/timeout/retry/JSON/logging/cache/token | `server/ai/` |
| 2.2 | 迁移现有 `ai_service.py` 调用到 Gateway（保持 API 兼容） | `server/routers/ai.py` |
| 2.3 | 材料导入：TXT/MD/纯文本/复制粘贴 → 文本提取 → 清洗 → 词汇识别 | `server/services/material_service.py` |
| 2.4 | AI 提取重点词：结构化 JSON + **pydantic schema 校验** + retry/repair/fallback | 同上 |
| 2.5 | 候选词展示 + 人工确认 → 生成词书 | `web/src/pages/MaterialImport.jsx` |
| 2.6 | AI 例句缓存升级（word+level+exam_type+version） | `server/models.py` + cache service |

**验证**：导入示例文章 → 得到候选词 → AI 推荐重点词 → 确认生成词书 → 进入学习。

---

## P3 — AI Learning Analysis

| 项 | 动作 | 文件 |
|---|---|---|
| 3.1 | 「为什么我总记不住」：基于错误次数/拼写/选义/间隔/相似词生成解释（数据不足时明确提示） | `server/services/analysis_service.py` |
| 3.2 | 易混词系统：`confusion_sets` 表 + 识别 + 生成辨析/记忆法/双词例句/选择/填空 | 同上 + `web/src/pages/` |
| 3.3 | AI 练习生成器：选择释义/拼写/听音识词/语境填空/辨析 | `server/services/exercise_service.py` |
| 3.4 | 学习分析页升级：真实统计（7 天学习/复习/正确率/遗忘率/时长）+ AI 解释数据 | `web/src/pages/Analytics.jsx` |
| 3.5 | AI Learning Insights 组件（首页/Analytics） | `web/src/components/` |

**验证**：故意答错 economic/economical → 生成辨析与练习 → 分析页看到真实统计。

---

## P4 — Reading 闭环

| 项 | 动作 | 文件 |
|---|---|---|
| 4.1 | 阅读页点击生词 → 释义 → 加入 FSRS（记录 source_document/source_sentence） | `server/routers/` + `web/src/pages/Reading.jsx` |
| 4.2 | 复习时优先展示「你第一次在哪里看到它」来源语境 | `web/src/components/WordCard.jsx` |

**验证**：阅读 → 点词加入 → 学习页出现该词 → 复习显示来源。

---

## P5 — Teacher MVP

| 项 | 动作 | 文件 |
|---|---|---|
| 5.1 | `courses` / `classes` / `assignments` 表 + 教师端 API | `server/routers/teacher.py` |
| 5.2 | 教师：创建课程 → 上传材料 → AI 提取 → 人工确认 → 生成课程词书 → 发布任务 | 前端页面 |
| 5.3 | 教师报告：完成率/平均正确率/共性薄弱词/高遗忘风险词 + AI 总结 | 同上 |
| 5.4 | **Local Classroom Demo**（明确标记 Demo Class / Demo 数据，不冒充真实用户） | seed demo data |

**验证**：教师端可走通「上传→提取→发布→查看薄弱点」。

---

## P6 — Competition Demo

| 项 | 动作 | 文件 |
|---|---|---|
| 6.1 | Demo Mode：示例大学英语短文 + 一键 AI 分析（60~120 秒完整演示） | `web/src/pages/Demo.jsx` |
| 6.2 | 参赛资料 `docs/competition/01~06` | `docs/competition/` |
| 6.3 | 关于页升级（一句话定位 + 功能列表，不夸大） | `web/src/pages/About.jsx` |

---

## P7 — Release Build

| 项 | 动作 |
|---|---|
| 7.1 | 补测试：FSRS/迁移/AI JSON/超时/导入/队列/缓存 |
| 7.2 | 前端 build → PyInstaller → installer → EXE 产物 |
| 7.3 | 稳定性测试清单逐项验证 |
| 7.4 | 最终 RELEASE REPORT |

---

## 风险与守则

- 迁移前必备份 DB；失败回滚 + 备份，绝不删用户数据。
- FSRS 用 MIT 实现并注明版权；edge-tts(LGPL) 合规记录；内置词库标 LICENSE_REVIEW_REQUIRED。
- AI 挂掉 ≠ 软件不能用：所有 AI 入口带 timeout/降级，基础背词离线可用。
- 每阶段结束运行现有 + 新增测试，不留下 TODO/假按钮/空白页。

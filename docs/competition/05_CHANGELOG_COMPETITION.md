# 05 · 参赛改进清单 (CHANGELOG)

> 本文件记录本次为 iCAN「AI 产品实现」赛道完成的**真实、可运行**改进。
> 所有功能均运行在 WordMaster 本体中，非一次性 Demo。

## 一、稳定性（P0）

- [x] SQLite 开启 WAL + `busy_timeout=30s` + 外键约束，解决并发读写 `database is locked`。
- [x] 迁移前自动备份 `wordmaster.db`（保留最近 3 份），迁移失败回滚不丢数据。
- [x] 修复 `GET /api/words/{id}` 找不到词时返回 500 的问题（改为 404）。
- [x] 前端统一 fetch 超时 + AbortController，AI 请求不再让界面假死。
- [x] 新增预初始化种子库 `scripts/build_seed_db.py`，消除首启 4.2 万词现场解析，首启提速。

## 二、FSRS 自适应复习（P1 · 核心）

- [x] 接入 MIT 许可的 `fsrs` 库（版本 6.3.2），封装为 `server/srs/engine.py`。
- [x] 新增 `word_memory_state` 表：`difficulty / stability / retrievability / due / reps / lapses`。
- [x] 学习页改为四级反馈「忘记/困难/一般/简单」，支持键盘 1-4。
- [x] `record_study` 改用 FSRS 计算下次复习；`reset` 同步清除 FSRS 状态。
- [x] 「为什么今天复习」可解释面板：保持率 / 稳定度 / 遗忘风险 / 下次复习时间。
- [x] 废弃固定艾宾浩斯间隔（旧逻辑仅作兼容保留）。

## 三、AI Material Engine（P2 · 比赛关键）

- [x] 建立 AI Gateway（`server/ai/`）：统一 model/key/timeout/retry/JSON 校验/日志/token。
- [x] DeepSeek provider 独立（`providers/deepseek.py`），便于未来扩展其它 LLM。
- [x] 材料导入（TXT/Markdown/纯文本/粘贴）→ 清洗 → 词汇识别 → AI 提取重点词。
- [x] AI 输出结构化 JSON + **pydantic schema 校验** + retry + repair + fallback。
- [x] 候选词人工确认 → 一键生成词书（并自动激活进入学习队列）。
- [x] AI 例句缓存升级：按 `word + level + exam_type + version` 缓存（`ai_content_cache`）。

## 四、AI 学习分析（P3）

- [x] 「为什么总记不住」：基于真实错误次数/正确率/遗忘次数的错因诊断。
- [x] 易混词系统：8 组内置辨析（affect/effect、economic/economical 等）+ 记忆法 + 双词例句。
- [x] AI 练习生成器：选择释义/拼写/语境填空/辨析，含答案与解析。
- [x] 学习分析页升级：真实 7 天统计 + FSRS 高风险词 + AI 洞察（AI 只解释真实数据）。

## 五、阅读闭环（P4）

- [x] 阅读中点词 → 加入生词 → 进入 FSRS。
- [x] 记录 `source_document` / `source_sentence`，复习时展示“你第一次在哪里看到它”。

## 六、教师端 MVP（P5）

- [x] `courses / students / student_word_stats` 表 + 教师端 API。
- [x] 教师端页面：班级完成率/正确率/遗忘率、共性薄弱词、学生名单。
- [x] AI 教学总结（基于真实班级统计）。
- [x] Local Classroom Demo：明确标注「演示数据」，绝不冒充真实用户。

## 七、比赛演示（P6）

- [x] 示例材料 + 一键 AI 分析（Material 页内置示例短文）。
- [x] 完整演示链路：上传 → AI 提取 → 确认 → 学习 → FSRS → 错因分析 → 教师端。
- [x] 参赛文档 `docs/competition/01~06`。

## 测试

- 新增 `tests/test_fsrs.py`（25 项）、`tests/test_ai_gateway.py`（16 项）。
- 更新 `tests/test_routes.py`（57 项，覆盖全部 62 个 API 路由）。
- 既有测试全部通过：review algorithm（36）、routes（57）、fsrs（25）、ai gateway（16）、api key priority（18）。

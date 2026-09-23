# WordMaster AI — 全面代码审计报告 (AUDIT REPORT)

> 生成日期：2026-09-23
> 审计范围：`WordMaster本体文件/` 下全部后端（server/）、前端（web/src/）、打包（wordmaster.spec / installer/）、数据（data/、内置词库请勿删除/）、测试（tests/）。
> 审计方法：逐文件通读 + 运行现有测试 + 依赖许可证核查。

---

## 1. 当前技术架构

```
React 18 + Vite + Tailwind CSS + Recharts + React Router 6   (web/)
        ↓  HTTP (localhost 动态端口 8000-8020)
PyWebView 桌面窗口（Windows / Edge WebView2，原生窗口）       (main.py)
        ↓
FastAPI (uvicorn, 异步)                                       (server/app.py)
        ├─ routers/  9 个路由模块，47 个 /api/* 路由 + /health
        ├─ core.py          共享领域逻辑（复习算法、词书映射、查询助手）
        ├─ ai_service.py    DeepSeek API 集成（单一模块，已相对集中）
        ├─ audio_service.py Edge TTS 音频 + 本地缓存
        ├─ config_manager.py API Key 安全存储（Windows Credential Manager）
        ├─ seed.py / mdx_reader.py  词库解析
        └─ db_init.py       schema 创建 + 迁移（schema_version 追踪）
        ↓
SQLite (SQLAlchemy ORM, wordmaster.db)                        (server/database.py)
```

| 层 | 技术 | 状态 |
|---|---|---|
| 前端 | React 18 + Vite + Tailwind + Recharts + Router 6 | 健康 |
| 桌面壳 | PyWebView 6.x（原生窗口，无地址栏） | 健康 |
| 后端 | FastAPI + SQLAlchemy 2.x | 健康，分层清晰 |
| 数据库 | SQLite（`%APPDATA%\WordMaster\wordmaster.db`） | 健康，有迁移体系 |
| AI | DeepSeek API（`deepseek-chat`），Key 存 keyring | 健康，但无统一 Gateway |
| 音频 | edge-tts（Edge 神经 TTS）+ pyttsx3 兜底 + 本地 MP3 缓存 | 健康 |
| 打包 | PyInstaller（`dist/WordMaster.exe` 已存在，29MB） | 已能产出 EXE |

**结论：代码整体质量良好，分层清晰，已有迁移/日志/密钥安全/JSON 兜底等基础，不是需要推倒重来的烂代码。** 本次升级应在复用现有架构的前提下补齐「AI 参与学习路径」与「FSRS」两大核心能力。

---

## 2. 当前功能清单（已确认存在且可运行）

| 模块 | 功能 | 状态 |
|---|---|---|
| Dashboard | 今日任务、连续天数、掌握进度环、30 天热力图、搜索、每日目标 | ✅ |
| 单词学习 | 卡片翻转、四级反馈（太简单/认识/模糊/不会）、发音、例句 | ✅ |
| 复习机制 | 7 级**艾宾浩斯固定间隔**（4h→1d→2d→4d→7d→15d→30d） | ⚠️ 待替换为 FSRS |
| 词书 | 内置 5 本（高中/四级/六级/考研/托福，约 4.2 万词）+ MDX/文本/CSV/JSON 导入 | ✅ |
| 游戏 | 填词填空、字母乱序 | ✅ |
| AI 导师 | 3 个角色聊天（Emma/Alex/Sophia） | ⚠️ 非核心竞争力 |
| AI 阅读 | 按考试/难度/主题生成文章 + 阅读理解题 | ⚠️ 未闭环 |
| AI 查词/例句 | explain + word/explain（SQLite 缓存） | ✅ |
| AI 测验 | 选择题/填空题 | ✅ |
| AI 报告/错词分析 | analyze-errors + report | ✅（浅） |
| 搜索 | 中英文模糊搜索、学习词 + 词典双路 | ✅ |
| 收藏 | 收藏/取消 | ✅ |
| 学习分析 | 7 天趋势、熟练度分布、薄弱词、AI 建议 | ✅（浅） |
| 主题系统 | 6 套主题 + 自定义 RGB + 暗色 | ⚠️ 非核心，保留即可 |
| 设置 | 音效、主题、AI Key 管理、协议/关于 | ✅ |

---

## 3. 已发现问题（按严重程度排序）

### 🔴 P0 — 稳定性 / 数据风险

| # | 问题 | 位置 | 影响 | 严重度 |
|---|---|---|---|---|
| 1 | **SQLite 未开启 WAL / busy_timeout**。Dashboard 每 3s 轮询读取，学习页持续写入，并发下可能触发 `database is locked` | `server/database.py` | 学习/首页偶发 500 | 🔴 高 |
| 2 | **首次启动慢 + 18s 超时风险**。`server/wordmaster_seed.db` 被引用但**未随包产出**（不存在），新装用户首次启动需现场解析 4.2 万词；`main.py` 后端就绪预算 18s 在慢机/杀软扫描下可能不够 | `database.py:28`、`main.py:55` | 新装首启失败 | 🔴 高 |
| 3 | **前端 fetch 无 timeout / 无 AbortController**。AI 请求（尤其阅读 90s、报告、例句）后端挂起时，前端只能等，无取消按钮 | `web/src/api.js`、各页面 | UI 假死感 | 🔴 高 |
| 4 | **`get_word` 找不到词时返回 `{"error": ...}` dict，与 `response_model=WordOut` 不符 → FastAPI 校验抛 500** | `routers/words.py:63-68` | 潜在 500 | 🟠 中 |
| 5 | **AI JSON 无 schema 校验**，仅 best-effort `_parse_json_response`，模型返回缺字段/错类型时靠 `str()`/空串兜底，存在「假数据」风险 | `ai_service.py` | AI 输出污染 | 🟠 中 |
| 6 | **AI 返回格式异常时 reading 直接 `json.loads` 抛错→返 `{"error": ...}`，无 retry/repair** | `routers/ai.py:159-163` | 功能偶发失败 | 🟠 中 |
| 7 | **`_import_progress` / `_applied_versions` 全局可变字典**，多线程边界下存在竞态（当前单用户可接受，但应加锁） | `routers/dictionary.py`、`db_init.py` | 低概率竞态 | 🟡 低 |

### 🟠 P1 — 核心能力缺口（产品升级关键）

| # | 缺口 | 说明 |
|---|---|---|
| 8 | **复习是固定艾宾浩斯间隔，无自适应** | 无 difficulty/stability/retrievability 状态，无「为什么今天复习」可解释性。这是产品核心短板 |
| 9 | **无 AI 材料引擎** | 无法从文章 TXT/MD/文本提取重点词生成词表；无结构化 JSON + schema 校验 + retry/repair/fallback |
| 10 | **AI 例句缓存键仅有 word** | 无 level/exam_type/version 维度，无法按「高中/CET4/CET6/考研/TOEFL」分级缓存 |
| 11 | **阅读未闭环** | 生成文章的 vocabulary 不能点击加入 FSRS 学习队列，无 source_document/source_sentence 溯源 |
| 12 | **无「为什么总记不住」** | 单词详情无基于真实学习记录的错因诊断 |
| 13 | **无易混词系统** | 无 confusion_set（affect/effect 等） |
| 14 | **无 AI 练习生成器** | 仅 quiz（选择/填空），无听音识词/语境填空/辨析 |
| 15 | **无教师端** | 无课程/班级/作业/班级报告 |
| 16 | **无 AI Gateway 结构** | 现为单一 `ai_service.py`（已较集中），但无 provider/service 分层、无统一 token 统计/缓存/重试策略 |

### 🟡 P2 — 性能 / 代码质量

| # | 问题 | 位置 |
|---|---|---|
| 17 | 首页热力图/连续天数各 30 次单条 SQL（N+1） | `stats.py` |
| 18 | 词典中文搜索 `definition_cn.ilike('%x%')` 全表扫描，无 FTS | `dictionary.py` |
| 19 | `recent_records` 每条循环查一次 `Word.english`（10 次 N+1） | `stats.py:87-94` |
| 20 | 死代码：`server/_archived/word_manager.py`（15KB）、根目录 `convert_wordbanks.py`、`generate_examples.py` | — |
| 21 | `BOOK_ID_MAP` 硬编码中文名，AI 生成的新词书 ID 映射脆弱 | `core.py:57` |
| 22 | `study_records.book_id` 默认 0，历史记录跨词书污染「今日新词」统计 | `models.py`、`stats.py` |
| 23 | 主题系统含粒子/极光动画（AuroraBackground / StarlightParticles），与「clean/modern/academic」目标相悖 | `web/src/theme/` |

### ⚖️ 许可证 / 知识产权

| # | 事项 | 风险 |
|---|---|---|
| 24 | **edge-tts = LGPLv3**（已核实 classifier）。PyInstaller 打包属静态捆绑，需满足 LGPL 允许替换库、附 LGPL 文本等义务 | 🟠 需记录并合规 |
| 25 | pyttsx3 许可证元数据缺失，需核实（应为 MIT） | 🟡 核实 |
| 26 | 内置词库 5 个 TXT（`2 高中-乱序.txt` 等）**来源无法确认** | 🔴 标记 `LICENSE_REVIEW_REQUIRED` |
| 27 | 缺 `THIRD_PARTY_LICENSES.md` / `CONTENT_SOURCES.md` | 🟠 需补 |
| 28 | FSRS 需选用 MIT 实现（如 py-fsrs / ts-fsrs），禁止复制 Anki(AGPL)/LibreLingo(AGPL) 代码 | 需执行 |

---

## 4. 潜在数据丢失风险（必须规避）

1. **删除词书**（`books.py:delete_book`）：删除「仅本词书独占」的 Word/StudyRecord。逻辑正确，但需确保未来 AI 词书删除时同样走「独占才删」而非级联误删。
2. **重置进度**（`words.py:reset`）：清空 review/study_status 但保留词书与单词，安全。新增 FSRS 字段后，reset 必须同步清 FSRS 状态。
3. **迁移失败兜底**（`db_init.py:_apply_migration`）：当前 `except → rollback + skip`，**不会备份数据库**。升级时若迁移失败，可能留下半迁移 schema。需在迁移前备份 `wordmaster.db`。
4. **内置词书重建**（`db_init.py:_initialize_builtin_books`）：`BUILTIN_BOOKS_VERSION` 变化会重跑，`dictionary` 表按 book 全删重建——**不触碰学习进度**（words 表进度字段不受影响），安全，但需确认新版本号不会误触发。

---

## 5. 修改建议（重构优先级）

### 优先级 P0（本次必须先做）
1. 开启 SQLite **WAL + busy_timeout**（`database.py`）。
2. 后端就绪预算逻辑保留，但**在首次启动做种子库预热**或在 README/打包脚本中生成 `wordmaster_seed.db`，消除首启 4.2 万词现场解析。
3. 前端 `api.js` 统一加 **fetch timeout + AbortController**；AI 请求失败统一降级文案「AI 服务暂时不可用，基础学习功能不受影响」。
4. 修复 `get_word` 的 500（返回 `WordOut` 或 `404`）。
5. 迁移前**自动备份 `wordmaster.db`**（`wordmaster.db.bak-<version>`）。

### 优先级 P1（产品升级核心）
6. **接入 FSRS**：新增 `word_memory_state`（difficulty/stability/retrievability/last_review/next_review/review_count/lapse_count），四级反馈映射「忘记/困难/一般/简单」，并提供可解释性数据（预计保持率/遗忘风险/下次复习）。
7. **AI Material Engine**：文本/MD/TXT/复制粘贴 → 清洗 → 词汇识别 → AI 提取重点词（结构化 JSON + pydantic schema 校验 + retry/repair/fallback）→ 人工确认 → 生成词书。
8. **AI 例句缓存升级**：缓存键加入 level/exam_type/version，支持高中/CET4/CET6/考研/TOEFL。
9. **阅读闭环**：点击生词 → 查看释义 → 加入 FSRS，记录 source_document/source_sentence。
10. **「为什么总记不住」+ 易混词 + AI 练习生成器**。
11. **AI Gateway 分层**：`server/ai/gateway.py`（统一 model/key/timeout/retry/JSON 解析/logging/cache/token）+ `providers/deepseek.py` + `services/{example,material,analysis,exercise}.py`。

### 优先级 P2
12. 教师端 MVP（课程/班级/作业/报告 + Local Classroom Demo）。
13. 首页/学习页重设计（3 秒知道今天学什么，突出 WORD/phonetic/meaning/example + Why?）。
14. 学习分析页升级（真实统计 + AI 解释数据）。
15. 性能：热力图/连续天数/最近记录改聚合 SQL；词典中文搜索可后置 FTS。
16. 清理死代码（`_archived/`、根目录一次性脚本）。

### 优先级 P3（比赛/发布）
17. Demo Mode + 示例材料 + 一键演示流程。
18. 参赛资料文档（docs/competition/01~06）。
19. `THIRD_PARTY_LICENSES.md` + `CONTENT_SOURCES.md`（词库标 LICENSE_REVIEW_REQUIRED）。
20. Windows Release Build（前端 build + PyInstaller + installer）。

---

## 6. 现有测试基线

已运行，全部通过：
- `tests/test_review_algorithm.py` → **36 PASSED, 0 FAILED**
- `tests/test_routes.py` → **53 PASSED, 0 FAILED**

待补：FSRS scheduler、迁移、AI JSON 解析、AI 超时、词导入、复习队列、缓存测试。

---

## 7. 一句话结论

**代码基础健康、可复用率高；真正的产品短板是「AI 未参与学习路径」与「复习是死板固定间隔」。** 本次升级聚焦：P0 稳定性（WAL/超时/备份）→ P1 FSRS + AI Material Engine + 学习分析 + 阅读闭环 → P2 教师端 MVP → P3 比赛 Demo 与发布，全程不删用户数据、不重写技术栈。

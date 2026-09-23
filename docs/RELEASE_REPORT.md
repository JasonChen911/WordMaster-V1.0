# ==============================
# WORDMASTER AI RELEASE REPORT
# ==============================

> 生成日期：2026-09-23

## 1. 当前版本

**WordMaster AI**（由 WordMaster v0.1.0 Beta 重构升级而来）。
定位：面向高校英语课程、四六级、考研场景的 **AI 驱动、本地优先、自适应词汇学习与教学平台**。

## 2. 完成的核心功能

- AI 材料引擎：TXT / Markdown / 纯文本 / 粘贴 → AI 提取重点词 → 人工确认 → 一键生成词书（自动激活进入学习队列）。
- FSRS 自适应复习：四级反馈（忘记/困难/一般/简单），difficulty/stability/retrievability，可解释「为什么今天复习」。
- AI 学习分析：错因诊断、易混词辨析（8 组内置）、针对性练习生成、真实统计 + AI 洞察。
- 阅读闭环：阅读中点词加入生词，记录来源语境，复习时回看。
- 教师端 MVP：班级学习情况、共性薄弱词、AI 教学总结（Local Classroom Demo，明确标注演示数据）。

## 3. AI 功能

- AI Gateway（`server/ai/`）：统一 model/key/timeout/retry/JSON 校验/日志/token 统计；provider 可扩展。
- 材料分析（结构化 JSON + pydantic schema 校验 + retry/repair/fallback）。
- 分级例句缓存（word + level + exam_type + version）。
- 错因诊断、AI 练习生成、AI 学习洞察、AI 教学总结。
- 所有 AI 入口带 timeout + 降级，AI 挂掉 ≠ 软件不能用。

## 4. FSRS 功能

- 接入 MIT 许可 `fsrs` 库（v6.3.2，Open Spaced Repetition），封装 `server/srs/engine.py`。
- `word_memory_state` 表存 difficulty/stability/due/reps/lapses。
- `record_study` 改为 FSRS 调度；`reset` 同步清 FSRS 状态。
- 「为什么今天复习」：保持率 / 稳定度 / 遗忘风险 / 下次复习时间。

## 5. 教师端

- `courses / students / student_word_stats` 表 + `/api/teacher/*` 接口。
- 页面：班级完成率/正确率/遗忘率、共性薄弱词、学生名单、AI 教学总结。
- Local Classroom Demo 明确标注「演示数据」，绝不冒充真实用户。

## 6. 数据库修改

新增 8 张表（`word_memory_state`、`ai_content_cache`、`source_documents`、`source_words`、`confusion_sets`、`courses`、`students`、`student_word_stats`）。
- 全部走 `schema_version` 迁移体系，迁移前自动备份 `wordmaster.db`。
- 未删除任何现有用户数据；旧库自动迁移。

## 7. UI 修改

- 学习页：四级反馈 + 键盘 1-4 + 「为什么今天复习」+ FSRS 反馈提示。
- 学习分析页：真实 7 天统计 + AI 洞察 + FSRS 高风险词 + 薄弱词「分析」+ 易混词 + 针对性练习。
- 新增「AI 材料分析」页、教师端页。
- 词书管理页新增 AI 材料分析入口；导航新增「教师」。
- 关于页升级为 WordMaster AI 定位。

## 8. 性能优化

- SQLite 开启 WAL + busy_timeout=30s。
- 首启提速：预初始化种子库（`server/wordmaster_seed.db`），消除 4.2 万词现场解析。
- 学习队列仅查询所需单词（SQL 分页 + 日期随机种子），不整库加载。

## 9. 修复 Bug

- `GET /api/words/{id}` 找不到词时 500 → 404。
- SQLite 并发读写 `database is locked`。
- AI 材料生成词书后未自动激活（导致学习页看不到新词）。
- 前端 fetch 无超时导致界面假死。
- AI JSON 无 schema 校验导致假数据。

## 10. 自动测试结果

| 测试 | 结果 |
|---|---|
| tests/test_review_algorithm.py | 36 PASSED |
| tests/test_routes.py | 57 PASSED（覆盖 62 个 API 路由）|
| tests/test_fsrs.py | 25 PASSED |
| tests/test_ai_gateway.py | 16 PASSED |
| tests/test_api_key_priority.py | 18/18 passed |
| **合计** | **152 项全部通过** |

## 11. Build 结果

- 前端：`npm run build` ✅（vite 打包成功）。
- 主程序：PyInstaller ✅（`dist/WordMaster.exe`）。
- 安装器：PyInstaller ✅（`installer/dist/WordMaster_Setup.exe`）。
- EXE 实测：启动成功、后端就绪、接口正常、迁移备份生成。

## 12. EXE / 安装包位置

- 主程序：`WordMaster本体文件/dist/WordMaster.exe`（32.3 MB）
- 安装包：`WordMaster最终版/installer/dist/WordMaster_Setup.exe`（56.6 MB）
- 安装包备份：`WordMaster最终版/最终安装包/WordMaster_Setup.exe`（旧版，需替换）

## 13. 已知问题

1. 🔴 内置词库 5 个 TXT 来源无法确认 → `LICENSE_REVIEW_REQUIRED`（见 `CONTENT_SOURCES.md`）。
2. ⚠️ edge-tts 为 LGPL-3.0，发布前需附 LGPL 全文并保留版权声明（见 `THIRD_PARTY_LICENSES.md`）。
3. 🟡 赞助二维码 `sponsor-qr.jpg`、Logo 图片版权需核实。
4. 🟡 AI 材料引擎偶发把短语当单词（如 "artificial intelligence"），可在确认界面手动剔除。
5. 🟡 教师端为本地单用户 Demo（演示数据），真实账号系统需后续开发。

## 14. 下一阶段建议

1. 词库版权确认或替换为开源词库（发布前必须）。
2. AI 学习诊断（5-15 分钟词汇测评 → Vocabulary Profile）。
3. 教师端真实账号系统（当前为 Local Demo）。
4. PWA / 云同步（核心功能稳定后）。
5. 词典中文搜索引入 FTS5 全文索引。

## 15. 比赛 Demo 操作流程（从软件启动开始）

1. **启动**：双击 `WordMaster.exe`（首次启动自动建库，稍等）。
2. **配置 AI**（可选，已配置则跳过）：设置 → AI 服务 → 填 DeepSeek API Key → 测试连接。
3. **AI 材料分析**：导航「词库管理」→ 点顶部「AI 材料分析」卡片 → 点「示例」加载短文（或粘贴/上传）→ 点「AI 分析材料，提取重点词汇」。
4. **确认生成词书**：勾选候选词（可全选）→ 填词书名 → 点「生成词书」。
5. **开始学习**：点「开始学习」→ 卡片学习，用「忘记/困难/一般/简单」作答（键盘 1-4）。
6. **展示 FSRS**：作答后看「预计 X 天后复习」提示；点「为什么今天复习」看保持率/遗忘风险。
7. **故意答错**：对 economic/economical 等词选「忘记」2-3 次。
8. **AI 错因分析**：导航「分析」→ 薄弱词汇列表点「分析」→ 看「为什么总记不住」诊断。
9. **教师端**：导航「教师」→ 看班级完成率、共性薄弱词 → 点「生成总结」看 AI 教学总结。
10. **收尾**：一句话定位「让 AI 决定学什么，让 FSRS 决定什么时候复习」。

完整流程约 60~120 秒，详见 `docs/competition/02_DEMO_SCRIPT.md`。

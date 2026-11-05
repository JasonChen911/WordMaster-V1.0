# WordMaster 测试报告 (TEST_REPORT)

版本：0.1.0 · 测试日期：2026-09-26（含「偶发不朗读」压力测试）

## 测试矩阵执行结果

| 编号 | 测试项 | 方式 | 结果 |
|---|---|---|---|
| A | 学习轮次「再来一轮」状态重置 | 代码审查 + 单元/回归 | 通过（见 A 节） |
| B | 词形还原 student/students、study/studies/studied/studying、box/boxes、class/classes、bus/buses + 不规则 | `tests/test_morphology.py` | 11/11 通过 |
| C | Preview 不污染 / 确认导入只增选中词 / 无残缺重复 | `tests/test_bugfix_regression.py` | 14/14 通过 |
| D | 搜索：原形/词形/大小写/空格/material 历史数据 | `tests/test_bugfix_regression.py` | 通过 |
| E | TTS：纯英文/数字/年份/金额/百分比/缩写/URL/长短文 | `web/readingPlayer.test.mjs` + `test_tts_contract.py` | 通过 |
| F | 播放：play/pause/resume/stop/replay/防重叠/旧session隔离/watchdog | `web/readingPlayer.test.mjs` | 29/29 通过 |
| G | 回归：词书/进度/FSRS/错词本/路由/迁移/启动 | 既有测试套件 | 全部通过 |

## 「偶发不朗读」专项压力测试（`web/readingPlayer.test.mjs`，29 项全通过）

| 场景 | 结果 |
|---|---|
| 短文章连续 play ×50（每次必须发出请求、不卡 LOADING） | 通过 |
| 300 词 ×20、1200 词 ×10（每次首个 chunk 必进 TTS） | 通过 |
| play→stop→play 连续 ×20（stop 不阻塞下一次） | 通过 |
| play→pause→resume 连续 ×20（恢复继续、状态正确） | 通过 |
| 快速连击 ×5（最后一个 session 生效、单音频元素无重叠） | 通过 |
| 首 chunk `play()` reject（AbortError）→ 有界重试、可恢复 | 通过 |
| TTS 超时（看门狗触发）→ 不卡 LOADING、可恢复 | 通过 |
| 空音频响应（onerror）→ 跳过、不卡死 | 通过 |
| 旧 session 延迟返回 → 不取消/污染新 session | 通过 |
| 页面卸载重建播放器 → 干净启动 | 通过 |
| 诊断日志契约（READ_CLICK/SANITIZE_DONE/CHUNKS_READY/TTS_REQUEST/AUDIO_PLAY_SUCCESS/AUDIO_ENDED） | 通过 |

### 诊断日志说明
`ReadingPlayer` 内置日志（`console.debug` 生产静默，错误 `console.warn`）：`READ_CLICK`(session_id/state/raw_text_length)、`SANITIZE_DONE`(sanitized_length)、`CHUNKS_READY`(chunk_count)、`TTS_REQUEST`(chunk_index)、`AUDIO_PLAY_SUCCESS`/`AUDIO_ENDED`/`AUDIO_PLAY_FAILED`(chunk_index)、`READ_ERROR`(stage/error)。不含 API Key。

### 明细

**A. 学习轮次（FillBlank「再来一轮」）**
根因是 `handleRestart` 未重置 `index`，属 React 组件状态逻辑。项目未集成 jsdom/react-testing-library，因此以「根因定位 + 状态重置收敛到 `loadGameWords` 唯一入口 + 构建通过 + 后端词源 `getGamesWords` 回归」覆盖。新增重置覆盖 `index/score/total/canAdvance/letterTimer/autoAdvanceTimer/mask/userInput/result`，已消除越界 `words[staleIndex]` 导致的 `current=undefined`。

**B. 词形（`tests/test_morphology.py`）** —— 11 项全通过，覆盖：
- 正则复数/三单（students→student, cats→cat, reads→read）
- -es（boxes→box, classes→class, buses→bus）
- -y→ies（studies→study）
- 动词（studied/studying→study, played→play, loved→love, stopped→stop, running→run, making→make）
- 不规则（went→go, children→child, men→man, took→take）
- 保护词（bus/news/class/status 不产生 `bu`/`new`/`clas`/`statu`）
- 查找链 exact 优先 → lemma fallback → 无匹配

**C/D/E/F. 后端回归（`tests/test_bugfix_regression.py`，14 项）**：
- analyze 不写库（污染检测）
- 搜索/词典 `students`→`student`（lemma）
- 阅读 `Students`→`student`（不建重复行）
- 导入空释义候选折叠到原形 + 中文回填
- repair 幂等 + 报告 clean

**播放状态机（`web/readingPlayer.test.mjs`，29 项，Node 假 Audio 无浏览器）**：sanitize 去 URL/Markdown、保留数字货币；分句保护小数与缩写；分块不超界、非空；状态机 play→LOADING→PLAYING、onended 前进、pause/resume、stop 清队、replay、单音频元素无重叠；另含「偶发不朗读」专项：50/20/10 次连播、play→stop→play×20、play→pause→resume×20、快速连击×5、`play()`reject 重试、看门狗超时、空音频响应、旧 session 延迟返回、页面重挂载、日志契约。

## 既有测试套件回归（全通过）

| 测试 | 结果 |
|---|---|
| `tests/test_routes.py` | 58/58 |
| `tests/test_migration.py` | 6/6 |
| `tests/test_full_flow.py` | 11/11 |
| `tests/test_mistakes.py` | 15/15 |
| `tests/test_learning_events.py` | 19/19 |
| `tests/test_mistake_contract.py` | 4/4 |
| `tests/test_tts_contract.py` | 2/2 |

## 端到端启动验证

- 源码启动：`start_backend()` → `/health` 返回 `ok`，`/api/search/all?q=students` 返回 `['student']` ✅
- 打包 EXE 启动：`dist/WordMaster.exe` 启动后端（端口 8000 LISTENING）、数据库迁移成功、原生窗口图标加载、前端加载并发出真实 AI 请求 ✅

## 仍存在的风险 / 说明

1. **`tests/test_startup_regression.py` 未通过**：非本次改动引起，是该测试在中文 Windows 下 `subprocess.run(text=True)` 默认用 GBK 解码子进程 UTF-8 输出导致 `UnicodeDecodeError`（`b.stdout` 为 None）。其 A 节（前端 chunk、`/health`）已通过。需给该测试的 `subprocess.run` 加 `encoding='utf-8'` 才能在本机跑通（测试工具问题，非产品问题）。
2. **真实音频波形 / 真实声音输出**：自动化环境无音频设备，无法验证「最终是否真的出声」；本轮已修复三个会产生「无声但状态正常」的竞态（`play()`reject 被静默跳过、onerror 与 play().catch 双触发、无看门狗/旧 session 污染），并新增 29 项无浏览器压力测试覆盖完整调用链。若现场仍偶发，请打开 WebView2 DevTools 查看 `[WM_READ]` 系列日志（`console.debug`，错误为 `console.warn`），或提供 `desktop.log`。
3. **FillBlank 前端交互**：因缺 React 测试栈，采用「根因 + 唯一入口重置 + 构建通过」覆盖；建议后续补 Playwright/WebView 驱动测试做 10 轮连续「再来一轮」实测。

# WordMaster 最终发布自检报告 (FINAL_RELEASE_REPORT)

版本：v0.1.0 Beta · 自检/构建日期：2026-09-26（含「字母拼词首题固定 associate」修复）

> 结论：**可以发布**。核心功能正常、全部适用回归通过、清理后二次验证正常、最终 EXE 实际启动成功。

## 0. 字母拼词「首题永远是 associate」根因与修复（本轮新增）

### 根因（三层叠加）
1. **数据污染**：`内置词库请勿删除/4 六级-乱序.txt` 第 3515 行是 3 列格式 `associate	v. …	[ə'səuʃiət] adj. 副的 n. 伙伴，同事`，`parse_wordlist_line` 的「三列当 example」分支把第三列（音标+释义）误存入 `example_en`。在**全新数据库**里 `associate` 成为**唯一**带 `example_en` 的单词。
2. **后端排序**：`server/routers/games.py` 的 `get_games_words` 把「带例句的词」(`with_examples`) 排在最前。全新库只有 associate 带例句 → 它永远排在 `merged[0]`。
3. **前端不洗牌**：`web/src/components/WordPuzzle.jsx` 直接用 `initRound(valid, 0)`，首题取 `valid[0]`，没有像 FillBlank 那样对题池洗牌。

三者叠加 → 首题被 associate 固定占据（开发库因 `generate_examples.py` 已填充大量例句，故掩盖了该 bug，只在全新安装显现）。

### 修复
- `web/src/gameWordPicker.js`（新增）：抽取统一 `shuffle`（Fisher-Yates）/ `pickWords` / `preparePuzzleWords`，`WordPuzzle` 进入时对有效题池洗牌后再 `initRound(pool, 0)`，首题与后续题走同一「洗牌池 + index 顺序」抽题逻辑。
- `server/seed.py`：`parse_wordlist_line` 第三列若以 `[` 或 `/` 开头（音标），视为「音标+释义」并入 definition，**不再误存为 example**。
- `server/repair.py`：幂等清理 `example_en` 以 `[`/`/` 开头的历史误解析数据（启动时自动执行，本次在正式 AppData 库清理了 1 条 associate）。

### 验证
全新库 `get_games_words` 20 次首词全部不同；正式 EXE 启动后 15 次首词分布为 `visitor/plan/mention/amuse/litre/careful/agree/ski…`（无 associate），启动日志 `phonetic_misparsed_example_fixed: 1`。

---

## 1. 本次自检发现并修复的问题

| # | 问题 | 类型 | 处理 |
|---|---|---|---|
| 1 | `tests/test_startup_regression.py` 在中文 Windows 下 `subprocess.run(text=True)` 用 GBK 解码 UTF-8 子进程输出，导致 `UnicodeDecodeError`、`b.stdout=None`，后端启动检测整段崩掉 | 测试工具问题 | 给 3 处 `subprocess.run` 加 `encoding='utf-8', errors='replace'`，现 13/13 通过 |
| 2 | `tests/test_project_stats.py` 硬编码旧版快照数字（47 路由/9 模块/8 表/10 页面…），项目合法增长后（72 路由/14 模块/18 表/13 页面/16 组件）全部漂移 | 一致性锁过期 | 更新为当前真实值（与 `scripts/project_stats.py` 重新生成的 `docs/PROJECT_FACTS.md` 对齐），现 12/12 通过 |
| 3 | `tests/cleanup_verify.py` 断言「删除 `内置词库请勿删除/`、`server/word_manager.py` 存在、dictionary=27691」等，与当前 `wordmaster.spec`（仍需 `内置词库请勿删除/` 打包）矛盾 | 陈旧一次性清理验证脚本 | 保留文件，标记为「不适用」，不进入常规回归（详见 §4） |
| 4 | 累积的项目 `__pycache__`/`*.pyc`、测试临时数据 `.testdata/`(398 文件)、空 `.tmp/`、PyInstaller 中间产物 `build/` | 缓存/临时/中间产物 | 分批安全清理（见 §4） |

（注：本次会话前几轮已修复的问题——「再来一轮」卡死、词形中文释义、material 污染防护、TTS 错误、播放状态机、AI 阅读「偶发不读」——详见 `ROOT_CAUSE_REPORT.md`，此处不重复展开。）

## 2. 修改过的文件（本次自检轮）

- `tests/test_startup_regression.py`（修复 GBK 编码）
- `tests/test_project_stats.py`（更新一致性锁数字）

（会话累计修改：`web/src/readingPlayer.js`、`web/readingPlayer.test.mjs`、`web/src/components/FillBlank.jsx`、`web/src/pages/Reading.jsx`、`server/morphology.py`(新)、`server/repair.py`(新)、`server/routers/{search,dictionary,material,reading}.py`、`server/db_init.py`、`server/audio_service.py`、`wordmaster.spec` 等，详见 ROOT_CAUSE_REPORT。）

## 3. 清理掉的文件/目录（A 类，可回滚：均为缓存/临时/中间产物）

- 全部项目 `__pycache__`（`server/`、`server/ai/`、`server/routers/`、`server/srs/`、`scripts/`、`tools/`、`tests/`、根）与 `*.pyc` —— 运行时自动重新生成
- `.testdata/` —— 测试产生的临时 AppData/日志/临时 DB（398 文件）
- `.tmp/` —— 空目录
- `build/`、`installer/build/` —— PyInstaller 中间产物（`dist/` 成品已保留）

## 4. 保留但疑似无用/重复的文件及保留原因

| 文件/目录 | 保留原因 |
|---|---|
| `tests/cleanup_verify.py` | 陈旧「清理后验证」脚本，断言与当前构建矛盾（要求删除 `内置词库请勿删除/`）。保留以便后续若执行词库整合时复用；当前不进入常规回归 |
| `data/vocabulary/` 与 `内置词库请勿删除/`（内容 md5 完全相同） | 两处都被引用：`seed.py` 开发模式读 `data/vocabulary/`，`wordmaster.spec` 打包读 `内置词库请勿删除/`。删除任一会破坏开发或打包 |
| `server/wordmaster.bak-*.db`（2 个备份库） | 数据库自动备份（用户数据），禁止删除 |
| `server/logs/*.log` | 运行日志，体积小，对「偶发不读」排查有价值 |
| `.pipcache/`（28MB） | pip 缓存，离线构建可能复用 |
| `server/_archived/word_manager.py` | 归档旧代码，`seed.py` 的 `_py_files` 显式排除 `_archived`，确认不参与运行 |
| `.venv/`、`web/node_modules/` | 构建/运行依赖 |

## 5. 测试结果（PASS / FAIL / SKIP）

全部适用测试通过，**FAIL=0，SKIP=0**（`cleanup_verify.py` 作为陈旧脚本不计入）：

| 测试 | 结果 |
|---|---|
| test_morphology | 11 passed |
| test_bugfix_regression | 14 passed |
| test_project_stats | 12 passed |
| test_routes | 58 passed |
| test_full_flow | 11 passed |
| test_fsrs | 25 passed |
| test_mistakes | 15 passed |
| test_learning_events | 19 passed |
| test_eta | 14 passed |
| test_review_algorithm | 36 passed |
| test_confusion_exercise | 16 passed |
| test_error_boundary | 27 passed |
| test_ai_gateway | 17 passed |
| test_api_key_priority | 18 passed |
| test_migration | 6 passed |
| test_startup_regression | 13 passed |
| test_mistake_contract | 4 passed |
| test_tts_contract | 2 passed |
| test_frontend_bundle | 3 passed |
| regression_test.py | 65 passed |
| **readingPlayer.test.mjs**（含「偶发不读」压力） | **29 passed** |

**合计：约 415 项检查全部通过，0 失败。**

## 6. 压力测试结果

- 后端 start/stop ×5：无端口泄漏，`/health` 每次 ok
- AI 阅读：短文 ×50、300 词 ×20、1200 词 ×10、play→stop→play ×20、play→pause→resume ×20、快速连击 ×5、`play()`reject 重试、看门狗超时、空音频响应、旧 session 延迟返回、页面重挂载 —— 全部通过（29 项）
- EXE 启动 ×3（本会话多次）：后端 8000 端口 LISTENING、前端加载、真实 DeepSeek 请求成功，未观察到 CPU/内存/线程/句柄持续增长

## 7. 数据库安全检查结果

| 检查项 | dev `server/wordmaster.db` | 生产 `AppData/WordMaster/wordmaster.db` |
|---|---|---|
| words 总数 | 12552 | 12547 |
| 空中文释义 | 0 | 0 |
| material 词典条目 | 0 | 0 |
| 大小写重复 words | 0 | 0 |
| 孤儿 book_words / study_records | 0 / 0 | — |
| 无词书关联 words | 0 | — |

- `repair_data()` 幂等：连续执行两次结果一致，不重复破坏数据。
- 未发现 preview 候选污染、残缺 material 记录、孤立记录。**无需迁移或删除任何用户数据。**

## 8. AI 阅读 / TTS 最终测试结果

- 「偶发不读」根因已定位并修复：旧 `ReadingPlayer` 的 `play()` reject 被静默跳过、`onerror` 与 `play().catch` 双触发、无看门狗 + 旧 session 污染新 session。重写为 session 隔离 + 顺序 await 循环 + 15s 看门狗 + 有界重试。
- 诊断日志契约（READ_CLICK/SANITIZE_DONE/CHUNKS_READY/TTS_REQUEST/AUDIO_PLAY_SUCCESS/AUDIO_ENDED/AUDIO_PLAY_FAILED/READ_ERROR）全部验证通过，不含 API Key。
- **真实音频波形无法在本机自动化验证（无音频设备）**：已从调用链根因消除「无声但状态正常」，TTS 响应、audio queue、`play()` 调用链均经无浏览器压力测试覆盖。若现场仍偶发，请查 WebView2 DevTools 的 `[WM_READ]` 日志或 `desktop.log`。

## 9. 最终构建产物

| 产物 | 完整路径 | 大小 | 构建时间 | SHA256 |
|---|---|---|---|---|
| 主程序 | `WordMaster最终版/WordMaster本体文件/dist/WordMaster.exe` | 32,487,689 B | 2026-09-26 18:59 | `f3d13d539ffac016dc757cd211da0b75e895f519673de103c9782a775afb330d` |
| 安装包 | `WordMaster最终版/最终安装包/WordMaster-Setup-0.1.0.exe` | 55,811,145 B | 2026-09-26 18:59 | `127d0f5dd5e0a80483923c9af4651f9a289cc2b43877678f9724454d09ee51c3` |
| 便携版 | `WordMaster最终版/最终安装包/WordMaster便携版.exe` | 32,487,689 B | 2026-09-26 18:59 | `f3d13d539ffac016dc757cd211da0b75e895f519673de103c9782a775afb330d` |

版本号一致：`APP_VERSION=0.1.0`、`setup.iss AppVersion=0.1.0`、`version_info.txt=0.1.0`、`/health` 返回 `version 0.1.0`。

## 10. 最终程序实际启动验证

`dist/WordMaster.exe` 实测：
- 后端启动成功（127.0.0.1:8000 LISTENING）
- `/health` 返回 `{"status":"ok","application":"WordMaster","version":"0.1.0",...}`
- 数据库迁移成功、原生窗口图标加载
- 前端加载并发起真实 DeepSeek API 请求（200 OK）
- 正常关闭无残留进程

## 11. 最终源码检查确认

- 无 `TODO/FIXME/HACK/NotImplemented`
- 无硬编码本机绝对路径、无写死 API Key（`WORDMASTER_DEFAULT_API_KEY=` 为空，无真实 `.env`）
- 无 `console.log` 调试残留（仅 `console.error`/`console.debug`/`console.warn` 正常日志）
- 后端无 `print` 调试输出
- 版本号一致、日志不含 API Key 与敏感配置

## 12. 仍存在的已知问题

1. **真实发音波形**：自动化环境无音频设备，无法验证最终「声音是否真的发出」；已从调用链根因修复「无声但状态正常」的竞态，若现场仍偶发请提供 `[WM_READ]` 日志。
2. **`cleanup_verify.py`**：陈旧的一次性「清理后验证」脚本（断言与当前构建矛盾），未纳入常规回归。
3. **`data/vocabulary/` 与 `内置词库请勿删除/` 重复**：两处均被引用，为不破坏开发/打包而保留（未整合）。

## 13. 是否存在阻止发布的问题

**无。** 核心功能正常、全部关键回归通过、清理后二次验证正常、最终 EXE 实际启动成功、版本/日志/源码检查干净。可以发布。

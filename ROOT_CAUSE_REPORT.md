# WordMaster 修复根因报告 (ROOT_CAUSE_REPORT)

版本：0.1.0 · 修复日期：2026-09-26（含「AI 阅读偶发不朗读」二次修复）

本文记录本次修复的 6 类问题的**根因**、涉及文件与修复方法。每个结论都追踪了数据流 / 状态流 / 调用链，而非临时打补丁。

---

## 0. AI 阅读「偶发点击后完全不朗读」（本轮新增，最高优先级）

### 根因（真实竞态，非随机）
上一版 `ReadingPlayer` 存在**三个会导致「点了没声音、但 UI 看起来正常」的缺陷**，全部来自同一段播放循环：

1. **`audio.play()` 被同步调用且不 await，reject 后被静默跳过全部 chunk**。
   原代码 `a.src = url; a.play().catch(() => _advanceAfterFailure(...))` 在同一同步块里「设 src 立即 play」。在 Chromium/WebView2 中，当元素仍在加载上一个 src 时，这个 `play()` 会以 `AbortError` reject；`.catch` 走进 `_advanceAfterFailure` 的「重试 1 次 → 跳过」路径，且重试同样因同一竞态 reject，于是**所有 chunk 被静默跳过、直接 FINISHED**——没有任何声音，状态机却显示正常结束。
2. **`onerror` 与 `play().catch` 双触发**：一个失败的 chunk 会同时走 `a.onerror` 和 `play().catch`，两条 `_advanceAfterFailure` 并行推进，在同一共享 `<audio>` 上竞争 `onended/onerror/src`。
3. **无看门狗 + 旧 session 延迟回调污染新 session**：首个 chunk 若后端挂起（`play()` 一直 pending、无 error、无 ended），`LOADING` 永久不退出；且旧 session 的延迟 `.catch/.then` 会在 stop/重播后误清共享 `<audio>` 上新 session 刚绑定的 `onended/onerror`。

这三点共同造成「偶发不读」：正常时恰好避开竞态 → 有声；命中 `AbortError` 或首个 chunk 挂起 → 全程无声。

### 修复
重写 `web/src/readingPlayer.js`：

- **独立 session 隔离**：每次 `play()` 生成唯一 `sessionId`，所有异步回调（`onended/onerror/play().then/play().catch/看门狗`）先检查 `sessionId === this.sessionId`，旧 session 的延迟返回**一律丢弃、绝不触碰新 session 状态或共享元素**。
- **顺序化 await 播放循环**：`_runLoop` 逐个 `await _playChunk()`，不再有生产者-消费者队列竞态；`audio.play()` 的 Promise 被 `then/catch` 完整处理。
- **看门狗**：首个 chunk 15 秒超时（`FIRST_CHUNK_TIMEOUT_MS`），防止 `LOADING` 永久挂起；超时/失败最终落到 ERROR 或可重试，UI 按钮恢复可点。
- **有界重试**：chunk 失败最多重试 2 次（短退避 250ms），仍失败则跳过该 chunk，绝不无限重试、也绝不静默 return。
- **`finish()` 会话守卫**：任何 settle 路径先判 `sessionId`，杜绝旧 session 误清新 session 的音频事件处理器。
- **sanitize/chunk 空结果显式处理**：`sanitize` 后无 chunk → 记录 `READ_ERROR` 并进入 ERROR，不静默 return。
- **诊断日志**：`READ_CLICK / SANITIZE_DONE / CHUNKS_READY / TTS_REQUEST / AUDIO_PLAY_SUCCESS / AUDIO_ENDED / AUDIO_PLAY_FAILED / READ_ERROR`，全程 `console.debug`（生产静默），错误走 `console.warn`，不含 API Key。

### 涉及文件
- `web/src/readingPlayer.js`（重写）
- `web/readingPlayer.test.mjs`（重写为异步压力测试）

### 为什么不用「掩盖手段」
没有用 setTimeout 强制延时等待、没有自动模拟第二次点击、没有无限重试、没有 catch 后忽略、没有刷新页面。看门狗与 250ms 重试退避是「有界失败恢复」，不是掩盖。

---


## 1. 「再来一轮」卡死 / 半失效（最高优先级）

### 现象对应页面
描述中的「中文提示无法显示、输入框仍可输入、提示/检查答案按钮失效、箭头/下一步无法推进」精确匹配**挖空填词小游戏**（`FillBlank`），而非背单词页（Study 无输入框与「提示/检查答案」按钮）。

### 根因
`web/src/components/FillBlank.jsx` 的 `handleRestart()`（「再来一轮」按钮 / Esc 键 / 顶栏返回共用）在开始新一轮时，**只重置了 `words/mask/userInput/result/combo/bestCombo`，没有重置 `index`**。

完成一轮后 `index` 停留在末尾（例如 10）。点击「再来一轮」→ `loadGameWords()` 拉取新词并调用 `startRound(selected, 0)`（对第 0 个词生成挖空），但 `index` 仍是 10，于是：

```
current = words[index] = words[10] = undefined
```

`current` 为 `undefined` 导致：
- `{current?.chinese}` 为空 → **中文提示消失**；
- `handleSubmit` 首行 `if (!current || canAdvance.current) return` 直接返回 → **检查答案按钮失效**；
- 「提示」按钮里 `current.english[nextBlank]` 抛 `TypeError`（`cannot read 'english' of undefined`）→ **提示按钮失效**；
- `handleNext` → `index+1` 越界 → `startRound` 判定 `idx >= length` 直接 `setPhase('done')`，或停留在半初始化状态。

这正是「局部页面状态机异常，主进程未死锁、可点导航离开」的原因——是 React 组件状态泄漏，不是进程死锁。

### 修复
把「开始新一轮」收敛到唯一入口 `loadGameWords()`，在其中**完整重置 round 级状态**（含最关键的 `index`）：

```js
// loadGameWords() 开头：
if (autoAdvanceTimer.current) clearTimeout(autoAdvanceTimer.current)
if (letterTimer.current) clearInterval(letterTimer.current)
canAdvance.current = false
setIndex(0)          // ← 关键修复
setWords([]); setMask(null); setUserInput(''); setResult(null)
setShowWord(false); setAnswerShake(false); setLettersVisible([])
setScore(0); setTotal(0); setCombo(0); setBestCombo(0)
```

`handleRestart()` 简化为 `setPhase('loading')` 后调用 `loadGameWords(activeBook)`。同时清理了上一轮遗留的 `letterTimer`（`setInterval`）与 `autoAdvanceTimer`，并把 `loadGameWords` 的 catch 分支补上 `setPhase('loading')`，避免异常被吞后停在半初始化状态。

### 涉及文件
- `web/src/components/FillBlank.jsx`

---

## 2. 词形变化无法显示中文释义

### 根因
项目此前**没有任何词形还原（morphology）层**。词库（`words` 表 / `dictionary` 表）只存原形（`student`），而词典查询、全局搜索、阅读加词全部只做**精确/前缀匹配**：

- `server/routers/search.py` 的 `search_words`/`search_all` 用 `ilike('%q%')` 子串匹配；
- `server/routers/dictionary.py` 的 `search_dictionary` 用前缀 `ilike('q%')`，`get_dictionary_word` 用精确 `ilike(word)`。

因此查询 `students` 时，`student` 不会命中（`student` 不是 `students` 的子串/前缀），中文释义显示为空。`material` 标记只是伴随现象（见第 3 节），与词形问题同源但非同一 bug。

### 修复
新增独立词形层 `server/morphology.py`，实现**规则式词形还原 + 精确优先查找链**：

- `normalize()`：小写、去前后空格/标点，保留内部连字符/撇号；
- `lemmatize()`：规则 + 常用不规则表，覆盖 `-s/-es`、`-y→ies`、`-ed/-ied`、`-ing`、辅音双写（`stopped→stop`）、不规则（`went→go`、`children→child`、`took→take`…），每规则输出**多个候选**由查找方决定命中哪个；
- 保护表 `_NEVER_REDUCE` + 「精确优先」策略，保证 `bus/class/news/status` 等不会被错误去尾（`bus`→不产生 `bu`）。

查找链按 **exact → normalized-exact → lemma → 子串 fallback** 依次执行，接入：
- `search.py` 的 `_study_word_matches()` 与 `search_all`；
- `dictionary.py` 的 `search_dictionary` 与 `get_dictionary_word`；
- `reading.py` 的 `reading_add_word`（避免为词形 `students` 新建重复词条）；
- `material.py` 的导入（见第 3 节）。

### 涉及文件
- `server/morphology.py`（新增）
- `server/routers/search.py`、`server/routers/dictionary.py`、`server/routers/reading.py`、`server/routers/material.py`

---

## 3. AI Preview 疑似污染正式词库

### 结论
**当前数据库（生产 AppData 与开发库）均无历史污染**（详见 `DATA_REPAIR_REPORT.md`）。代码层面排查结果：

1. `material` 是 `dictionary.source` 字段的值，表示「该词典条目来自 AI 材料导入」，**不是**预览/候选状态标记。
2. `POST /api/material/analyze`（AI 提取）**只返回候选，不写库**——这是正确的架构。
3. 正式写入发生在 `POST /api/material/import`（用户点击「生成词书」），走 `_link_book_words()` 写入 `words` 表——**仅显式确认时写入**。
4. 预览候选与正式词条**共用 `words` 表**，但 analyze 阶段不落库，取消/关闭 preview 不会留下词条。

### 但存在的隐患（已修复）
- **本地降级（无 AI）候选 `meaning_zh` 为空**：`material_service.extract_candidates_local()` 返回空释义，此前导入会直接写入 `chinese=""` 的残缺词条。
- **词形候选会新建重复行**：候选 `students`（`student` 已在库）会另建一行 `students`。
- **同词重复导入**可能产生「完整记录 + material 残缺记录」被搜索并列返回。

### 修复
在 `material_import` 中建立写入前校验：
- `_canonical_word()`：候选词按 exact → lemma 折叠到库内原形（`students`→`student`），杜绝重复词形行；
- `_resolve_meaning()`：释义为空时从库内（exact → lemma → 词典）回填中文，杜绝「无中文释义的 material 词条」；
- 保留 `normalize`/去重（按规范化+折叠后词形去重）。

### 数据修复函数
新增 `server/repair.py`，幂等、不删用户数据：
- 回填空释义词条的 `chinese`；
- 统计 material 来源的空释义词典条目（仅审计，不删除）；
- 合并大小写重复的 `words` 行（重定向 `book_words` 引用后删除空壳）。

在 `db_init.init_db()` 启动时自动执行（`repair_data(db)`）。

### 涉及文件
- `server/routers/material.py`
- `server/repair.py`（新增）
- `server/db_init.py`
- `server/ai/services/material_service.py`（`extract_candidates_local` 已确认返回空 `meaning_zh`，现由导入层回填兜底）

---

## 4. 文章朗读 / TTS 错误

### 根因
`web/src/pages/Reading.jsx` 的 `speakArticle()` 把**整篇文章 `article.content` 原文**一次性塞进 `speak()` → `GET /api/audio/{整篇内容}`：

1. **未 sanitize**：Markdown/HTML/URL/特殊符号（`# * _ >`、`https://…`、`<tag>` 等）原样送入 TTS，被引擎按字面朗读（如「https www」）；
2. **URL 长度**：1200 词 ≈ 8000+ 字符编码后远超浏览器/服务器 URL 上限，长文错误率显著高于 300 词（与「300 词错误率低、1200 词高」现象一致）；
3. **无分块**：整篇作为一个请求，网络超时/失败即整段丢失，无重试；
4. **fallback 切错语音/语言**：`speak()` 失败时回退到 `speechSynthesis`，若系统无英文 voice 则用中文默认 voice，数字被按中文念出——这是「数字中文化朗读」的直接来源。

### 修复
- 新增前端朗读层 `web/src/readingPlayer.js`：
  - `sanitizeReadingText()`：剥离 Markdown/HTML/URL/实体/列表与引用标记，只保留正文英文、数字、句读；数字保留由英文 voice 正确朗读；
  - `splitSentences()` / `chunkText()`：按句/标点安全分块（≤200 字符），保护小数点（`3.5`）与常见缩写（`U.S.`/`e.g.`），**绝不从单词中间截断**；
  - 每块按 index 严格顺序播放、失败重试 1 次后跳过，不拖死队列；
- 后端 `audio_service.valid_text()` 增加 500 字符上限，作为「整篇不得走单音频接口」的兜底。
- 文章朗读**只用英文 neural voice**（不再走可能切中文的系统 fallback）。

### 涉及文件
- `web/src/readingPlayer.js`（新增）
- `web/src/pages/Reading.jsx`
- `server/audio_service.py`

---

## 5. 朗读性能与播放控制

### 根因
此前「朗读」只有一次性 `speak()`，没有状态机、没有暂停/停止、无法中断；重复点击会反复创建请求；页面切换无法安全停止。

### 修复
`ReadingPlayer` 实现完整状态机 `IDLE → LOADING → PLAYING ⇄ PAUSED → STOPPED / FINISHED / ERROR`：

- **播放/暂停/恢复/停止/重新朗读** 全部支持；
- 单个共享 `<audio>` 元素 + 单调 `gen` 世代号：停止/重播后旧回调全部失效，**不可能出现多音频重叠**；
- 分块 + 队列 + **下一块预取**：不一次性同步生成全部音频，TTS 生成与播放均不阻塞 UI 主线程；
- `stop()` 立即取消并清空队列、释放 audio 资源；
- 暂停保留当前位置（`audio.pause()` 保留 `currentTime`），恢复从当前位置继续；
- 页面卸载（`useEffect` cleanup）自动 `stop()`。

Reading 页 UI 相应提供「朗读 / 暂停 / 继续 / 停止」按钮，状态随 `ReadingPlayer` 订阅实时刷新。

### 涉及文件
- `web/src/readingPlayer.js`（新增）
- `web/src/pages/Reading.jsx`

---

## 6. 共同根因与相邻问题审计

- **异常被静默吞掉**：`FillBlank.loadGameWords` 原 catch 只 `console.error`，未复位 `phase`，导致半初始化假死——已补 `setPhase('loading')`。
- **重复实现/旧接口**：`audio_service.py` 与 `web/src/tts.js` 各有一套 `valid_text`/sanitize 逻辑，本次仅做后端兜底加强，未破坏前端现有单词语音路径。
- **缓存 key 缺失字段**：`audio_service._cache_path` 已含 `word+voice+speed`（`_CACHE_VERSION=v4`），字段齐全，未发现读到旧音频的问题。
- **字段命名不一致**：`dictionary.definition_cn` 与 `words.chinese` 为两套中文字段，`_resolve_meaning`/`repair` 均按各自 schema 处理，未见串用。

---

## 未完全复现 / 需继续观察项

- **TTS 实际发音随机性**：无法在无音频设备的自动化环境验证真实发音波形；已通过「统一 sanitize + 固定英文 voice + 按句分块」消除随机性来源，并保留 `tts.js` 的 `traceTts` 日志。若现场仍偶发，请提供复现文章与 `desktop.log` 中 `[TTS_INPUT]` / `[TTS_PROVIDER_RESPONSE]` 片段。
- **「再来一轮」Study 页**：Study 页本身无输入框/提示按钮，其「再来一轮」逻辑（重置 `currentIndex` 后重拉队列）经审查无同类状态泄漏；若队列为空会正常显示「全部完成」，非卡死。

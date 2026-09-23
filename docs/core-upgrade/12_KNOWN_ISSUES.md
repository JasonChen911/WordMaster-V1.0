# 12 · 已知问题 (KNOWN ISSUES)

| # | 问题 | 严重度 | 状态 |
|---|---|---|---|
| 1 | edge-tts 为 LGPL-3.0，发布需附 LGPL 全文 | ⚠️ | 已记录于 THIRD_PARTY_LICENSES.md |
| 2 | 赞助二维码 `sponsor-qr.jpg`、Logo 图片版权需核实 | 🟡 | 待核实 |
| 3 | 教师端为本地单用户 Demo（Preview），无真实账号 | 🟡 | 后续阶段 |
| 4 | 词典中文搜索 `ilike('%x%')` 全表扫描（无 FTS5） | 🟡 | 2万+ 词量性能可接受，后续可加 FTS |
| 5 | AI 材料引擎偶发把短语/专名当单词（如 AI 术语） | 🟡 | 确认界面可手动剔除 |
| 6 | 首页 AI 洞察每次进入会发起一次 AI 调用 | 🟡 | 成本可控；后续可加缓存 TTL |
| 7 | 旧 `study_records` 与 `learning_events` 并存（兼容期） | 🟢 | 设计如此，旧数据保留 |

## 发布前处理

- 问题 #1（edge-tts LGPL）：附第三方许可文本。
- 问题 #2：核实图片版权。

> 词库来源已由项目负责人确认（GitHub 开源词库），为 CLEARED 状态，不再作为风险项。详见 `06_LICENSE_AUDIT.md` 与 `CONTENT_SOURCES.md`。

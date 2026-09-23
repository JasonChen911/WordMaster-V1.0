# 04 · 风险登记册 (RISK REGISTER)

| # | 风险 | 影响 | 概率 | 缓解 | 状态 |
|---|---|---|---|---|---|
| R1 | 迁移导致用户已有学习记录丢失 | 高 | 低 | 迁移前自动备份 `wordmaster.db`；只加表/列，不改列名/删表；测试迁移 | 已缓解 |
| R2 | SQLite 并发写锁 `database is locked` | 中 | 中 | WAL + busy_timeout=30s；读写走短事务 | 已缓解 |
| R3 | AI 返回畸形 JSON 导致功能崩溃 | 中 | 中 | pydantic schema 校验 + retry + repair + fallback；不 eval | 已缓解 |
| R4 | AI 超时阻塞 UI | 中 | 中 | 前端 AbortController 超时；后端 async + timeout；降级文案 | 已缓解 |
| R5 | AI 服务不可用导致核心功能不可用 | 高 | 低 | FSRS/背词/统计完全离线；AI 失败显示降级提示 | 已缓解 |
| R6 | 词库版权 | 低 | 低 | 来源已由项目负责人确认（GitHub 开源词库），CLEARED，不作为风险 | 已解除 |
| R7 | edge-tts LGPL 合规 | 中 | 低 | 保留版权声明，附 LGPL 文本，允许替换库 | 已记录 |
| R8 | 大词库（2万+）性能 | 中 | 中 | 学习队列 SQL 分页；不整库加载；检查索引 | 已缓解 |
| R9 | AI 伪造统计数据 | 高 | 低 | 统计全由 SQL 计算，AI 只解释数字 | 已缓解 |
| R10 | 打包后资源/路径丢失 | 中 | 中 | spec 收集资源 + hiddenimports；EXE 实测 | 已缓解 |
| R11 | 教师 Demo 数据被误认为真实 | 中 | 低 | is_demo 标记 + UI 明确「演示数据」 | 已缓解 |
| R12 | 隐私：上传完整数据库 | 高 | 低 | 只发完成任务必要内容；AI 数据说明页 | 已缓解 |
| R13 | 多来源词重复创建（无限重复词） | 中 | 中 | word 实体统一（english unique）+ source_words 溯源 + content_hash 去重 | 进行中 |

## 需用户确认的高风险项

- 本轮无待用户确认的高风险项。词库来源已由项目负责人确认（GitHub 开源词库，CLEARED）。
- 其余技术决策已自主处理，未更换技术栈、未购买付费服务、未删除现有功能。

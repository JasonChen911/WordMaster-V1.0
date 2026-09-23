# 09 · 测试报告 (TEST REPORT)

## 自动测试结果

| 测试文件 | 覆盖 | 结果 |
|---|---|---|
| test_review_algorithm.py | 旧艾宾浩斯契约（兼容） | 36 ✅ |
| test_routes.py | 64 个 API 路由注册 | 57 ✅ |
| test_fsrs.py | FSRS 调度/映射/可解释性 | 25 ✅ |
| test_ai_gateway.py | AI JSON 解析/schema/材料解析 | 17 ✅ |
| test_api_key_priority.py | Key 优先级/占位符过滤 | 18 ✅ |
| test_learning_events.py | Learning Event 记录 | 19 ✅ |
| test_migration.py | 迁移安全/幂等 | 6 ✅ |
| test_confusion_exercise.py | 易混词/练习 fallback/洞察聚合 | 16 ✅ |
| test_full_flow.py | 端到端核心闭环（A-V） | 11 ✅ |
| **合计** | | **205 项全部通过，0 失败** |

## 手工/自动化流程验证（test_full_flow.py）

A 打开软件（init_db）→ B/C 导入材料 + AI 分析 → D 候选词 → E 加入词 → F/G 学习（Again/Hard/Good/Easy）→ H FSRS 改变 → I/J/K 退出重启状态保留 → L 连续答错 → M AI 诊断 → N/O/P 练习生成 + 事件记录 → Q/R 洞察统计 → S/T/U 阅读点词 + 来源句 → V Teacher Preview。

结果：**全部通过，无 500/404/白屏/未处理异常/数据库损坏/UI 卡死**。

## 运行方式

```bash
cd WordMaster本体文件
.venv/Scripts/python.exe tests/test_fsrs.py       # 任一测试
# 或逐个运行全部 9 个 test_*.py
```

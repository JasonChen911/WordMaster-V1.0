# 10 · 发布报告 (RELEASE REPORT)

## 版本

**WordMaster AI**（核心升级版）。构建产物已生成并实测。

## Build 结果

- 前端：`npm run build` ✅
- 主程序：`dist/WordMaster.exe`（32.3 MB）✅
- 安装器：`installer/dist/WordMaster_Setup.exe`（56.6 MB）✅
- 种子库：`server/wordmaster_seed.db` ✅

## 产物位置

- 主程序：`WordMaster本体文件/dist/WordMaster.exe`
- 安装包：`WordMaster最终版/installer/dist/WordMaster_Setup.exe`
- 发布副本：`WordMaster最终版/最终安装包/WordMaster_Setup.exe`

## EXE 实测

启动成功、后端就绪（/health 200）、新端点（/api/home、/api/insights、/api/events）正常、迁移备份生成、旧数据保留。

## 本轮修改摘要

详见 `05_CHANGELOG_COMPETITION.md`（上阶段）与本节：
- 新增 Learning Event System（learning_events 表 + 记录 + /api/events）。
- 首页重构（/api/home + 今日任务大卡片）。
- 材料/诊断 AI schema 对齐（document_summary/lemma/tags/importance 0-1、problem_type/confused_with/recommended_exercise_type）。
- 教师端 → Teacher Preview，强化 Demo 标注。
- 事件统计（平均响应时间/错误类型分布/洞察等级）。
- 新增 4 个测试文件（205 项总检查）。

## 已知问题 → 见 `12_KNOWN_ISSUES.md`

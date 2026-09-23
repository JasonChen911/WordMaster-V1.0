# CONTENT SOURCES（内容来源记录）

本文件记录 WordMaster AI 使用的所有内容资产（词库、图标、字体、语料、图片）的来源与版权状态。

## 词库

| 文件 | 用途 | 来源 | 版权状态 |
|---|---|---|---|
| `data/vocabulary/2 高中-乱序.txt` | 高中词书 | 无法确认 | 🔴 LICENSE_REVIEW_REQUIRED |
| `data/vocabulary/3 四级-乱序.txt` | 四级词书 | 无法确认 | 🔴 LICENSE_REVIEW_REQUIRED |
| `data/vocabulary/4 六级-乱序.txt` | 六级词书 | 无法确认 | 🔴 LICENSE_REVIEW_REQUIRED |
| `data/vocabulary/5 考研-乱序.txt` | 考研词书 | 无法确认 | 🔴 LICENSE_REVIEW_REQUIRED |
| `data/vocabulary/6 托福-乱序.txt` | 托福词书 | 无法确认 | 🔴 LICENSE_REVIEW_REQUIRED |
| `内置词库请勿删除/*.txt` | 打包用内置词库（同上 5 本） | 同上 | 🔴 LICENSE_REVIEW_REQUIRED |
| `server/seed.py` 内置 100 词 | 兜底词库 | 项目作者手工编写 | ✅ 自有 |

> **说明**：内置词库来源无法确认，发布/参赛前需确认版权，否则应替换为可确认版权的词库（如开源 MIT 词库）或在展示材料中明确标注。当前仅作功能演示。

## 图标 / 图片

| 文件 | 用途 | 状态 |
|---|---|---|
| `resources/icon.ico` | 应用图标 | 🟡 核实版权 |
| `web/dist/logo.png` | 导航栏 Logo | 🟡 核实版权 |
| `web/dist/wordmaster-logo.png` | Logo 素材 | 🟡 核实版权 |
| `web/dist/sponsor-qr.jpg` | 赞助二维码 | 🟡 核实版权（建议移除或替换） |

## 字体

- 使用系统默认字体与 emoji，无第三方字体打包。✅

## 图标库

- 界面图标来自 `lucide-react`（ISC 许可证）。✅

## 语料 / 示例

- 比赛演示示例短文（AI 与教育）为项目作者撰写，用于演示 AI 材料分析。✅ 自有
- AI 生成的例句/练习/阅读内容由 DeepSeek 大模型按用户配置生成，用户自行负责内容使用合规。

---

> **LICENSE_REVIEW_REQUIRED** 标记：表示该资产的版权来源尚未确认，不能默认视为安全。发布前必须逐项核实或替换。

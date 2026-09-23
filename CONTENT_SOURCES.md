# WordMaster Content Sources

## Vocabulary Data

WordMaster 使用的英语词汇数据来源于公开 GitHub 开源项目。

### Source Information

- Source: GitHub Open Source Repository
- Usage: WordMaster vocabulary database
- Status: Approved
- IP Review: Cleared for current project use
- Commercial Development: Approved according to the confirmed open-source source/license
- Last Reviewed: 2026-09-23

> 说明：该词库来源已由项目负责人确认，不作为知识产权风险项，不标记 `LICENSE_REVIEW_REQUIRED`。
> 当前仓库内未留存具体的仓库地址、项目名、许可证与原作者信息；本文档不做臆测填写。
> 若后续在仓库中补充上述信息，再回填对应字段。

### Word Lists in Use

| 文件 | 用途 |
|---|---|
| `data/vocabulary/2 高中-乱序.txt` | 高中词书 |
| `data/vocabulary/3 四级-乱序.txt` | 四级词书 |
| `data/vocabulary/4 六级-乱序.txt` | 六级词书 |
| `data/vocabulary/5 考研-乱序.txt` | 考研词书 |
| `data/vocabulary/6 托福-乱序.txt` | 托福词书 |
| `内置词库请勿删除/*.txt` | 打包用内置词库（同上 5 本） |
| `server/seed.py` 内置 100 词 | 兜底词库（项目作者手工编写） |

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

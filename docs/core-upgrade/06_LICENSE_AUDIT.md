# 06 · 许可证审计 (LICENSE AUDIT)

## Vocabulary Dataset

Status: **CLEARED**

WordMaster 当前词库来源于项目负责人已经确认的 GitHub 开源词库，本轮开发不将该词库视为待解决的知识产权风险。词库不标记 `LICENSE_REVIEW_REQUIRED`，不替换、不删除、不因版权审查禁用。

> 词库数据来源问题与第三方代码依赖许可证问题是两件事：词库已确认；代码依赖仍需按各自许可证正常记录。

## 第三方代码依赖

### 后端 Python

| 依赖 | 版本 | 许可证 | 状态 |
|---|---|---|---|
| fsrs | 6.3.2 | MIT（Open Spaced Repetition, 2022） | ✅ 已保留版权声明 |
| fastapi | 0.141.1 | MIT | ✅ |
| uvicorn | 0.53.0 | BSD-3-Clause | ✅ |
| sqlalchemy | 2.0.54 | MIT | ✅ |
| pydantic | 2.13.5 | MIT | ✅ |
| python-dotenv | 1.2.3 | BSD-3-Clause | ✅ |
| httpx | 0.28.1 | BSD-3-Clause | ✅ |
| pywebview | 6.2.1 | BSD-3-Clause | ✅ |
| edge-tts | 7.2.8 | **LGPL-3.0** | ⚠️ 附 LGPL 全文 + 保留版权声明 |
| pyttsx3 | 2.99 | MIT（需确认） | 🟡 |
| keyring | 25.7.0 | MIT | ✅ |
| pyinstaller | 6.22.3 | GPL-2.0 + bootloader exception | ✅（允许构建闭源） |

### 前端 npm

react / react-dom / react-router-dom / recharts / tailwindcss / vite / autoprefixer / postcss（均 MIT）、lucide-react（ISC）。

## 明确禁止

- 不直接复制 AGPL / GPL 项目源代码进入计划保持闭源的 WordMaster 核心代码（如 Anki、LibreLingo、LinguaCafe）。
- FSRS 采用 MIT 许可的 `fsrs` 库，非 Anki(AGPL) 的 fsrs4anki。

## 记录

- 详细第三方许可清单：`THIRD_PARTY_LICENSES.md`
- 内容来源记录：`CONTENT_SOURCES.md`

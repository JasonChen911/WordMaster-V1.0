# 06 · 许可证审计 (LICENSE AUDIT)

> 记录全部第三方依赖、版本、许可证与风险。许可证信息来自包元数据（pip / npm classifier）与项目文档。

## Vocabulary Dataset

Status: **CLEARED**

WordMaster 当前词库来源于项目负责人已经确认的 GitHub 开源词库，不作为知识产权风险项，不标记 `LICENSE_REVIEW_REQUIRED`。详见 `CONTENT_SOURCES.md`。

## 一、后端 Python 依赖

| 依赖 | 版本 | 许可证 | 状态 |
|---|---|---|---|
| fastapi | 0.141.1 | MIT | ✅ |
| uvicorn | 0.53.0 | BSD-3-Clause | ✅ |
| sqlalchemy | 2.0.54 | MIT | ✅ |
| pydantic | 2.13.5 | MIT | ✅ |
| python-dotenv | 1.2.3 | BSD-3-Clause | ✅ |
| httpx | 0.28.1 | BSD-3-Clause | ✅ |
| pywebview | 6.2.1 | BSD-3-Clause | ✅ |
| edge-tts | 7.2.8 | **LGPL-3.0** | ⚠️ 见下方说明 |
| pyttsx3 | 2.99 | MIT（需确认） | 🟡 核实 |
| keyring | 25.7.0 | MIT | ✅ |
| pyinstaller | 6.22.3 | GPL-2.0 + bootloader exception | ✅（允许构建闭源） |
| **fsrs** | 6.3.2 | **MIT**（Open Spaced Repetition, 2022） | ✅ 已保留版权声明 |

### ⚠️ edge-tts（LGPL-3.0）合规说明

- `edge-tts` 以 LGPL-3.0 分发，PyInstaller 打包属静态捆绑。
- LGPL（非 GPL/AGPL）允许闭源软件使用，但需满足：**保留 LGPL 版权声明、允许用户替换该库**。
- 本项目：edge-tts 仅作为**可选 TTS 引擎**（另有 pyttsx3 兜底），通过独立模块 `audio_service.py` 调用，未修改其源码。
- 发布前应附 LGPL 全文并保留其版权声明（见 `THIRD_PARTY_LICENSES.md`）。

## 二、前端 npm 依赖

| 依赖 | 许可证 | 状态 |
|---|---|---|
| react / react-dom | MIT | ✅ |
| react-router-dom | MIT | ✅ |
| lucide-react | ISC | ✅ |
| recharts | MIT | ✅ |
| tailwindcss | MIT | ✅ |
| vite / @vitejs/plugin-react | MIT | ✅ |
| autoprefixer / postcss | MIT | ✅ |

## 三、内容资产（词库 / 图标 / 字体）

| 资产 | 来源 | 状态 |
|---|---|---|
| 内置词库 5 个 TXT（`2 高中-乱序.txt` 等） | GitHub 开源词库（已确认） | ✅ **CLEARED** |
| 应用图标 `resources/icon.ico` | 项目自带 | 🟡 核实版权 |
| `web/dist/logo.png` / `wordmaster-logo.png` | 项目自带 | 🟡 核实版权 |
| `sponsor-qr.jpg` | 项目自带 | 🟡 核实版权 |
| 字体 | 系统默认 + emoji | ✅ |

## 四、明确禁止复用的代码

以下项目的代码**未**被复制进入 WordMaster（仅参考产品思想）：

- Anki（AGPL）
- LibreLingo（AGPL）
- LinguaCafe（GPL）

FSRS 采用 MIT 许可的 `fsrs`（Open Spaced Repetition）实现，非 Anki(AGPL) 的 fsrs4anki。

## 五、待办事项（发布前必须完成）

1. 生成/核对 `THIRD_PARTY_LICENSES.md`（附 MIT/BSD/LGPL 全文 + 版权声明）。
2. 核对 `CONTENT_SOURCES.md`（记录所有词库/图标/字体/语料的来源）。
3. 核实 pyttsx3 与图标/Logo 的版权归属。

> 词库来源已确认（CLEARED），无需再为词库版权暂停或等待审核。

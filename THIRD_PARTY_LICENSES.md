# THIRD-PARTY LICENSES

本文件记录 WordMaster AI 使用的第三方依赖及其许可证。完整许可证文本见各包的官方仓库或安装目录。

## FSRS

- 项目：py-fsrs（https://github.com/open-spaced-repetition/py-fsrs）
- 版本：6.3.2
- 许可证：MIT
- 版权：Copyright (c) 2022 Open Spaced Repetition
- 用途：自适应间隔重复调度算法（`server/srs/engine.py` 封装）

> Permission is hereby granted, free of charge, to any person obtaining a copy of this
> software and associated documentation files (the "Software"), to deal in the Software
> without restriction, including without limitation the rights to use, copy, modify, merge,
> publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
> to whom the Software is furnished to do so, subject to the following conditions:
> The above copyright notice and this permission notice shall be included in all copies or
> substantial portions of the Software.
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED...

## FastAPI

- 许可证：MIT
- 版权：Copyright (c) 2018-present, Sebastián Ramírez

## Pydantic

- 许可证：MIT
- 版权：Copyright (c) 2017-present, Samuel Colvin and contributors

## SQLAlchemy

- 许可证：MIT
- 版权：Copyright (c) 2005-2025 SQLAlchemy authors and contributors

## HTTPX / python-dotenv / Uvicorn

- HTTPX：BSD-3-Clause（Copyright Encode OSS Ltd.）
- python-dotenv：BSD-3-Clause（Copyright Saurabh Kumar）
- Uvicorn：BSD-3-Clause（Copyright Encode OSS Ltd.）

## PyWebView

- 许可证：BSD-3-Clause
- 版权：Copyright (c) 2014-2017, Roman Sirokov

## edge-tts（LGPL-3.0）

- 项目：edge-tts（https://github.com/rany2/edge-tts）
- 许可证：GNU Lesser General Public License v3
- 用途：可选 TTS 引擎（另有 pyttsx3 兜底），未修改其源码。
- 合规：保留 LGPL 版权声明；用户可替换该库。完整 LGPLv3 文本见官方仓库。

## keyring

- 许可证：MIT
- 版权：Copyright Jason R. Coombs and contributors

## PyInstaller

- 许可证：GPL-2.0 with a special exception（bootloader exception，允许用于构建闭源商业软件）
- 用途：仅作为打包工具，产物中不链接 GPL 代码进入应用逻辑。

## 前端依赖（npm）

| 包 | 许可证 |
|---|---|
| react / react-dom | MIT |
| react-router-dom | MIT |
| lucide-react | ISC |
| recharts | MIT |
| tailwindcss | MIT |
| vite | MIT |

---

> 注：若存在任何许可证归属或条款疑问，请参考各依赖的官方仓库 `LICENSE` 文件。本项目未复制任何 AGPL/GPL 项目（Anki、LibreLingo、LinguaCafe）的代码。

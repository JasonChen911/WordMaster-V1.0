# WordMaster 官网

这是 WordMaster 的独立静态官网。网站源代码位于本目录，桌面软件仍位于上一级项目。官网当前仅在本地完成，尚未公开部署。

## 本地运行

需要 Node.js 20 或更新版本，以及 `../release/WordMaster_Setup.exe`。

```powershell
cd website
npm install
npm run dev
```

打开终端输出的本地地址。开发服务器会直接读取上一级 `release` 目录中的安装包。

## 构建与部署

```powershell
$env:SITE_URL = 'https://你的正式域名'
npm run build
```

将 `dist/` 作为静态站点目录部署。输出中包含首页、下载页、更新日志、真实软件截图、安装包、使用协议、`robots.txt` 和 `sitemap.xml`。部署前设置 `SITE_URL`，以生成正确的站点地图；未设置时默认使用本地预览地址。主流支持目录索引的静态托管可直接提供 `/download/` 和 `/changelog/` 页面。

本地构建完成后可运行 `npm run preview` 检查产物。

## 内容来源

- 版本号从 `../version_info.txt` 读取。
- 安装包体积与 SHA-256 从 `../release/WordMaster_Setup.exe` 实时计算。
- 首页展示的是本项目运行时截取的真实界面。AI 对话演示和记忆曲线明确标为示意。
- `../license_agreement.txt` 是当前内部 Beta 使用协议。项目尚无公开仓库或开源许可证，因此 GitHub、贡献和 Releases 入口仅显示开放状态，不提供虚构链接。

如需公开部署，应先确认软件发行授权、正式域名及公开仓库信息，再更新站内的来源状态和下载渠道。

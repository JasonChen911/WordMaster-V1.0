# WordMaster 官网

这是 WordMaster 的独立静态官网。网站源代码位于本目录，桌面软件仍位于上一级项目。源码公开在 GitHub，官网尚未公开部署。

## 本地运行

需要 Node.js 20 或更新版本。仓库不包含安装包；没有本地 `../release/WordMaster_Setup.exe` 时，网站自动显示源码获取入口。

```powershell
cd website
npm install
npm run dev
```

打开终端输出的本地地址。如果本机存在安装包，开发服务器可以直接读取上一级 `release` 目录中的文件。

## 构建与部署

```powershell
$env:SITE_URL = 'https://你的正式域名'
npm run build
```

将 `dist/` 作为静态站点目录部署。输出包含首页、下载页、更新日志、真实软件截图、使用协议、`robots.txt` 和 `sitemap.xml`。仅在本地存在安装包时，构建才会将其复制到输出目录；从 GitHub 源码构建不会附带安装包或显示无效下载按钮。部署前设置 `SITE_URL`，以生成正确的站点地图；未设置时默认使用本地预览地址。

本地构建完成后可运行 `npm run preview` 检查产物。

## 内容来源

- 版本号从 `../version_info.txt` 读取。
- 若本地存在安装包，体积与 SHA-256 从 `../release/WordMaster_Setup.exe` 实时计算；否则元数据标记为未提供。
- 首页展示的是本项目运行时截取的真实界面。AI 对话演示和记忆曲线明确标为示意。
- `../license_agreement.txt` 是当前 Beta 使用协议。源码仓库公开，但尚未授予开源许可证，也没有公开二进制 Release。

如需公开部署，应先确认正式域名与软件发行授权。

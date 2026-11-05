import { Link } from 'react-router-dom'
import { ArrowRight, Check, Clipboard, Download, ExternalLink, HardDrive, Monitor, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import Reveal from '../components/Reveal'
import release from '../release.generated.json'

export default function DownloadPage() {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle')
  const size = (release.installerBytes / 1024 / 1024).toFixed(1)
  const copyHash = async () => {
    try {
      await navigator.clipboard.writeText(release.sha256)
      setCopyState('copied')
    } catch {
      setCopyState('failed')
    }
    setTimeout(() => setCopyState('idle'), 2500)
  }
  return <>
    <section className="subpage-hero container"><Reveal><span className="eyebrow">Download for Windows</span><h1>开始一段更清晰的<br /><em>学习旅程。</em></h1><p>一份安装包，带上你需要的词汇学习工具。</p></Reveal></section>
    <section className="download-section container"><Reveal className="download-card"><div className="download-card-main"><div className="download-icon"><img src="/images/wordmaster-logo.webp" alt="" width="64" height="64" /></div><div><div className="release-badge"><span /> 当前版本 · Beta</div><h2>WordMaster <span>v{release.version}</span></h2><p>适用于 Windows 的独立桌面应用</p></div></div><div className="download-card-action"><a href="/downloads/WordMaster_Setup.exe" download className="button button-primary"><Download size={18} /> 下载安装包 <ArrowRight size={17} /></a><small>{release.platform} · {size} MiB · 无需安装 Python 或 Node.js</small></div></Reveal><div className="release-note"><ShieldCheck size={17} /><span>文件来自本项目当前构建。下载后可用下方 SHA-256 校验完整性。</span></div></section>
    <section className="download-details container"><Reveal className="detail-panel"><Monitor size={25} /><h3>系统要求</h3><ul><li>Windows 64 位系统</li><li>需要 Microsoft Edge WebView2 运行环境</li><li>AI 功能需要网络与用户自己的 DeepSeek API Key</li></ul><p>当前构建在 Windows 11 环境验证。其他 Windows 版本尚未单独验证。</p></Reveal><Reveal className="detail-panel" delay={0.05}><HardDrive size={25} /><h3>安装方式</h3><ol><li>下载并运行 <code>{release.installerFile}</code></li><li>阅读软件使用协议并选择安装位置</li><li>安装完成后启动 WordMaster</li></ol><p>程序按当前用户安装，不要求管理员权限；学习数据保存在本机。</p></Reveal></section>
    <section className="integrity-section container"><Reveal><div className="integrity-top"><div><span className="eyebrow">Verify your download</span><h2>校验安装包</h2></div><button type="button" onClick={copyHash} className="copy-button" aria-live="polite"><Clipboard size={16} /> {copyState === 'copied' ? '已复制' : copyState === 'failed' ? '复制失败，请手动选取' : '复制 SHA-256'}</button></div><code>{release.sha256}</code><p>Windows PowerShell 可运行：<code>Get-FileHash .\WordMaster_Setup.exe -Algorithm SHA256</code></p></Reveal></section>
    <section className="download-bottom container"><Reveal><div className="bottom-link-card"><div><span className="eyebrow">Release notes</span><h3>查看更新日志</h3><p>了解目前已实现的学习、AI 与稳定性更新。</p></div><Link to="/changelog/" aria-label="查看更新日志"><ArrowRight size={22} /></Link></div></Reveal><Reveal delay={0.06}><div className="bottom-link-card subdued"><div><span className="eyebrow">GitHub releases</span><h3>公开发布入口准备中</h3><p>当前仓库尚未公开，因此暂不提供无效的 GitHub Releases 链接。</p></div><span className="unavailable-mark">未开放</span></div></Reveal></section>
    <section className="license-footnote container"><Check size={15} /><p>当前版本仍受内部 Beta 使用协议约束。<a href="/license/">查看使用协议 <ExternalLink size={12} /></a></p></section>
  </>
}


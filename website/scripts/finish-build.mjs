import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const dist = resolve(root, 'dist')
const installer = process.env.WORDMASTER_INSTALLER || resolve(root, '../release/WordMaster_Setup.exe')
const metadata = JSON.parse(await readFile(resolve(root, 'src/release.generated.json'), 'utf8'))
if (metadata.available) {
  await mkdir(resolve(dist, 'downloads'), { recursive: true })
  if (metadata.chunked) {
    const bytes = await readFile(installer)
    const chunkSize = 8 * 1024 * 1024
    const parts = []
    for (let offset = 0; offset < bytes.length; offset += chunkSize) {
      const name = `part-${String(parts.length).padStart(2, '0')}.bin`
      parts.push(`/downloads/${name}`)
      await writeFile(resolve(dist, 'downloads', name), bytes.subarray(offset, offset + chunkSize))
    }
    const manifest = JSON.stringify({ parts, size: metadata.installerBytes, sha256: metadata.sha256, filename: metadata.installerFile })
    const downloadPage = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>下载安装包 — WordMaster</title><style>body{font-family:"Segoe UI","Microsoft YaHei",sans-serif;background:#f6f9fa;color:#173440;margin:0;min-height:100vh;display:grid;place-items:center}main{background:white;border:1px solid #dce8eb;border-radius:16px;padding:32px;max-width:480px;margin:20px;box-shadow:0 12px 40px #17344012}h1{font-size:27px}p{line-height:1.7;color:#526771}button{border:0;border-radius:10px;background:#176e95;color:white;font:inherit;font-weight:650;padding:14px 22px;cursor:pointer}button:disabled{opacity:.6;cursor:wait}progress{width:100%;height:12px;accent-color:#176e95}a{color:#176e95}@media(prefers-color-scheme:dark){body{background:#101a20;color:#e8f2f5}main{background:#17252c;border-color:#33454d}p{color:#bccdd3}}</style></head><body><main><a href="/download/">← 返回下载页</a><h1>下载 WordMaster</h1><p>安装包将在浏览器中合并并校验，大小 ${(metadata.installerBytes / 1048576).toFixed(1)} MiB。请保持此页打开。</p><button id="start" type="button">开始下载</button><p id="status" role="status" aria-live="polite">准备就绪</p><progress id="progress" max="100" value="0"></progress></main><script>const manifest=${manifest};const button=document.getElementById('start'),status=document.getElementById('status'),progress=document.getElementById('progress');button.onclick=async()=>{button.disabled=true;let chunks=[],done=0;try{for(const path of manifest.parts){const response=await fetch(path);if(!response.ok)throw Error('下载分片失败：'+response.status);const chunk=await response.arrayBuffer();chunks.push(chunk);done+=chunk.byteLength;progress.value=Math.round(done/manifest.size*100);status.textContent='已下载 '+progress.value+'%，正在准备文件';}if(done!==manifest.size)throw Error('文件大小不符');const blob=new Blob(chunks,{type:'application/octet-stream'});status.textContent='正在校验文件…';const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()))).map(x=>x.toString(16).padStart(2,'0')).join('');if(hash!==manifest.sha256)throw Error('文件校验失败，请重新下载');const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=manifest.filename;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);status.textContent='下载已开始，SHA-256 校验通过';}catch(error){status.textContent=error.message;button.disabled=false;progress.value=0;}};</script></body></html>`
    await writeFile(resolve(dist, 'download-file.html'), downloadPage)
  } else {
    await copyFile(installer, resolve(dist, 'downloads/WordMaster_Setup.exe'))
  }
}
const agreement = await readFile(resolve(root, '../license_agreement.txt'), 'utf8')
await writeFile(resolve(dist, 'license.txt'), `\uFEFF${agreement}`, 'utf8')
const escapeHtml = value => value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character])
const agreementBlocks = agreement.trim().split(/\r?\n\s*\r?\n/)
const agreementHtml = agreementBlocks.map((block, index) => {
  if (block.startsWith('## ')) return `<h2>${escapeHtml(block.slice(3))}</h2>`
  if (index === 0) {
    const [title, ...details] = block.split(/\r?\n/)
    return `<h1>${escapeHtml(title)}</h1><p class="license-meta">${details.map(escapeHtml).join('<br>')}</p>`
  }
  return `<p>${escapeHtml(block).replace(/\r?\n/g, '<br>')}</p>`
}).join('\n')
const licensePage = `<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="WordMaster v0.1.0 Beta 用户使用协议，说明软件授权、AI 服务、数据存储和测试版风险。"><title>用户使用协议 — WordMaster</title><link rel="canonical" href="${(process.env.SITE_URL || 'http://localhost:4173').replace(/\/$/, '')}/license/"><style>:root{font-family:Aptos,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:#f8fafb;color:#19252d}header,main,footer{max-width:850px;margin:auto;padding-inline:28px}header{padding-top:38px}header a,footer a{color:#246db2;text-decoration:none}main{padding-top:44px;padding-bottom:70px}h1{font-size:clamp(30px,5vw,46px);letter-spacing:-.04em;line-height:1.2}h2{font-size:22px;margin-top:43px;border-top:1px solid #dae4e8;padding-top:29px}p{font-size:15px;line-height:1.95;margin:18px 0;color:#344750}.license-meta{font-size:13px;color:#667883}footer{border-top:1px solid #dae4e8;padding-top:25px;padding-bottom:50px;font-size:13px}@media(prefers-color-scheme:dark){body{background:#10171b;color:#eff6f8}p{color:#cedde3}.license-meta{color:#9aadb6}h2,footer{border-color:#324249}header a,footer a{color:#a8d9ff}}</style></head><body><header><a href="/">← 返回 WordMaster 官网</a></header><main>${agreementHtml}</main><footer>WordMaster · JasonChen · <a href="mailto:cby080812b@outlook.com">联系提供者</a></footer></body></html>\n`
await mkdir(resolve(dist, 'license'), { recursive: true })
await writeFile(resolve(dist, 'license/index.html'), licensePage, 'utf8')
const siteUrl = (process.env.SITE_URL || 'http://localhost:4173').replace(/\/$/, '')
const urls = ['/', '/download/', '/changelog/', '/license/']
for (const page of urls) {
  if (page === '/license/') continue
  const htmlFile = resolve(dist, page.slice(1), 'index.html')
  const html = await readFile(htmlFile, 'utf8')
  const routeUrl = `${siteUrl}${page}`
  const withMetadata = html
    .replace('content="/images/og-wordmaster.svg"', `content="${siteUrl}/images/og-wordmaster.svg"`)
    .replace('</head>', `<link rel="canonical" href="${routeUrl}" /><meta property="og:url" content="${routeUrl}" /></head>`)
  await writeFile(htmlFile, withMetadata)
}
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map(path => `  <url><loc>${siteUrl}${path}</loc></url>`).join('\n')}\n</urlset>\n`
await writeFile(resolve(dist, 'sitemap.xml'), sitemap)
await writeFile(resolve(dist, 'robots.txt'), `User-agent: *\nAllow: /\nSitemap: ${siteUrl}/sitemap.xml\n`)
await writeFile(resolve(dist, 'release.json'), JSON.stringify(metadata, null, 2) + '\n')
console.log(`Static site built ${metadata.available ? 'with local installer' : 'from source only'}, license, sitemap, and robots.txt`)

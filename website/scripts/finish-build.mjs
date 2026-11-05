import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const dist = resolve(root, 'dist')
const installer = process.env.WORDMASTER_INSTALLER || resolve(root, '../release/WordMaster_Setup.exe')
const metadata = JSON.parse(await readFile(resolve(root, 'src/release.generated.json'), 'utf8'))
if (metadata.available) {
  await mkdir(resolve(dist, 'downloads'), { recursive: true })
  await copyFile(installer, resolve(dist, 'downloads/WordMaster_Setup.exe'))
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

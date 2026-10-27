import { build } from 'vite'
import { mkdir, readFile, writeFile, readdir, copyFile, rename, rm } from 'node:fs/promises'
import { createHash, randomUUID } from 'node:crypto'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.dirname(fileURLToPath(import.meta.url))
const buildId = `${Date.now()}-${randomUUID().slice(0, 8)}`
const stage = path.join(root, `dist_new-${buildId}`)
const dist = path.join(root, 'dist')
const digest = data => createHash('sha256').update(data).digest('hex')
async function files(dir, prefix = '') {
  const result = []
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const name = path.posix.join(prefix, entry.name)
    if (entry.isDirectory()) result.push(...await files(path.join(dir, entry.name), name))
    else result.push(name)
  }
  return result
}
process.env.WORDMASTER_BUILD_ID = buildId
try {
  await build({ root, build: { outDir: stage, emptyOutDir: true } })
  // Give public files immutable generation paths too; an in-flight startup
  // can validate either complete generation while index.html changes atomically.
  let html = await readFile(path.join(stage, 'index.html'), 'utf8')
  for (const name of await files(path.join(root, 'public'))) {
    const versioned = `builds/${buildId}/${name}`
    await mkdir(path.dirname(path.join(stage, versioned)), { recursive: true })
    await rename(path.join(stage, name), path.join(stage, versioned))
    html = html.replaceAll(`/${name}`, `/${versioned}`)
  }
  await writeFile(path.join(stage, 'index.html'), html)
  const names = await files(stage)
  const contents = new Map(await Promise.all(names.map(async name => [name, await readFile(path.join(stage, name))])))
  for (const [name, data] of contents) {
    if (!/\.(js|html|css)$/.test(name)) continue
    for (const match of data.toString().matchAll(/["']((?:\/assets\/|\.\/)[A-Za-z0-9_./-]+\.(?:js|css))["']/g)) {
      const target = match[1].startsWith('/') ? match[1].slice(1) : path.posix.normalize(path.posix.join(path.posix.dirname(name), match[1]))
      if (!contents.has(target)) throw new Error(`Missing dependency ${name} -> ${target}`)
    }
  }
  const manifest = { build_id: buildId, app_version: '0.1.0', index_sha256: digest(contents.get('index.html')), files: {} }
  for (const [name, data] of contents) if (name !== 'index.html') manifest.files[name] = digest(data)
  await writeFile(path.join(stage, `build-${buildId}.json`), JSON.stringify(manifest, null, 2))
  await mkdir(dist, { recursive: true })
  // Additive publication: old tabs retain their hashed imports. Never empty live dist.
  for (const name of [...names.filter(n => n !== 'index.html'), `build-${buildId}.json`]) {
    const target = path.join(dist, name)
    await mkdir(path.dirname(target), { recursive: true })
    const temp = `${target}.${buildId}.tmp`
    await copyFile(path.join(stage, name), temp)
    await rename(temp, target)
  }
  const indexTemp = path.join(dist, `index-${buildId}.tmp`)
  await copyFile(path.join(stage, 'index.html'), indexTemp)
  await rename(indexTemp, path.join(dist, 'index.html'))
  console.log(`Published verified frontend ${buildId}; previous hashed assets retained.`)
} finally {
  // Only this build's unique staging directory, never dist or another build.
  if (path.dirname(path.resolve(stage)) !== path.resolve(root) || !path.basename(stage).startsWith('dist_new-')) throw new Error('Unsafe staging path')
  await rm(stage, { recursive: true, force: true })
}

import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

test('built agreement is a readable UTF-8 page linked from the site', async () => {
  const root = resolve(import.meta.dirname, '..')
  const page = await readFile(resolve(root, 'dist/license/index.html'), 'utf8')
  const plainText = await readFile(resolve(root, 'dist/license.txt'), 'utf8')
  const footer = await readFile(resolve(root, 'src/components/Chrome.tsx'), 'utf8')
  const download = await readFile(resolve(root, 'src/pages/DownloadPage.tsx'), 'utf8')
  assert.match(page, /<meta charset="UTF-8">/)
  assert.match(page, /WordMaster 用户使用协议/)
  assert.match(page, /AI 服务与第三方费用/)
  assert.match(page, /数据存储与删除/)
  assert.ok(plainText.startsWith('\uFEFFWordMaster 用户使用协议'))
  assert.match(footer, /href="\/license\/"/)
  assert.match(download, /href="\/license\/"/)
})

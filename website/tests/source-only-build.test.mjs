import test from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

test('release metadata supports a source checkout without installer binaries', async () => {
  const root = resolve(import.meta.dirname, '..')
  const result = spawnSync(process.execPath, ['scripts/prepare.mjs'], {
    cwd: root,
    env: { ...process.env, WORDMASTER_INSTALLER: resolve(root, 'missing-setup.exe') },
    encoding: 'utf8',
  })
  assert.equal(result.status, 0, result.stderr)
  const metadata = JSON.parse(await readFile(resolve(root, 'src/release.generated.json'), 'utf8'))
  assert.equal(metadata.available, false)
  assert.equal(metadata.sha256, '')
  assert.equal(metadata.chunked, false)
})

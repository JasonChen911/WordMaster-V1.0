import test from 'node:test'
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createHash } from 'node:crypto'

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

test('external download metadata uses the hosted archive checksum and filename', async () => {
  const root = resolve(import.meta.dirname, '..')
  const directory = await mkdtemp(join(tmpdir(), 'wordmaster-download-'))
  try {
    const archive = join(directory, 'WordMaster_Test.zip')
    await writeFile(archive, 'test archive')
    const result = spawnSync(process.execPath, ['scripts/prepare.mjs'], {
      cwd: root,
      env: { ...process.env, WORDMASTER_EXTERNAL_ARCHIVE: archive, WORDMASTER_EXTERNAL_DOWNLOAD_URL: 'https://example.com/download' },
      encoding: 'utf8',
    })
    assert.equal(result.status, 0, result.stderr)
    const metadata = JSON.parse(await readFile(resolve(root, 'src/release.generated.json'), 'utf8'))
    assert.equal(metadata.available, true)
    assert.equal(metadata.installerFile, 'WordMaster_Test.zip')
    assert.equal(metadata.installerBytes, 12)
    assert.equal(metadata.externalUrl, 'https://example.com/download')
    assert.equal(metadata.sha256, createHash('sha256').update('test archive').digest('hex'))
  } finally {
    await rm(directory, { recursive: true, force: true })
  }
})

import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { pruneDist } from './prune-dist.mjs'

test('keeps only the published frontend generation', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'wm-prune-'))
  try {
    await mkdir(path.join(root, 'assets'))
    await mkdir(path.join(root, 'builds', 'old'), { recursive: true })
    await writeFile(path.join(root, 'index.html'), 'current')
    await writeFile(path.join(root, 'build-new.json'), '{}')
    await writeFile(path.join(root, 'build-old.json'), '{}')
    await writeFile(path.join(root, 'assets', 'new.js'), 'new')
    await writeFile(path.join(root, 'assets', 'old.js'), 'old')
    await writeFile(path.join(root, 'builds', 'old', 'recovery.js'), 'old')
    await pruneDist(root, ['index.html', 'build-new.json', 'assets/new.js'])
    assert.equal(await readFile(path.join(root, 'assets', 'new.js'), 'utf8'), 'new')
    await assert.rejects(readFile(path.join(root, 'assets', 'old.js')))
    await assert.rejects(readFile(path.join(root, 'build-old.json')))
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

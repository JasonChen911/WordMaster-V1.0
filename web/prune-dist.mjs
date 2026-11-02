import { readdir, rm, rmdir } from 'node:fs/promises'
import path from 'node:path'

/** Remove old generated assets after the new index and manifest are published. */
export async function pruneDist(dist, activeFiles) {
  const keep = new Set(activeFiles)
  async function visit(dir, prefix = '') {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const name = path.posix.join(prefix, entry.name)
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        if (prefix === '' && !['assets', 'builds'].includes(entry.name)) continue
        await visit(full, name)
        if ((await readdir(full)).length === 0) await rmdir(full)
      } else if ((name.startsWith('assets/') || name.startsWith('builds/') || /^build-[A-Za-z0-9_-]+\.json$/.test(name)) && !keep.has(name)) {
        await rm(full)
      }
    }
  }
  await visit(dist)
}

import { readFile, stat, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createHash } from 'node:crypto'

const root = resolve(import.meta.dirname, '..')
const project = resolve(root, '..')
const versionText = await readFile(resolve(project, 'version_info.txt'), 'utf8')
const match = versionText.match(/StringStruct\(u'ProductVersion',\s*u'([^']+)'\)/)
if (!match) throw new Error('Could not read product version from version_info.txt')
const installer = process.env.WORDMASTER_INSTALLER || resolve(project, 'release/WordMaster_Setup.exe')
const bytes = await readFile(installer).catch(error => {
  if (error.code === 'ENOENT') return null
  throw error
})
const info = {
  version: match[1],
  channel: 'Beta',
  platform: 'Windows x64',
  installerFile: 'WordMaster_Setup.exe',
  available: bytes !== null,
  installerBytes: bytes === null ? 0 : (await stat(installer)).size,
  sha256: bytes === null ? '' : createHash('sha256').update(bytes).digest('hex'),
}
await writeFile(resolve(root, 'src/release.generated.json'), JSON.stringify(info, null, 2) + '\n')
console.log(`Release metadata: v${info.version}, ${info.available ? `${(info.installerBytes / 1024 / 1024).toFixed(1)} MiB` : 'source only'}`)

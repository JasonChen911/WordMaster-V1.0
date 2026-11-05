import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(fileURLToPath(import.meta.url))
const installer = resolve(root, '../release/WordMaster_Setup.exe')
const downloadPath = '/downloads/WordMaster_Setup.exe'

export default defineConfig({
  plugins: [react(), {
    name: 'local-installer-download',
    configureServer(server) {
      server.middlewares.use(downloadPath, (request, response, next) => {
        if (!existsSync(installer)) return next()
        response.setHeader('Content-Type', 'application/vnd.microsoft.portable-executable')
        response.setHeader('Content-Disposition', 'attachment; filename="WordMaster_Setup.exe"')
        response.setHeader('Content-Length', statSync(installer).size)
        if (request.method === 'HEAD') { response.end(); return }
        createReadStream(installer).pipe(response)
      })
    },
  }],
  build: {
    rollupOptions: {
      input: {
        home: resolve(root, 'index.html'),
        download: resolve(root, 'download/index.html'),
        changelog: resolve(root, 'changelog/index.html'),
      },
    },
  },
})

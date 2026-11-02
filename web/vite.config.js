import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { randomUUID } from 'node:crypto'

export default defineConfig({
  base: '/',
  plugins: [react(), {
    name: 'wordmaster-build-id',
    transformIndexHtml() {
      return [{ tag: 'meta', attrs: { name: 'wordmaster-build', content: process.env.WORDMASTER_BUILD_ID || `dev-${randomUUID()}` }, injectTo: 'head' }]
    },
  }],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      vue(),
      vuetify({ autoImport: true })
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true
        },
        '/auth': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true
        },
        '/ws': {
          target: env.VITE_WS_URL || 'ws://localhost:8000',
          ws: true
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: true
    }
  }
})

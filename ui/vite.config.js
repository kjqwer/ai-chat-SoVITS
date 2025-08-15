import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      // 代理ASR API请求到后端
      '/asr': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // 代理其他API请求到后端
      '/models': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/characters': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/config': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/tts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/status': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})

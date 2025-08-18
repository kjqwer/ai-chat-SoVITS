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
  build: {
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Vue 相关库
          if (id.includes('vue')) {
            return 'vue-vendor';
          }
          // Element Plus 核心
          if (id.includes('element-plus/es') && !id.includes('element-plus/es/components')) {
            return 'element-core';
          }
          // Element Plus 组件
          if (id.includes('element-plus/es/components')) {
            return 'element-components';
          }
          // Element Plus 图标
          if (id.includes('@element-plus/icons-vue')) {
            return 'element-icons';
          }
          // 状态管理
          if (id.includes('pinia')) {
            return 'state-vendor';
          }
          // 工具库
          if (id.includes('axios')) {
            return 'utils-vendor';
          }
          // 其他第三方库
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        }
      }
    },
    // 调整块大小警告限制
    chunkSizeWarningLimit: 1500
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

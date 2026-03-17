import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  // ============================================
  // NGROK MODE - Uncomment below for ngrok
  // ============================================
  server: {
    host: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 固定用 127.0.0.1:5173,跟後端 CORS / callback 設定一致
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
  },
})

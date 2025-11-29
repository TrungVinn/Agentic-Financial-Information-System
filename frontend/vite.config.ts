import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Cấu hình server dev cho frontend
  server: {
    port: 5173,
    strictPort: true,
    // Khi gọi API bắt đầu bằng /api sẽ proxy sang Django (http://localhost:8000)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

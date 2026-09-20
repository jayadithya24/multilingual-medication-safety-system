import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_PROXY_TARGET = process.env.VITE_API_URL || 'http://127.0.0.1:8000'

const API_PROXY_PATHS = [
  '/auth',
  '/admin',
  '/neo4j',
  '/patient',
  '/patient-schedule',
  '/doctor',
  '/medicines',
  '/medicine',
  '/interaction',
  '/tts',
  '/voice-search',
  '/upload-image',
  '/prescription-ocr',
  '/health',
  '/mongo',
  '/fcm',
]

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      API_PROXY_PATHS.map((path) => [
        path,
        {
          target: API_PROXY_TARGET,
          changeOrigin: true,
        },
      ]),
    ),
  },
})

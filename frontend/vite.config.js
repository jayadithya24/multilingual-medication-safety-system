import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import process from 'node:process'
import { generateFirebaseConfig } from './scripts/generate-firebase-config.mjs'

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
export default defineConfig(({ mode }) => {
  generateFirebaseConfig(mode)
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const API_PROXY_TARGET = env.VITE_API_URL || 'http://127.0.0.1:8000'
  return {
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      API_PROXY_PATHS.map((path) => [
        path,
        {
          target: API_PROXY_TARGET,
          changeOrigin: true,
          // Patient page URLs share prefixes with API routes. Let Vite serve HTML navigation.
          bypass(req) { if (req.headers.accept?.includes('text/html')) return req.url },
        },
      ]),
    ),
  },
  }
})

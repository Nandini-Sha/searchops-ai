import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, '../', '')
  
  return {
    plugins: [react()],
    envDir: '../', // Read .env from backend root
    server: {
      proxy: {
        '/search': env.VITE_API_PROXY_TARGET || 'http://localhost:8000'
      }
    }
  }
})

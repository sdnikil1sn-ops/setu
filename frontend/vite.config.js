import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.SETU_BACKEND_TARGET || 'http://127.0.0.1:8081';
  return {
    plugins: [react()],
    server: {
      host: '127.0.0.1',
      port: 5173,
      strictPort: true,
      proxy: {
        '/health': { target, changeOrigin: true },
        '/api': { target, changeOrigin: true },
        '/docs': { target, changeOrigin: true },
        '/openapi.json': { target, changeOrigin: true }
      }
    }
  };
});
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, open: true },
  build: {
    // INLINE_ASSETS=1 embute imagens e fontes como data URI, permitindo gerar
    // uma versão da página em arquivo único (ver scripts/build-standalone.mjs).
    assetsInlineLimit: process.env.INLINE_ASSETS ? 100_000_000 : 4096,
  },
})

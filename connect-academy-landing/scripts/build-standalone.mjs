/**
 * Gera uma versão da landing page em ARQUIVO ÚNICO — CSS, JS, imagens e fontes
 * embutidos como data URI, sem nenhuma requisição externa.
 *
 * Útil para enviar a página por e-mail/WhatsApp, abrir offline com duplo clique
 * ou publicar em hospedagens com política de segurança restritiva.
 *
 *   node scripts/build-standalone.mjs   (roda o build com INLINE_ASSETS=1)
 *
 * Saída: dist-standalone/connect-academy.html
 */

import { execSync } from 'node:child_process'
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const DIST = resolve(ROOT, 'dist')
const OUT_DIR = resolve(ROOT, 'dist-standalone')

/* Pesos da Poppins usados pela página */
const WEIGHTS = [400, 500, 600, 700, 800]
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

console.log('› build com assets embutidos…')
execSync('npx vite build', { cwd: ROOT, stdio: 'inherit', env: { ...process.env, INLINE_ASSETS: '1' } })

console.log('› baixando Poppins (subset latin)…')
const gcss = execSync(
  `curl -sS -A "${UA}" "https://fonts.googleapis.com/css2?family=Poppins:wght@${WEIGHTS.join(';')}&display=swap"`,
  { encoding: 'utf8' },
)

let fontCss = ''
for (const block of gcss.split('/*').map((s) => '/*' + s)) {
  if (!/^\/\*\s*latin\s*\*\//.test(block)) continue // só o subset latin
  const url = block.match(/url\((https:[^)]+\.woff2)\)/)?.[1]
  const weight = block.match(/font-weight:\s*(\d+)/)?.[1]
  if (!url || !weight) continue
  const b64 = execSync(`curl -sS -A "${UA}" "${url}" | base64 -w0`, { encoding: 'utf8', maxBuffer: 1 << 28 })
  fontCss += `@font-face{font-family:'Poppins';font-style:normal;font-weight:${weight};font-display:swap;src:url(data:font/woff2;base64,${b64.trim()}) format('woff2');}\n`
}

const assets = readdirSync(resolve(DIST, 'assets'))
const css = readFileSync(resolve(DIST, 'assets', assets.find((f) => f.endsWith('.css'))), 'utf8')
const js = readFileSync(resolve(DIST, 'assets', assets.find((f) => f.endsWith('.js'))), 'utf8')

const html = `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="theme-color" content="#14193C" />
<title>Connect Academy | Gestão. Pessoas. Crescimento. Futuro.</title>
<style>
${fontCss}${css}
/* Landing dark-mode por definição de marca: fixa o fundo em qualquer contexto */
:root, html, body { background:#14193C; color:#FFFFFF; color-scheme: dark; }
</style>
</head>
<body>
<div id="root"></div>
<script type="module">
${js}
</script>
</body>
</html>`

mkdirSync(OUT_DIR, { recursive: true })
const out = resolve(OUT_DIR, 'connect-academy.html')
writeFileSync(out, html)
console.log(`✓ ${out} — ${Math.round(html.length / 1024)} KB, zero requisições externas`)

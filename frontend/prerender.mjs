/**
 * Post-build prerender script.
 * Spins up a static file server on the dist/ folder, visits each public route
 * with Puppeteer, and overwrites the HTML files with the fully-rendered output.
 *
 * Usage: node prerender.mjs (run after `vite build`)
 */

import { createServer } from 'node:http'
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer'

const __dirname = dirname(fileURLToPath(import.meta.url))
const DIST = join(__dirname, 'dist')
const PORT = 4173

const ROUTES = [
  '/',
  '/login',
  '/terms',
  '/privacy',
  '/cookies',
  '/blog',
  '/blog/why-i-built-tonnd',
]

// Minimal static file server that serves dist/ with SPA fallback
function startServer() {
  const mime = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
  }

  const server = createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`)
    let filePath = join(DIST, url.pathname)

    try {
      // Try exact file first
      const content = readFileSync(filePath)
      const ext = filePath.substring(filePath.lastIndexOf('.'))
      res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' })
      res.end(content)
    } catch {
      // SPA fallback: serve index.html
      const html = readFileSync(join(DIST, 'index.html'))
      res.writeHead(200, { 'Content-Type': 'text/html' })
      res.end(html)
    }
  })

  return new Promise((resolve) => {
    server.listen(PORT, () => resolve(server))
  })
}

async function prerender() {
  console.log('Starting prerender...')

  const server = await startServer()
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] })

  for (const route of ROUTES) {
    const page = await browser.newPage()
    const url = `http://localhost:${PORT}${route}`

    console.log(`  Rendering ${route}...`)
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 15000 })

    // Wait for React to finish rendering (app-rendered event or timeout)
    await page.evaluate(() => {
      return new Promise((resolve) => {
        if (document.querySelector('nav') || document.querySelector('h1')) {
          resolve()
          return
        }
        document.addEventListener('app-rendered', resolve, { once: true })
        setTimeout(resolve, 5000)
      })
    })

    // Small extra delay for Helmet to update <head>
    await new Promise((r) => setTimeout(r, 500))

    const html = await page.content()

    // Write the pre-rendered HTML to the correct path
    const outPath = route === '/'
      ? join(DIST, 'index.html')
      : join(DIST, route, 'index.html')

    mkdirSync(dirname(outPath), { recursive: true })
    writeFileSync(outPath, html)
    console.log(`  ✓ ${route} → ${outPath.replace(DIST, 'dist')}`)

    await page.close()
  }

  await browser.close()
  server.close()
  console.log(`\nPrerendered ${ROUTES.length} routes.`)
}

prerender().catch((err) => {
  console.error('Prerender failed:', err)
  process.exit(1)
})

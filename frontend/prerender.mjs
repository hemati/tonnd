/**
 * Post-build prerender script.
 * Spins up a static file server on the dist/ folder, visits each public route
 * with Puppeteer, and overwrites the HTML files with the fully-rendered output.
 *
 * After rendering each page:
 * 1. Deduplicates <head> tags (React Helmet injects page-specific tags, but
 *    the SPA shell's default tags persist — we keep only the last of each type)
 * 2. Inlines critical (above-the-fold) CSS and makes the full stylesheet async
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
  '/impressum',
  '/about',
  '/blog',
  '/blog/why-i-built-tonnd',
  '/blog/fitbit-killed-the-dashboard',
  '/blog/hrv-workout-recovery',
  '/blog/mcp-blog-post',
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
    '.txt': 'text/plain',
  }

  const server = createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`)
    let filePath = join(DIST, url.pathname)

    try {
      const content = readFileSync(filePath)
      const ext = filePath.substring(filePath.lastIndexOf('.'))
      res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' })
      res.end(content)
    } catch {
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

    // Wait for React to finish rendering
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

    // Deduplicate <head> tags — React Helmet appends page-specific tags after
    // the SPA shell defaults. For duplicated tags, keep only the LAST one
    // (which is the page-specific one from Helmet).
    await page.evaluate(() => {
      const head = document.head

      // Deduplicate <title> — keep the page-specific one (not the default)
      const titles = head.querySelectorAll('title')
      if (titles.length > 1) {
        // The default title contains only "TONND" without page-specific prefix.
        // Keep whichever title does NOT start with the default site name alone.
        const defaultPrefix = 'TONND \u2014 Ask'
        let kept = titles[titles.length - 1] // fallback: keep last
        for (const t of titles) {
          if (!t.textContent.startsWith(defaultPrefix)) { kept = t; break }
        }
        for (const t of titles) { if (t !== kept) t.remove() }
      }

      // Deduplicate <link rel="canonical"> — keep last
      const canonicals = head.querySelectorAll('link[rel="canonical"]')
      if (canonicals.length > 1) {
        for (let i = 0; i < canonicals.length - 1; i++) canonicals[i].remove()
      }

      // Deduplicate meta by name or property — keep last of each
      const seen = new Map()
      const metas = Array.from(head.querySelectorAll('meta[name], meta[property]'))
      for (const meta of metas) {
        const key = meta.getAttribute('name') || meta.getAttribute('property')
        if (seen.has(key)) {
          seen.get(key).remove() // remove the earlier one
        }
        seen.set(key, meta)
      }

      // Deduplicate GTM/GA script tags — keep only the first async gtag script
      const gtagScripts = head.querySelectorAll('script[src*="googletagmanager.com/gtag"]')
      if (gtagScripts.length > 1) {
        for (let i = 1; i < gtagScripts.length; i++) gtagScripts[i].remove()
      }
    })

    // Extract critical CSS (styles actually used by rendered DOM)
    const criticalCss = await page.evaluate(() => {
      const used = new Set()
      const sheets = Array.from(document.styleSheets)

      for (const sheet of sheets) {
        try {
          const rules = Array.from(sheet.cssRules || [])
          for (const rule of rules) {
            if (rule instanceof CSSMediaRule) {
              // Include media queries if any contained rule matches
              const subRules = Array.from(rule.cssRules || [])
              const matchingRules = subRules.filter(sub => {
                if (sub instanceof CSSStyleRule) {
                  try { return document.querySelector(sub.selectorText) } catch { return false }
                }
                return true
              })
              if (matchingRules.length > 0) {
                used.add(rule.cssText)
              }
            } else if (rule instanceof CSSStyleRule) {
              try {
                if (document.querySelector(rule.selectorText)) {
                  used.add(rule.cssText)
                }
              } catch { /* invalid selector, skip */ }
            } else {
              // @keyframes, @font-face, etc. — include
              used.add(rule.cssText)
            }
          }
        } catch { /* cross-origin sheet, skip */ }
      }

      return Array.from(used).join('\n')
    })

    // Inline critical CSS and make full stylesheet async
    if (criticalCss.length > 0) {
      await page.evaluate((css) => {
        // Add inline critical CSS
        const style = document.createElement('style')
        style.setAttribute('data-critical', '')
        style.textContent = css
        // Insert before the first <link rel="stylesheet">
        const firstLink = document.head.querySelector('link[rel="stylesheet"]')
        if (firstLink) {
          document.head.insertBefore(style, firstLink)
          // Make the external stylesheet non-render-blocking
          firstLink.setAttribute('media', 'print')
          firstLink.setAttribute('onload', "this.media='all'")
        }
      }, criticalCss)
    }

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

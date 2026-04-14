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

    // Extract above-the-fold critical CSS (only rules matching visible elements)
    const criticalCss = await page.evaluate(() => {
      const viewportHeight = window.innerHeight || 900
      const used = new Set()

      function isAboveFold(selector) {
        try {
          const els = document.querySelectorAll(selector)
          for (const el of els) {
            const rect = el.getBoundingClientRect()
            if (rect.top < viewportHeight && rect.bottom > 0) return true
          }
          return false
        } catch { return false }
      }

      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules || []) {
            if (rule instanceof CSSStyleRule) {
              if (isAboveFold(rule.selectorText)) used.add(rule.cssText)
            } else if (rule instanceof CSSMediaRule) {
              // Only include individual matching rules within the media query
              const matched = []
              for (const sub of rule.cssRules || []) {
                if (sub instanceof CSSStyleRule && isAboveFold(sub.selectorText)) {
                  matched.push(sub.cssText)
                }
              }
              if (matched.length > 0) {
                used.add(`${rule.conditionText ? `@media ${rule.conditionText}` : rule.cssText.split('{')[0]} { ${matched.join(' ')} }`)
              }
            }
            // Skip @keyframes, @font-face — they load with the async stylesheet
          }
        } catch { /* cross-origin, skip */ }
      }

      return Array.from(used).join('\n')
    })

    // Inline critical CSS and make full stylesheets async
    if (criticalCss.length > 0) {
      await page.evaluate((css) => {
        const head = document.head

        // Remove any existing data-critical blocks (from nested renders)
        head.querySelectorAll('style[data-critical]').forEach(s => s.remove())

        // Add single inline critical CSS block
        const style = document.createElement('style')
        style.setAttribute('data-critical', '')
        style.textContent = css

        // Insert before the first <link rel="stylesheet"> and make all stylesheets async
        const styleLinks = head.querySelectorAll('link[rel="stylesheet"]')
        if (styleLinks.length > 0) {
          head.insertBefore(style, styleLinks[0])
          for (const link of styleLinks) {
            link.setAttribute('media', 'print')
            link.setAttribute('onload', "this.media='all'")
          }
        }

        // Remove any existing noscript stylesheet fallbacks
        head.querySelectorAll('noscript').forEach(n => {
          if (n.innerHTML.includes('stylesheet')) n.remove()
        })

        // Add noscript fallback with relative paths (not localhost)
        const noscript = document.createElement('noscript')
        for (const link of styleLinks) {
          const fallback = document.createElement('link')
          fallback.rel = 'stylesheet'
          // Use getAttribute to get the original relative path, not the resolved localhost URL
          const href = link.getAttribute('href') || new URL(link.href).pathname
          fallback.setAttribute('href', href)
          noscript.appendChild(fallback)
        }
        head.appendChild(noscript)
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

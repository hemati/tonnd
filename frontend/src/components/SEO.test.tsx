import { describe, it, expect, afterEach } from 'vitest'
import { render, cleanup, waitFor } from '@testing-library/react'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import SEO from './SEO'

afterEach(cleanup)

function renderSEO(props: Parameters<typeof SEO>[0] = {}) {
  render(
    <HelmetProvider>
      <MemoryRouter>
        <SEO {...props} />
      </MemoryRouter>
    </HelmetProvider>
  )
}

function getMeta(attr: string, value: string): HTMLMetaElement | null {
  return document.querySelector(`meta[${attr}="${value}"]`)
}

function getLink(rel: string): HTMLLinkElement | null {
  return document.querySelector(`link[rel="${rel}"]`)
}

describe('SEO component', () => {
  it('sets default title when no title prop', async () => {
    renderSEO()
    await waitFor(() => {
      expect(document.title).toContain('TONND')
      expect(document.title).toContain('Ask your health data')
    })
  })

  it('sets custom title with TONND suffix', async () => {
    renderSEO({ title: 'Blog' })
    await waitFor(() => {
      expect(document.title).toContain('Blog')
      expect(document.title).toContain('TONND')
    })
  })

  it('sets meta description', async () => {
    renderSEO({ description: 'Custom description' })
    await waitFor(() => {
      const desc = getMeta('name', 'description')
      expect(desc?.content).toBe('Custom description')
    })
  })

  it('uses default description when none provided', async () => {
    renderSEO()
    await waitFor(() => {
      const desc = getMeta('name', 'description')
      expect(desc?.content).toContain('Connect Fitbit')
    })
  })

  it('sets canonical URL from path', async () => {
    renderSEO({ path: '/blog' })
    await waitFor(() => {
      const canonical = getLink('canonical')
      expect(canonical?.href).toBe('https://tonnd.com/blog')
    })
  })

  it('sets noindex meta when noindex=true', async () => {
    renderSEO({ noindex: true })
    await waitFor(() => {
      const robots = getMeta('name', 'robots')
      expect(robots?.content).toBe('noindex, nofollow')
    })
  })

  it('sets og:title and og:description', async () => {
    renderSEO({ title: 'Test', description: 'Test desc' })
    await waitFor(() => {
      expect(getMeta('property', 'og:title')?.content).toContain('Test')
      expect(getMeta('property', 'og:description')?.content).toBe('Test desc')
    })
  })

  it('sets og:image', async () => {
    renderSEO()
    await waitFor(() => {
      const ogImage = getMeta('property', 'og:image')
      expect(ogImage?.content).toContain('tonnd.com')
    })
  })
})

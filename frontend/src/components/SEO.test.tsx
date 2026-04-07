import { describe, it, expect, afterEach } from 'vitest'
import { render, cleanup } from '@testing-library/react'
import { HelmetProvider } from 'react-helmet-async'
import { MemoryRouter } from 'react-router-dom'
import SEO from './SEO'

afterEach(cleanup)

function renderSEO(props: Parameters<typeof SEO>[0] = {}) {
  const ctx = {} as { helmet?: any }
  render(
    <HelmetProvider context={ctx}>
      <MemoryRouter>
        <SEO {...props} />
      </MemoryRouter>
    </HelmetProvider>
  )
  return ctx.helmet
}

describe('SEO component', () => {
  it('renders without crashing', () => {
    expect(() => renderSEO()).not.toThrow()
  })

  it('renders with custom title', () => {
    const helmet = renderSEO({ title: 'Blog' })
    // Helmet context should have title data
    expect(helmet).toBeDefined()
  })

  it('renders with noindex', () => {
    const helmet = renderSEO({ noindex: true })
    expect(helmet).toBeDefined()
  })

  it('accepts all prop combinations', () => {
    expect(() => renderSEO({ title: 'Test', description: 'Desc', path: '/test', noindex: true })).not.toThrow()
    expect(() => renderSEO({ path: '/blog/slug' })).not.toThrow()
    expect(() => renderSEO({})).not.toThrow()
  })
})

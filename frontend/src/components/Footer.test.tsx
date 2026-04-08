import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Footer from './Footer'

afterEach(cleanup)

function renderFooter() {
  return render(
    <MemoryRouter>
      <Footer />
    </MemoryRouter>
  )
}

describe('Footer component', () => {
  it('renders without crashing', () => {
    expect(() => renderFooter()).not.toThrow()
  })

  it('displays TONND brand text', () => {
    renderFooter()
    // "TONND" appears in both the brand area and the copyright
    const tonndElements = screen.getAllByText(/TONND/)
    expect(tonndElements.length).toBeGreaterThanOrEqual(1)
  })

  it('displays the current year in copyright', () => {
    renderFooter()
    const year = new Date().getFullYear().toString()
    expect(screen.getByText(new RegExp(year))).toBeInTheDocument()
  })

  it('renders Sign In link pointing to /login', () => {
    renderFooter()
    const signInLink = screen.getByText('Sign In')
    expect(signInLink).toBeInTheDocument()
    expect(signInLink.closest('a')).toHaveAttribute('href', '/login')
  })

  it('renders Blog link pointing to /blog', () => {
    renderFooter()
    const blogLink = screen.getByText('Blog')
    expect(blogLink).toBeInTheDocument()
    expect(blogLink.closest('a')).toHaveAttribute('href', '/blog')
  })

  it('renders Terms of Service link pointing to /terms', () => {
    renderFooter()
    const link = screen.getByText('Terms of Service')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/terms')
  })

  it('renders Privacy Policy link pointing to /privacy', () => {
    renderFooter()
    const link = screen.getByText('Privacy Policy')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/privacy')
  })

  it('renders Cookie Policy link pointing to /cookies', () => {
    renderFooter()
    const link = screen.getByText('Cookie Policy')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/cookies')
  })

  it('renders GitHub link as external', () => {
    renderFooter()
    const link = screen.getByText('GitHub')
    expect(link).toHaveAttribute('href', 'https://github.com/hemati/tonnd')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('renders Discord link as external', () => {
    renderFooter()
    const link = screen.getByText('Discord')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
    expect(link.getAttribute('href')).toMatch(/^https:\/\/discord\.gg\//)
  })

  it('renders Product and Legal section headings', () => {
    renderFooter()
    expect(screen.getByText('Product')).toBeInTheDocument()
    expect(screen.getByText('Legal')).toBeInTheDocument()
  })

  it('renders GDPR Rights link', () => {
    renderFooter()
    const link = screen.getByText('GDPR Rights')
    expect(link.closest('a')).toHaveAttribute('href', '/privacy#gdpr')
  })

  it('renders Do Not Sell My Info link', () => {
    renderFooter()
    const link = screen.getByText('Do Not Sell My Info')
    expect(link.closest('a')).toHaveAttribute('href', '/privacy#ccpa')
  })

  it('renders the tagline text', () => {
    renderFooter()
    expect(screen.getByText(/Open-source health tracking/)).toBeInTheDocument()
  })
})

import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import NotFound from './NotFound'

afterEach(cleanup)

function renderNotFound() {
  return render(
    <HelmetProvider>
      <MemoryRouter>
        <NotFound />
      </MemoryRouter>
    </HelmetProvider>
  )
}

describe('NotFound component', () => {
  it('renders without crashing', () => {
    expect(() => renderNotFound()).not.toThrow()
  })

  it('displays 404 text', () => {
    renderNotFound()
    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('displays "Page not found" heading', () => {
    renderNotFound()
    expect(screen.getByText('Page not found')).toBeInTheDocument()
  })

  it('displays descriptive message', () => {
    renderNotFound()
    expect(screen.getByText(/doesn't exist/)).toBeInTheDocument()
  })

  it('has a link back to home', () => {
    renderNotFound()
    const backLink = screen.getByText(/Back to home/)
    expect(backLink).toBeInTheDocument()
    expect(backLink.closest('a')).toHaveAttribute('href', '/')
  })

  it('renders the Logo component (TONND text)', () => {
    renderNotFound()
    expect(screen.getByText('TONND')).toBeInTheDocument()
  })

  it('Logo links to home page', () => {
    renderNotFound()
    const tonndLink = screen.getByText('TONND').closest('a')
    expect(tonndLink).toHaveAttribute('href', '/')
  })
})

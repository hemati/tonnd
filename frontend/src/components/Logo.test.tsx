import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Logo from './Logo'
import { LOGO_PATH } from '../config/theme'

afterEach(cleanup)

function renderLogo() {
  return render(
    <MemoryRouter>
      <Logo />
    </MemoryRouter>
  )
}

describe('Logo component', () => {
  it('renders without crashing', () => {
    expect(() => renderLogo()).not.toThrow()
  })

  it('displays TONND text', () => {
    renderLogo()
    expect(screen.getByText('TONND')).toBeInTheDocument()
  })

  it('links to the home page', () => {
    renderLogo()
    const link = screen.getByText('TONND').closest('a')
    expect(link).toHaveAttribute('href', '/')
  })

  it('renders an SVG element', () => {
    renderLogo()
    const link = screen.getByText('TONND').closest('a')!
    const svg = link.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('SVG uses the LOGO_PATH constant', () => {
    renderLogo()
    const link = screen.getByText('TONND').closest('a')!
    const path = link.querySelector('svg path')
    expect(path).toBeInTheDocument()
    expect(path?.getAttribute('d')).toBe(LOGO_PATH)
  })
})

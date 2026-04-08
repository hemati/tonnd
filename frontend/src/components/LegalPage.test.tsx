import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import { LegalPage, LegalHeading, LegalSubheading } from './LegalPage'

afterEach(cleanup)

function renderLegalPage(props?: Partial<{ title: string; lastUpdated: string; children: React.ReactNode }>) {
  const defaultProps = {
    title: 'Terms of Service',
    lastUpdated: 'January 1, 2025',
    children: <p>Legal content goes here.</p>,
    ...props,
  }

  return render(
    <HelmetProvider>
      <MemoryRouter initialEntries={['/terms']}>
        <LegalPage {...defaultProps} />
      </MemoryRouter>
    </HelmetProvider>
  )
}

describe('LegalPage component', () => {
  it('renders without crashing', () => {
    expect(() => renderLegalPage()).not.toThrow()
  })

  it('displays the title as an h1', () => {
    renderLegalPage({ title: 'Privacy Policy' })
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Privacy Policy')
  })

  it('displays the last updated date', () => {
    renderLegalPage({ lastUpdated: 'March 15, 2025' })
    expect(screen.getByText(/March 15, 2025/)).toBeInTheDocument()
  })

  it('renders children content', () => {
    renderLegalPage({ children: <p>Custom legal content</p> })
    expect(screen.getByText('Custom legal content')).toBeInTheDocument()
  })

  it('has a Back link to home', () => {
    renderLegalPage()
    const backLink = screen.getByText(/Back/)
    expect(backLink.closest('a')).toHaveAttribute('href', '/')
  })

  it('renders footer navigation links', () => {
    renderLegalPage()

    const termsLink = screen.getByText('Terms of Service', { selector: 'a[href="/terms"]' })
    expect(termsLink).toBeInTheDocument()

    const privacyLink = screen.getByText('Privacy Policy')
    expect(privacyLink.closest('a')).toHaveAttribute('href', '/privacy')

    const cookiesLink = screen.getByText('Cookie Policy')
    expect(cookiesLink.closest('a')).toHaveAttribute('href', '/cookies')

    const homeLink = screen.getByText('Home')
    expect(homeLink.closest('a')).toHaveAttribute('href', '/')
  })

})

describe('LegalHeading component', () => {
  it('renders an h2 element', () => {
    render(<LegalHeading>Section Title</LegalHeading>)
    const heading = screen.getByRole('heading', { level: 2 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Section Title')
  })

  it('renders with different text', () => {
    render(<LegalHeading>Data Collection</LegalHeading>)
    expect(screen.getByText('Data Collection')).toBeInTheDocument()
  })
})

describe('LegalSubheading component', () => {
  it('renders an h3 element', () => {
    render(<LegalSubheading>Subsection Title</LegalSubheading>)
    const heading = screen.getByRole('heading', { level: 3 })
    expect(heading).toBeInTheDocument()
    expect(heading).toHaveTextContent('Subsection Title')
  })

  it('renders with different text', () => {
    render(<LegalSubheading>Personal Information</LegalSubheading>)
    expect(screen.getByText('Personal Information')).toBeInTheDocument()
  })
})

import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import SEO from './SEO'

interface LegalPageProps {
  title: string
  lastUpdated: string
  children: ReactNode
}

export function LegalPage({ title, lastUpdated, children }: LegalPageProps) {
  const { pathname } = useLocation()

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <SEO title={title} description={`${title} for TONND, the open-source health dashboard.`} path={pathname} />
      <div className="max-w-3xl mx-auto px-5 py-12">
        <div className="mb-10">
          <Link to="/" className="text-[13px] text-white/40 hover:text-white/70 transition-colors">&larr; Back</Link>
          <h1 className="text-3xl font-bold mt-4 mb-1">{title}</h1>
          <p className="text-sm text-white/30">Last updated: {lastUpdated}</p>
        </div>

        <div className="space-y-8 text-sm text-white/50 leading-relaxed">
          {children}
        </div>

        <div className="mt-10 pt-6 border-t border-white/[.06] flex gap-6 text-[13px] text-white/30">
          <Link to="/terms" className="hover:text-white/60 transition-colors">Terms of Service</Link>
          <Link to="/privacy" className="hover:text-white/60 transition-colors">Privacy Policy</Link>
          <Link to="/cookies" className="hover:text-white/60 transition-colors">Cookie Policy</Link>
          <Link to="/" className="hover:text-white/60 transition-colors">Home</Link>
        </div>
      </div>
    </div>
  )
}

export function LegalHeading({ children }: { children: ReactNode }) {
  return <h2 className="text-lg font-semibold text-white/90 mb-3">{children}</h2>
}

export function LegalSubheading({ children }: { children: ReactNode }) {
  return <h3 className="text-sm font-semibold text-white/70 mt-5 mb-2">{children}</h3>
}

import { Link } from 'react-router-dom'
import SEO from './SEO'
import Logo from './Logo'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      <SEO title="Page not found" noindex path="/404" />
      <div className="max-w-5xl mx-auto px-5 h-14 flex items-center">
        <Logo />
      </div>
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-[13px] text-white/25 font-mono mb-2">404</p>
          <h1 className="text-2xl font-bold mb-3">Page not found</h1>
          <p className="text-sm text-white/40 mb-6">The page you're looking for doesn't exist.</p>
          <Link to="/" className="text-sm text-white/60 hover:text-white transition-colors">&larr; Back to home</Link>
        </div>
      </div>
    </div>
  )
}

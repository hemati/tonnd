import { Link } from 'react-router-dom'
import { LOGO_PATH } from '../config/theme'

export default function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 group">
      <svg viewBox="0 0 24 24" className="w-5 h-5 text-white/70 group-hover:text-white transition-colors" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d={LOGO_PATH} />
      </svg>
      <span className="text-sm font-semibold text-white/90">TONND</span>
    </Link>
  )
}

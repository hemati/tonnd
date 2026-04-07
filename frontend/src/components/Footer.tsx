import { Link } from 'react-router-dom'
import { GITHUB_URL, DISCORD_URL, LOGO_PATH } from '../config/theme'

export default function Footer() {
  return (
    <footer className="border-t border-white/[.06]">
      <div className="max-w-5xl mx-auto px-5 py-10">
        <div className="grid sm:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <svg viewBox="0 0 24 24" className="w-4 h-4 text-white/50" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                <path d={LOGO_PATH} />
              </svg>
              <span className="text-sm font-semibold text-white/70">TONND</span>
            </div>
            <p className="text-[13px] text-white/30 leading-relaxed">
              Open-source health tracking.<br />
              Your data, your server.
            </p>
          </div>

          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-white/25 mb-3">Product</h4>
            <div className="space-y-2">
              <Link to="/login" className="block text-[13px] text-white/40 hover:text-white/70 transition-colors">Sign In</Link>
              <Link to="/blog" className="block text-[13px] text-white/40 hover:text-white/70 transition-colors">Blog</Link>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="block text-[13px] text-white/40 hover:text-white/70 transition-colors">GitHub</a>
              <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer" className="block text-[13px] text-white/40 hover:text-white/70 transition-colors">Discord</a>
            </div>
          </div>

          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-white/25 mb-3">Legal</h4>
            <div className="space-y-2">
              <Link to="/terms" className="block text-[13px] text-white/40 hover:text-white/70 transition-colors">Terms of Service</Link>
              <Link to="/privacy" className="block text-[13px] text-white/40 hover:text-white/70 transition-colors">Privacy Policy</Link>
              <Link to="/cookies" className="block text-[13px] text-white/40 hover:text-white/70 transition-colors">Cookie Policy</Link>
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-white/[.06] flex flex-wrap justify-between items-center gap-4">
          <p className="text-[12px] text-white/20">&copy; {new Date().getFullYear()} TONND</p>
          <div className="flex gap-4 text-[12px] text-white/20">
            <Link to="/privacy#gdpr" className="hover:text-white/40 transition-colors">GDPR Rights</Link>
            <Link to="/privacy#ccpa" className="hover:text-white/40 transition-colors">Do Not Sell My Info</Link>
          </div>
        </div>
      </div>
    </footer>
  )
}

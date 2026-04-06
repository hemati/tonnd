import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth, User } from '../hooks/useAuth'
import { theme, LOGO_PATH, DISCORD_URL } from '../config/theme'

interface LayoutProps {
  children: ReactNode
  user: User | null
}

export default function Layout({ children, user }: LayoutProps) {
  const { signOut } = useAuth()

  const handleSignOut = () => {
    signOut()
    window.location.href = '/'
  }

  return (
    <div className={`min-h-screen ${theme.pageBg} text-white flex flex-col`}>

      {/* header */}
      <header className={theme.navBg}>
        <div className={theme.navContainer}>
          <Link to="/" className="flex items-center gap-2 group">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white/70 group-hover:text-white transition-colors" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <path d={LOGO_PATH} />
            </svg>
            <span className="text-sm font-semibold text-white/90">TONND</span>
          </Link>

          <div className="flex items-center gap-4">
            <span className="text-[13px] text-white/35 hidden sm:block">{user?.email}</span>
            <button onClick={handleSignOut} className={theme.btnGhost}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* content */}
      <main className={`flex-1 ${theme.container} ${theme.section}`}>
        {children}
      </main>

      {/* footer */}
      <footer className={theme.divider}>
        <div className={`${theme.container} py-4 flex items-center justify-between`}>
          <p className={`text-[12px] ${theme.muted}`}>
            TONND &copy; {new Date().getFullYear()}
          </p>
          <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer" className={`text-[12px] ${theme.muted} hover:text-white/50 transition-colors`}>
            Discord
          </a>
        </div>
      </footer>
    </div>
  )
}

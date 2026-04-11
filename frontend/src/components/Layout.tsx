import { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth, User } from '../hooks/useAuth'
import { theme, DISCORD_URL } from '../config/theme'
import Logo from './Logo'

interface LayoutProps {
  children: ReactNode
  user: User | null
}

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `text-[13px] transition-colors ${isActive ? 'text-white' : 'text-white/35 hover:text-white/60'}`

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
          <div className="flex items-center gap-6">
            <Logo />
            <nav className="flex items-center gap-4">
              <NavLink to="/" end className={navLinkClass}>Dashboard</NavLink>
              <NavLink to="/sources" className={navLinkClass}>Sources</NavLink>
            </nav>
          </div>

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

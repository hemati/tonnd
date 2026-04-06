import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { theme, LOGO_PATH } from '../config/theme'

export default function Login() {
  const { login, register, loginWithGoogle } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      if (isRegister) {
        await register(email, password)
      } else {
        await login(email, password)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={`min-h-screen ${theme.pageBg} text-white flex flex-col`}>

      {/* minimal nav */}
      <div className={theme.container}>
        <div className="h-14 flex items-center">
          <Link to="/" className="flex items-center gap-2 group">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white/70 group-hover:text-white transition-colors" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <path d={LOGO_PATH} />
            </svg>
            <span className="text-sm font-semibold text-white/90">TONND</span>
          </Link>
        </div>
      </div>

      {/* centered form */}
      <div className="flex-1 flex items-center justify-center px-5 py-16">
        <div className="w-full max-w-sm">
          <h1 className={`text-2xl mb-2 ${theme.heading}`}>
            {isRegister ? 'Create your account' : 'Sign in to TONND'}
          </h1>
          <p className={`text-sm ${theme.body} mb-8`}>
            {isRegister ? 'Free forever. No credit card required.' : 'Welcome back.'}
          </p>

          {/* Google OAuth */}
          <button
            onClick={() => loginWithGoogle()}
            className={`w-full ${theme.btnSecondary} py-2.5 mb-6`}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </button>

          {/* divider */}
          <div className="relative mb-6">
            <div className={`absolute inset-0 flex items-center ${theme.divider}`} />
            <div className="relative flex justify-center">
              <span className={`px-3 ${theme.pageBg} text-[12px] ${theme.muted}`}>or</span>
            </div>
          </div>

          {/* email/password form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className={theme.input}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className={theme.input}
            />
            {error && <p className="text-red-400/80 text-sm">{error}</p>}
            <button type="submit" disabled={isSubmitting} className={`w-full ${theme.btnPrimary} disabled:opacity-50`}>
              {isSubmitting ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          {/* toggle */}
          <p className="text-center text-sm text-white/40 mt-4">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              type="button"
              onClick={() => { setIsRegister(!isRegister); setError(null) }}
              className="text-white/70 hover:text-white transition-colors"
            >
              {isRegister ? 'Sign In' : 'Create one'}
            </button>
          </p>

          {/* legal */}
          <p className={`text-center text-[12px] ${theme.muted} mt-8`}>
            By signing in, you agree to our{' '}
            <Link to="/terms" className="text-white/40 hover:text-white/60 transition-colors">Terms</Link>
            {' '}and{' '}
            <Link to="/privacy" className="text-white/40 hover:text-white/60 transition-colors">Privacy Policy</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

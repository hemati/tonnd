import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { TOKEN_KEY } from '../config/constants'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [message, setMessage] = useState('Processing authentication...')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      const errorParam = searchParams.get('error')
      const errorMessage = searchParams.get('message')

      if (errorParam) {
        setError(errorMessage || errorParam)
        setTimeout(() => navigate('/'), 3000)
        return
      }

      // Fitbit OAuth callback
      const success = searchParams.get('success')
      const fitbit = searchParams.get('fitbit')
      if (success === 'true' && fitbit === 'connected') {
        setMessage('Fitbit connected successfully! Redirecting...')
        setTimeout(() => navigate('/'), 1500)
        return
      }

      // Google OAuth callback — token arrives as query param
      const token = searchParams.get('access_token')
      if (token) {
        localStorage.setItem(TOKEN_KEY, token)
        window.location.href = '/'
        return
      }

      // Email/password login callback (if any)
      if (localStorage.getItem(TOKEN_KEY)) {
        window.location.href = '/'
        return
      }

      setError('Authentication failed. Please try again.')
      setTimeout(() => navigate('/'), 3000)
    }

    handleCallback()
  }, [searchParams, navigate])

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        {error ? (
          <>
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/20 mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Error</h2>
            <p className="text-red-400">{error}</p>
            <p className="text-slate-400 mt-2">Redirecting...</p>
          </>
        ) : (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
            <p className="text-white">{message}</p>
          </>
        )}
      </div>
    </div>
  )
}

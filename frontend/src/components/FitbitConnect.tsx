import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { initFitbitAuth } from '../services/api'

export default function FitbitConnect() {
  const navigate = useNavigate()
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleConnect = async () => {
    setIsConnecting(true)
    setError(null)

    try {
      const response = await initFitbitAuth()
      // Redirect to Fitbit authorization page
      window.location.href = response.authorization_url
    } catch (err) {
      console.error('Error connecting Fitbit:', err)
      setError(err instanceof Error ? err.message : 'Failed to connect Fitbit')
      setIsConnecting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50">
        {/* Fitbit Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-[#00B0B9]/20 mb-4">
            <svg
              className="w-10 h-10 text-[#00B0B9]"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Connect Your Fitbit
          </h1>
          <p className="text-slate-400">
            Link your Fitbit account to sync your health data automatically
          </p>
        </div>

        {/* Benefits */}
        <div className="space-y-4 mb-8">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center">
              <span className="text-lg">⚖️</span>
            </div>
            <div>
              <h3 className="text-white font-medium">Weight & Body Composition</h3>
              <p className="text-slate-400 text-sm">
                Track weight, body fat, and BMI from your RENPHO scale
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center">
              <span className="text-lg">😴</span>
            </div>
            <div>
              <h3 className="text-white font-medium">Sleep Analysis</h3>
              <p className="text-slate-400 text-sm">
                Monitor sleep stages, duration, and efficiency
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center">
              <span className="text-lg">👟</span>
            </div>
            <div>
              <h3 className="text-white font-medium">Activity Tracking</h3>
              <p className="text-slate-400 text-sm">
                Steps, calories burned, and active minutes
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center">
              <span className="text-lg">❤️</span>
            </div>
            <div>
              <h3 className="text-white font-medium">Heart Rate</h3>
              <p className="text-slate-400 text-sm">
                Resting heart rate and heart rate zones
              </p>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {/* Connect Button */}
        <button
          onClick={handleConnect}
          disabled={isConnecting}
          className="w-full bg-[#00B0B9] hover:bg-[#009BA3] disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
        >
          {isConnecting ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
              Connecting...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M13.5 2c-5.621 0-10.211 4.443-10.475 10h-3.025l5 6.625 5-6.625h-2.975c.257-3.351 3.06-6 6.475-6 3.584 0 6.5 2.916 6.5 6.5s-2.916 6.5-6.5 6.5c-1.863 0-3.542-.793-4.728-2.053l-2.427 3.216c1.877 1.754 4.389 2.837 7.155 2.837 5.79 0 10.5-4.71 10.5-10.5s-4.71-10.5-10.5-10.5z" />
              </svg>
              Connect Fitbit
            </>
          )}
        </button>

        {/* Skip Link */}
        <button
          onClick={() => navigate('/')}
          className="w-full mt-4 text-slate-400 hover:text-white text-sm transition-colors"
        >
          Skip for now
        </button>

        {/* Privacy Note */}
        <p className="mt-6 text-center text-xs text-slate-500">
          We only access the data you authorize. Your information is encrypted
          and never shared with third parties.
        </p>
      </div>
    </div>
  )
}

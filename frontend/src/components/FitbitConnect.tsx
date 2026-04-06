import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { initFitbitAuth, fetchUser, api } from '../services/api'
import { trackEvent } from '../lib/analytics'

export default function FitbitConnect() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isConnectingFitbit, setIsConnectingFitbit] = useState(false)
  const [isConnectingRenpho, setIsConnectingRenpho] = useState(false)
  const [renphoEmail, setRenphoEmail] = useState('')
  const [renphoPassword, setRenphoPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const { data: user } = useQuery({ queryKey: ['user'], queryFn: fetchUser })

  const handleConnectFitbit = async () => {
    setIsConnectingFitbit(true)
    setError(null)
    try {
      const response = await initFitbitAuth()
      window.location.href = response.authorization_url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Fitbit')
      setIsConnectingFitbit(false)
    }
  }

  const handleConnectRenpho = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsConnectingRenpho(true)
    setError(null)
    setSuccess(null)
    try {
      await api.post('/auth/renpho/connect', { email: renphoEmail, password: renphoPassword })
      trackEvent('renpho_connected')
      setSuccess('Renpho connected!')
      setRenphoEmail('')
      setRenphoPassword('')
      queryClient.invalidateQueries({ queryKey: ['user'] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Renpho')
    } finally {
      setIsConnectingRenpho(false)
    }
  }

  const handleDisconnectRenpho = async () => {
    try {
      await api.delete('/auth/renpho/disconnect')
      queryClient.invalidateQueries({ queryKey: ['user'] })
      setSuccess('Renpho disconnected')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect')
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Fitbit */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#00B0B9]/20 mb-3">
            <svg className="w-8 h-8 text-[#00B0B9]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white">Fitbit</h2>
          <p className="text-slate-400 text-sm">
            Sleep, activity, heart rate, HRV, SpO2, and more
          </p>
        </div>

        {user?.fitbit_connected ? (
          <div className="text-center">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Connected
            </span>
          </div>
        ) : (
          <button
            onClick={handleConnectFitbit}
            disabled={isConnectingFitbit}
            className="w-full bg-[#00B0B9] hover:bg-[#009BA3] disabled:opacity-50 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {isConnectingFitbit ? 'Connecting...' : 'Connect Fitbit'}
          </button>
        )}
      </div>

      {/* Renpho */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-500/20 mb-3">
            <span className="text-2xl">⚖️</span>
          </div>
          <h2 className="text-xl font-bold text-white">Renpho</h2>
          <p className="text-slate-400 text-sm">
            Smart scale — weight, body fat, muscle mass, BMI, and 12+ metrics
          </p>
        </div>

        {user?.renpho_connected ? (
          <div className="text-center space-y-3">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Connected
            </span>
            <button
              onClick={handleDisconnectRenpho}
              className="block mx-auto text-slate-400 hover:text-red-400 text-sm transition-colors"
            >
              Disconnect
            </button>
          </div>
        ) : (
          <form onSubmit={handleConnectRenpho} className="space-y-3">
            <input
              type="email"
              placeholder="Renpho Email"
              value={renphoEmail}
              onChange={(e) => setRenphoEmail(e.target.value)}
              required
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <input
              type="password"
              placeholder="Renpho Password"
              value={renphoPassword}
              onChange={(e) => setRenphoPassword(e.target.value)}
              required
              className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              type="submit"
              disabled={isConnectingRenpho}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-medium py-3 px-4 rounded-lg transition-colors"
            >
              {isConnectingRenpho ? 'Connecting...' : 'Connect Renpho'}
            </button>
            <p className="text-xs text-slate-500 text-center">
              Uses your Renpho app credentials. Note: this may log you out of the Renpho mobile app.
            </p>
          </form>
        )}
      </div>

      {/* Messages */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}
      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
          <p className="text-emerald-400 text-sm">{success}</p>
        </div>
      )}

      {/* Skip */}
      <button
        onClick={() => navigate('/')}
        className="w-full text-slate-400 hover:text-white text-sm transition-colors"
      >
        Skip for now
      </button>

      <p className="text-center text-xs text-slate-500">
        We only access the data you authorize. Your information is encrypted and never shared with third parties.
      </p>
    </div>
  )
}

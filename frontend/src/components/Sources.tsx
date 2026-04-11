import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { initFitbitAuth, fetchUser, api } from '../services/api'
import { trackEvent } from '../lib/analytics'
import { FitbitIcon, RenphoIcon, HevyIcon } from './SourceIcons'

const CARD = 'rounded-xl border border-white/[.06] bg-white/[.02] p-8'
const INPUT = 'w-full px-4 py-2.5 bg-white/[.04] border border-white/[.1] rounded-md text-white placeholder-white/25 text-sm focus:outline-none focus:border-white/25 transition-colors'
const BTN_CONNECT = 'w-full bg-white text-black hover:bg-white/90 disabled:opacity-50 font-medium py-2.5 px-4 rounded-md transition-colors text-sm'

const CheckIcon = () => (
  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
)

export default function Sources() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isConnectingFitbit, setIsConnectingFitbit] = useState(false)
  const [isConnectingRenpho, setIsConnectingRenpho] = useState(false)
  const [isConnectingHevy, setIsConnectingHevy] = useState(false)
  const [renphoEmail, setRenphoEmail] = useState('')
  const [renphoPassword, setRenphoPassword] = useState('')
  const [hevyApiKey, setHevyApiKey] = useState('')
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

  const handleConnectHevy = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsConnectingHevy(true)
    setError(null)
    setSuccess(null)
    try {
      await api.post('/auth/hevy/connect', { api_key: hevyApiKey })
      trackEvent('hevy_connected')
      setSuccess('Hevy connected!')
      setHevyApiKey('')
      queryClient.invalidateQueries({ queryKey: ['user'] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect Hevy')
    } finally {
      setIsConnectingHevy(false)
    }
  }

  const handleDisconnect = async (source: 'renpho' | 'hevy') => {
    try {
      await api.delete(`/auth/${source}/disconnect`)
      queryClient.invalidateQueries({ queryKey: ['user'] })
      setSuccess(`${source.charAt(0).toUpperCase() + source.slice(1)} disconnected`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect')
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      {/* Fitbit */}
      <div className={CARD}>
        <div className="flex items-start gap-4 mb-5">
          <FitbitIcon className="w-8 h-8 flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-base font-semibold text-white">Fitbit</h2>
            <p className="text-white/40 text-sm">Sleep stages, heart rate, activity, HRV, SpO2, and 10+ metrics</p>
          </div>
        </div>
        {user?.fitbit_connected ? (
          <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/[.06] text-white/60 rounded-md text-sm">
            <CheckIcon /> Connected
          </span>
        ) : (
          <button onClick={handleConnectFitbit} disabled={isConnectingFitbit} className={BTN_CONNECT}>
            {isConnectingFitbit ? 'Connecting...' : 'Connect Fitbit'}
          </button>
        )}
      </div>

      {/* Renpho */}
      <div className={CARD}>
        <div className="flex items-start gap-4 mb-5">
          <RenphoIcon className="w-8 h-8 flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-base font-semibold text-white">Renpho Smart Scale</h2>
            <p className="text-white/40 text-sm">Weight, body fat, muscle mass, BMI, and full body composition</p>
          </div>
        </div>
        {user?.renpho_connected ? (
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/[.06] text-white/60 rounded-md text-sm">
              <CheckIcon /> Connected
            </span>
            <button onClick={() => handleDisconnect('renpho')} className="text-white/30 hover:text-white/60 text-sm transition-colors">
              Disconnect
            </button>
          </div>
        ) : (
          <form onSubmit={handleConnectRenpho} className="space-y-2.5">
            <input type="email" placeholder="Renpho email" value={renphoEmail} onChange={(e) => setRenphoEmail(e.target.value)} required className={INPUT} />
            <input type="password" placeholder="Renpho password" value={renphoPassword} onChange={(e) => setRenphoPassword(e.target.value)} required className={INPUT} />
            <button type="submit" disabled={isConnectingRenpho} className={BTN_CONNECT}>
              {isConnectingRenpho ? 'Connecting...' : 'Connect Renpho'}
            </button>
            <p className="text-xs text-white/25">Uses your Renpho app credentials. May log you out of the mobile app.</p>
          </form>
        )}
      </div>

      {/* Hevy */}
      <div className={CARD}>
        <div className="flex items-start gap-4 mb-5">
          <HevyIcon className="w-8 h-8 flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-base font-semibold text-white">Hevy</h2>
            <p className="text-white/40 text-sm">Workout tracking — exercises, sets, reps, volume, and muscle groups</p>
          </div>
        </div>
        {user?.hevy_connected ? (
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/[.06] text-white/60 rounded-md text-sm">
              <CheckIcon /> Connected
            </span>
            <button onClick={() => handleDisconnect('hevy')} className="text-white/30 hover:text-white/60 text-sm transition-colors">
              Disconnect
            </button>
          </div>
        ) : (
          <form onSubmit={handleConnectHevy} className="space-y-2.5">
            <input type="password" placeholder="Hevy API key" value={hevyApiKey} onChange={(e) => setHevyApiKey(e.target.value)} required className={INPUT} />
            <button type="submit" disabled={isConnectingHevy} className={BTN_CONNECT}>
              {isConnectingHevy ? 'Connecting...' : 'Connect Hevy'}
            </button>
            <p className="text-xs text-white/25">
              Requires Hevy Pro.{' '}
              <a href="https://hevy.com/settings?developer" target="_blank" rel="noopener noreferrer" className="text-white/40 hover:text-white/60 underline">
                Get your API key
              </a>
            </p>
          </form>
        )}
      </div>

      {/* Messages */}
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-md">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}
      {success && (
        <div className="p-3 bg-white/[.04] border border-white/[.08] rounded-md">
          <p className="text-white/60 text-sm">{success}</p>
        </div>
      )}

      {/* Skip */}
      <button onClick={() => navigate('/dashboard')} className="w-full text-white/30 hover:text-white/50 text-sm transition-colors py-2">
        Skip for now
      </button>

      <p className="text-center text-xs text-white/20 pb-4">
        Your credentials are encrypted and never shared with third parties.
      </p>
    </div>
  )
}

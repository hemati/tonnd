import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

interface CookiePreferences {
  necessary: boolean
  functional: boolean
  analytics: boolean
  marketing: boolean
  consentDate: string
  consentVersion: string
}

const CONSENT_VERSION = '1.0'
const COOKIE_CONSENT_KEY = 'cookie_consent'

export function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [preferences, setPreferences] = useState<CookiePreferences>({
    necessary: true,
    functional: true,
    analytics: false,
    marketing: false,
    consentDate: '',
    consentVersion: CONSENT_VERSION,
  })

  useEffect(() => {
    const stored = localStorage.getItem(COOKIE_CONSENT_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as CookiePreferences
      if (parsed.consentVersion === CONSENT_VERSION) {
        setPreferences(parsed)
        setShowBanner(false)
      } else {
        setShowBanner(true)
      }
    } else {
      setShowBanner(true)
    }
  }, [])

  const savePreferences = (prefs: CookiePreferences) => {
    const updatedPrefs = {
      ...prefs,
      consentDate: new Date().toISOString(),
      consentVersion: CONSENT_VERSION,
    }
    localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify(updatedPrefs))
    setPreferences(updatedPrefs)
    setShowBanner(false)
    setShowSettings(false)
    window.dispatchEvent(new CustomEvent('cookieConsentUpdated', { detail: updatedPrefs }))
  }

  const acceptAll = () => savePreferences({ ...preferences, functional: true, analytics: true, marketing: true })
  const acceptNecessary = () => savePreferences({ ...preferences, functional: false, analytics: false, marketing: false })
  const saveCustom = () => savePreferences(preferences)

  if (!showBanner) return null

  const toggleClass = "w-9 h-5 bg-white/[.12] rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white/40 after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-white/30 peer-checked:after:bg-white"

  return (
    <>
      <div className="fixed inset-0 bg-black/60 z-40" />

      <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6">
        <div className="max-w-2xl mx-auto bg-[#141414] rounded-xl border border-white/[.08] shadow-2xl">
          {!showSettings ? (
            <div className="p-5">
              <h2 className="text-sm font-semibold text-white/90 mb-2">Cookies</h2>
              <p className="text-[13px] text-white/40 leading-relaxed mb-4">
                We use cookies to keep you signed in and to understand how the site is used.{' '}
                <Link to="/cookies" className="text-white/50 underline hover:text-white/70">Cookie Policy</Link>.
              </p>
              <div className="flex flex-wrap gap-2">
                <button onClick={acceptAll} className="px-4 py-2 text-sm font-medium bg-white text-black rounded-md hover:bg-white/90 transition-colors">
                  Accept All
                </button>
                <button onClick={acceptNecessary} className="px-4 py-2 text-sm font-medium border border-white/[.12] text-white/60 rounded-md hover:text-white hover:border-white/25 transition-colors">
                  Necessary Only
                </button>
                <button onClick={() => setShowSettings(true)} className="px-4 py-2 text-sm text-white/40 hover:text-white/70 transition-colors">
                  Settings
                </button>
              </div>
            </div>
          ) : (
            <div className="p-5">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-sm font-semibold text-white/90">Cookie preferences</h2>
                <button onClick={() => setShowSettings(false)} className="text-white/30 hover:text-white/60 text-sm">Close</button>
              </div>

              <div className="space-y-3 mb-5">
                <div className="rounded-lg border border-white/[.06] bg-white/[.02] p-4">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-sm font-medium text-white/80">Necessary</h3>
                    <span className="text-[11px] text-white/30 border border-white/[.1] rounded px-2 py-0.5">Always on</span>
                  </div>
                  <p className="text-[13px] text-white/35">Authentication, security, session management.</p>
                </div>

                {[
                  { key: 'functional' as const, label: 'Functional', desc: 'Remembers your preferences and settings.' },
                  { key: 'analytics' as const, label: 'Analytics', desc: 'Helps us understand how the site is used.' },
                  { key: 'marketing' as const, label: 'Marketing', desc: 'Currently unused.' },
                ].map((item) => (
                  <div key={item.key} className="rounded-lg border border-white/[.06] bg-white/[.02] p-4">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-medium text-white/80">{item.label}</h3>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={preferences[item.key]}
                          onChange={(e) => setPreferences({ ...preferences, [item.key]: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className={toggleClass} />
                      </label>
                    </div>
                    <p className="text-[13px] text-white/35">{item.desc}</p>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-2 pt-4 border-t border-white/[.06]">
                <button onClick={saveCustom} className="px-4 py-2 text-sm font-medium bg-white text-black rounded-md hover:bg-white/90 transition-colors">
                  Save
                </button>
                <button onClick={acceptAll} className="px-4 py-2 text-sm font-medium border border-white/[.12] text-white/60 rounded-md hover:text-white hover:border-white/25 transition-colors">
                  Accept All
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export function useCookieConsent() {
  const [consent, setConsent] = useState<CookiePreferences | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem(COOKIE_CONSENT_KEY)
    if (stored) setConsent(JSON.parse(stored))

    const handleUpdate = (e: CustomEvent<CookiePreferences>) => setConsent(e.detail)
    window.addEventListener('cookieConsentUpdated', handleUpdate as EventListener)
    return () => window.removeEventListener('cookieConsentUpdated', handleUpdate as EventListener)
  }, [])

  return consent
}

export function CookieSettingsButton() {
  return (
    <button
      onClick={() => { localStorage.removeItem(COOKIE_CONSENT_KEY); window.location.reload() }}
      className="text-sm text-white/40 hover:text-white/70 transition-colors"
    >
      Manage Cookies
    </button>
  )
}

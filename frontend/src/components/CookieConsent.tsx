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
    necessary: true, // Always required
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
      // Check if consent version is current
      if (parsed.consentVersion === CONSENT_VERSION) {
        setPreferences(parsed)
        setShowBanner(false)
      } else {
        // New consent version required
        setShowBanner(true)
      }
    } else {
      // No consent given yet
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
    
    // Dispatch event for other components to react
    window.dispatchEvent(new CustomEvent('cookieConsentUpdated', { detail: updatedPrefs }))
  }

  const acceptAll = () => {
    savePreferences({
      ...preferences,
      functional: true,
      analytics: true,
      marketing: true,
    })
  }

  const acceptNecessary = () => {
    savePreferences({
      ...preferences,
      functional: false,
      analytics: false,
      marketing: false,
    })
  }

  const saveCustom = () => {
    savePreferences(preferences)
  }

  if (!showBanner) return null

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40" />
      
      {/* Cookie Banner */}
      <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6">
        <div className="max-w-4xl mx-auto bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl overflow-hidden">
          {!showSettings ? (
            // Main Banner
            <div className="p-6">
              <div className="flex items-start gap-4">
                <div className="text-3xl">🍪</div>
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-white mb-2">
                    We Value Your Privacy
                  </h2>
                  <p className="text-slate-300 text-sm leading-relaxed mb-4">
                    We use cookies and similar technologies to provide you with the best experience on our platform. 
                    Some cookies are essential for the service to work, while others help us improve your experience 
                    and understand how you use our service.
                  </p>
                  <p className="text-slate-400 text-xs mb-4">
                    By clicking "Accept All", you consent to our use of cookies. You can manage your preferences 
                    or withdraw consent at any time. For more information, see our{' '}
                    <Link to="/cookies" className="text-cyan-400 hover:underline">Cookie Policy</Link>,{' '}
                    <Link to="/privacy" className="text-cyan-400 hover:underline">Privacy Policy</Link>, and{' '}
                    <Link to="/terms" className="text-cyan-400 hover:underline">Terms of Service</Link>.
                  </p>
                  
                  <div className="flex flex-wrap gap-3">
                    <button
                      onClick={acceptAll}
                      className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-600 text-white font-medium rounded-lg transition-colors"
                    >
                      Accept All
                    </button>
                    <button
                      onClick={acceptNecessary}
                      className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors"
                    >
                      Necessary Only
                    </button>
                    <button
                      onClick={() => setShowSettings(true)}
                      className="px-6 py-2.5 border border-slate-600 hover:border-slate-500 text-slate-300 font-medium rounded-lg transition-colors"
                    >
                      Customize Settings
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Settings Panel
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white">Cookie Preferences</h2>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-slate-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 mb-6">
                {/* Necessary Cookies */}
                <div className="bg-slate-700/50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">🔒</span>
                      <h3 className="font-medium text-white">Strictly Necessary</h3>
                    </div>
                    <div className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                      Always Active
                    </div>
                  </div>
                  <p className="text-sm text-slate-400">
                    These cookies are essential for the website to function properly. They enable core functionality 
                    such as security, authentication, and session management. You cannot disable these cookies.
                  </p>
                </div>

                {/* Functional Cookies */}
                <div className="bg-slate-700/50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">⚙️</span>
                      <h3 className="font-medium text-white">Functional</h3>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.functional}
                        onChange={(e) => setPreferences({ ...preferences, functional: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
                    </label>
                  </div>
                  <p className="text-sm text-slate-400">
                    These cookies enable enhanced functionality and personalization, such as remembering your 
                    preferences and settings. Without these, some features may not work properly.
                  </p>
                </div>

                {/* Analytics Cookies */}
                <div className="bg-slate-700/50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">📊</span>
                      <h3 className="font-medium text-white">Analytics</h3>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.analytics}
                        onChange={(e) => setPreferences({ ...preferences, analytics: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
                    </label>
                  </div>
                  <p className="text-sm text-slate-400">
                    These cookies help us understand how visitors interact with our website by collecting and 
                    reporting information anonymously. This helps us improve our service.
                  </p>
                </div>

                {/* Marketing Cookies */}
                <div className="bg-slate-700/50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">📢</span>
                      <h3 className="font-medium text-white">Marketing</h3>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.marketing}
                        onChange={(e) => setPreferences({ ...preferences, marketing: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500"></div>
                    </label>
                  </div>
                  <p className="text-sm text-slate-400">
                    These cookies may be used to deliver relevant advertisements and track campaign effectiveness. 
                    We currently do not use marketing cookies.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-3 pt-4 border-t border-slate-700">
                <button
                  onClick={saveCustom}
                  className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-600 text-white font-medium rounded-lg transition-colors"
                >
                  Save Preferences
                </button>
                <button
                  onClick={acceptAll}
                  className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors"
                >
                  Accept All
                </button>
                <button
                  onClick={() => setShowSettings(false)}
                  className="px-6 py-2.5 border border-slate-600 hover:border-slate-500 text-slate-300 font-medium rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

// Hook to check cookie consent
export function useCookieConsent() {
  const [consent, setConsent] = useState<CookiePreferences | null>(null)

  useEffect(() => {
    const stored = localStorage.getItem(COOKIE_CONSENT_KEY)
    if (stored) {
      setConsent(JSON.parse(stored))
    }

    const handleUpdate = (e: CustomEvent<CookiePreferences>) => {
      setConsent(e.detail)
    }

    window.addEventListener('cookieConsentUpdated', handleUpdate as EventListener)
    return () => window.removeEventListener('cookieConsentUpdated', handleUpdate as EventListener)
  }, [])

  return consent
}

// Component to manage cookies from settings
export function CookieSettingsButton() {
  const openSettings = () => {
    localStorage.removeItem(COOKIE_CONSENT_KEY)
    window.location.reload()
  }

  return (
    <button
      onClick={openSettings}
      className="text-cyan-400 hover:text-cyan-300 text-sm"
    >
      Manage Cookie Preferences
    </button>
  )
}

/**
 * GA4 analytics — consent-aware with Consent Mode v2.
 * gtag.js is always loaded but respects consent state.
 */

const GA_ID = import.meta.env.VITE_GA4_MEASUREMENT_ID || ''

declare global {
  interface Window {
    dataLayer: IArguments[]
    gtag: (...args: unknown[]) => void
  }
}

let initialized = false

/**
 * Initialize GA4. Call once on app mount.
 * Loads gtag.js immediately with consent defaults (denied).
 * Consent update happens after user accepts cookies.
 */
export function initAnalytics() {
  if (!GA_ID || initialized) return
  initialized = true

  // Standard gtag pattern — MUST use `arguments`, not rest params
  window.dataLayer = window.dataLayer || []
  window.gtag = function () {
    // eslint-disable-next-line prefer-rest-params
    window.dataLayer.push(arguments)
  }

  // Consent Mode v2: deny by default, wait for consent update
  window.gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500,
  })

  // Load gtag.js immediately (it respects consent state internally)
  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`
  document.head.appendChild(script)

  window.gtag('js', new Date())
  window.gtag('config', GA_ID, { send_page_view: false })

  // Grant consent if user already accepted
  try {
    const stored = localStorage.getItem('cookie_consent')
    if (stored) {
      const prefs = JSON.parse(stored)
      if (prefs.analytics) {
        window.gtag('consent', 'update', { analytics_storage: 'granted' })
      }
    }
  } catch {
    // ignore
  }

  // Listen for future consent changes
  window.addEventListener('cookieConsentUpdated', ((e: CustomEvent) => {
    window.gtag('consent', 'update', {
      analytics_storage: e.detail?.analytics ? 'granted' : 'denied',
    })
  }) as EventListener)
}

export function trackPageView(path: string) {
  if (!GA_ID || !window.gtag) return
  window.gtag('event', 'page_view', {
    page_path: path,
    page_location: window.location.href,
  })
}

export function trackEvent(name: string, params?: Record<string, unknown>) {
  if (!GA_ID || !window.gtag) return
  window.gtag('event', name, params)
}

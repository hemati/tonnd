/**
 * GA4 analytics — consent-aware, loads gtag.js only after user accepts analytics cookies.
 * Uses Consent Mode v2: denied by default, granted after explicit consent.
 */

const GA_ID = import.meta.env.VITE_GA4_MEASUREMENT_ID || ''

// Extend window for gtag
declare global {
  interface Window {
    dataLayer: unknown[]
    gtag: (...args: unknown[]) => void
  }
}

let initialized = false

function gtag(...args: unknown[]) {
  window.dataLayer = window.dataLayer || []
  window.dataLayer.push(args)
}

/**
 * Initialize GA4 with Consent Mode v2 (denied by default).
 * Call once on app mount. Does NOT load gtag.js yet — only sets up consent defaults.
 */
export function initAnalytics() {
  if (!GA_ID || initialized) return
  initialized = true

  window.dataLayer = window.dataLayer || []
  window.gtag = gtag

  // Consent Mode v2: deny everything by default
  gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
  })

  // Check if user already consented (from previous visit)
  try {
    const stored = localStorage.getItem('cookie_consent')
    if (stored) {
      const prefs = JSON.parse(stored)
      if (prefs.analytics) {
        grantAnalytics()
      }
    }
  } catch {
    // ignore parse errors
  }

  // Listen for future consent changes
  window.addEventListener('cookieConsentUpdated', ((e: CustomEvent) => {
    if (e.detail?.analytics) {
      grantAnalytics()
    } else {
      revokeAnalytics()
    }
  }) as EventListener)
}

/**
 * Load gtag.js script and grant analytics consent.
 */
function grantAnalytics() {
  if (!GA_ID) return

  // Update consent
  gtag('consent', 'update', {
    analytics_storage: 'granted',
  })

  // Load gtag.js if not already loaded
  if (!document.getElementById('gtag-script')) {
    const script = document.createElement('script')
    script.id = 'gtag-script'
    script.async = true
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`
    document.head.appendChild(script)

    gtag('js', new Date())
    gtag('config', GA_ID, {
      send_page_view: false, // we track page views manually on route change
    })
  }
}

/**
 * Revoke analytics consent (user withdrew consent).
 */
function revokeAnalytics() {
  gtag('consent', 'update', {
    analytics_storage: 'denied',
  })
}

/**
 * Track a page view. Call on every route change.
 */
export function trackPageView(path: string) {
  if (!GA_ID) return
  gtag('event', 'page_view', {
    page_path: path,
    page_location: window.location.href,
  })
}

/**
 * Track a custom event.
 */
export function trackEvent(name: string, params?: Record<string, unknown>) {
  if (!GA_ID) return
  gtag('event', name, params)
}

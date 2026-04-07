import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.stubEnv('VITE_GA4_MEASUREMENT_ID', 'G-TEST123')

describe('analytics', () => {
  beforeEach(() => {
    document.head.innerHTML = ''
    ;(window as any).dataLayer = undefined
    ;(window as any).gtag = undefined
    vi.resetModules()
  })

  it('initializes dataLayer and gtag function', async () => {
    const { initAnalytics } = await import('./analytics')
    initAnalytics()
    expect(window.dataLayer).toBeDefined()
    expect(typeof window.gtag).toBe('function')
  })

  it('loads gtag.js script', async () => {
    const { initAnalytics } = await import('./analytics')
    initAnalytics()
    const script = document.querySelector('script[src*="googletagmanager"]')
    expect(script).toBeTruthy()
    expect(script?.getAttribute('src')).toContain('G-TEST123')
  })

  it('trackPageView adds to dataLayer', async () => {
    const { initAnalytics, trackPageView } = await import('./analytics')
    initAnalytics()
    const before = window.dataLayer.length
    trackPageView('/blog')
    expect(window.dataLayer.length).toBeGreaterThan(before)
  })

  it('trackEvent adds to dataLayer', async () => {
    const { initAnalytics, trackEvent } = await import('./analytics')
    initAnalytics()
    const before = window.dataLayer.length
    trackEvent('sign_up', { method: 'email' })
    expect(window.dataLayer.length).toBeGreaterThan(before)
  })

  it('does not initialize twice', async () => {
    const { initAnalytics } = await import('./analytics')
    initAnalytics()
    const scripts1 = document.querySelectorAll('script[src*="googletagmanager"]').length
    initAnalytics()
    const scripts2 = document.querySelectorAll('script[src*="googletagmanager"]').length
    expect(scripts2).toBe(scripts1)
  })
})

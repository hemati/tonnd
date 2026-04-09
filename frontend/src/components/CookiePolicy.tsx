import { Link } from 'react-router-dom'
import { LegalPage, LegalHeading } from './LegalPage'
import { CookieSettingsButton } from './CookieConsent'
import { GITHUB_URL } from '../config/theme'

export function CookiePolicy() {
  return (
    <LegalPage title="Cookie Policy" lastUpdated="April 6, 2026">
      <div className="rounded-lg border border-white/[.06] bg-white/[.02] p-4 flex items-center justify-between gap-4">
        <div>
          <p className="text-white/70 font-medium text-sm">Manage your cookie preferences</p>
          <p className="text-[13px] text-white/35">Change settings at any time.</p>
        </div>
        <CookieSettingsButton />
      </div>

      <section>
        <LegalHeading>1. What Are Cookies?</LegalHeading>
        <p>Cookies are small text files stored on your device when you visit a website. They can be "persistent" (remaining for a set period) or "session" (deleted when you close your browser).</p>
      </section>

      <section>
        <LegalHeading>2. Cookies We Use</LegalHeading>
        <p className="mb-4">TONND uses a small number of cookies:</p>
        <div className="space-y-4">
          <div className="rounded-lg border border-white/[.06] bg-white/[.02] p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-white/80">Essential Cookies</h3>
              <span className="text-[11px] text-white/30 border border-white/[.1] rounded px-2 py-0.5">Always active</span>
            </div>
            <div className="space-y-2 text-[13px]">
              <div className="flex justify-between"><span className="font-mono text-white/40">access_token</span><span className="text-white/30">JWT authentication</span></div>
              <div className="flex justify-between"><span className="font-mono text-white/40">cookie_consent</span><span className="text-white/30">Your cookie preferences</span></div>
            </div>
          </div>
          <div className="rounded-lg border border-white/[.06] bg-white/[.02] p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-white/80">Analytics Cookies</h3>
              <span className="text-[11px] text-white/30 border border-white/[.1] rounded px-2 py-0.5">Requires consent</span>
            </div>
            <p className="text-[13px] text-white/35 mb-3">We use Google Analytics 4 (GA4) with Consent Mode v2. Analytics is denied by default and only activates after you explicitly grant consent.</p>
            <div className="space-y-2 text-[13px]">
              <div className="flex justify-between"><span className="font-mono text-white/40">_ga</span><span className="text-white/30">GA4 client identifier (2 years)</span></div>
              <div className="flex justify-between"><span className="font-mono text-white/40">_ga_*</span><span className="text-white/30">GA4 session state (2 years)</span></div>
            </div>
          </div>
          <div className="rounded-lg border border-white/[.06] bg-white/[.02] p-4">
            <h3 className="text-sm font-semibold text-white/80 mb-2">What we don't use</h3>
            <ul className="list-disc list-inside space-y-1.5 ml-2 text-[13px]">
              <li>No advertising or marketing cookies</li>
              <li>No cross-site tracking</li>
            </ul>
          </div>
        </div>
      </section>

      <section>
        <LegalHeading>3. Third-Party Cookies</LegalHeading>
        <p>During authentication, Google OAuth may set session cookies for sign-in. If you consent to analytics cookies, Google Analytics 4 sets cookies (<code className="text-white/50">_ga</code>, <code className="text-white/50">_ga_*</code>) to collect anonymized usage data. GA4 is loaded with Consent Mode v2, meaning all analytics storage is denied by default until you explicitly opt in.</p>
      </section>

      <section>
        <LegalHeading>4. Managing Cookies</LegalHeading>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Use the cookie preferences panel above</li>
          <li>Your browser settings can block or delete cookies</li>
          <li>Blocking essential cookies may prevent the service from working</li>
        </ul>
      </section>

      <section>
        <LegalHeading>5. Do Not Sell My Information</LegalHeading>
        <p>TONND does not sell personal information. See our <Link to="/privacy#ccpa" className="text-white/60 underline hover:text-white/80">Privacy Policy</Link>.</p>
      </section>

      <section>
        <LegalHeading>6. Contact</LegalHeading>
        <p>Questions? <a href={`${GITHUB_URL}/issues`} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">GitHub Issues</a>.</p>
      </section>
    </LegalPage>
  )
}

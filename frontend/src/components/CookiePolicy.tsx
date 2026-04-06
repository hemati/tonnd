import { Link } from 'react-router-dom'
import { CookieSettingsButton } from './CookieConsent'

export function CookiePolicy() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <Link to="/" className="text-cyan-400 hover:text-cyan-300 flex items-center gap-2 mb-6">
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-white mb-2">Cookie Policy</h1>
          <p className="text-slate-400">Last updated: January 11, 2026</p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 space-y-8 text-slate-300">
          
          {/* Quick Actions */}
          <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4 flex items-center justify-between">
            <div>
              <h3 className="font-medium text-white">Manage Your Cookie Preferences</h3>
              <p className="text-sm text-slate-400">You can change your cookie settings at any time.</p>
            </div>
            <CookieSettingsButton />
          </div>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">1. What Are Cookies?</h2>
            <p className="mb-4">
              Cookies are small text files that are placed on your device (computer, smartphone, or tablet) when you 
              visit a website. They are widely used to make websites work more efficiently and provide information 
              to the website owners.
            </p>
            <p>
              Cookies can be "persistent" (remaining on your device for a set period) or "session" cookies 
              (deleted when you close your browser).
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">2. How We Use Cookies</h2>
            <p className="mb-4">
              TONND uses cookies and similar technologies for the following purposes:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Authentication:</strong> To keep you logged in and secure your session</li>
              <li><strong>Preferences:</strong> To remember your settings and preferences</li>
              <li><strong>Security:</strong> To protect against fraudulent activity</li>
              <li><strong>Performance:</strong> To understand how you use our service and improve it</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">3. Types of Cookies We Use</h2>
            
            <div className="space-y-6">
              {/* Necessary */}
              <div className="bg-slate-700/50 rounded-xl p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">🔒</span>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Strictly Necessary Cookies</h3>
                    <span className="text-xs text-green-400 bg-green-400/10 px-2 py-0.5 rounded">Always Active</span>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  These cookies are essential for the website to function and cannot be disabled. They are usually 
                  set in response to actions you take, such as logging in or filling out forms.
                </p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="pb-2">Cookie Name</th>
                      <th className="pb-2">Purpose</th>
                      <th className="pb-2">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-400">
                    <tr>
                      <td className="py-1 font-mono text-xs">CognitoIdentityServiceProvider.*</td>
                      <td className="py-1">Authentication tokens</td>
                      <td className="py-1">Session/30 days</td>
                    </tr>
                    <tr>
                      <td className="py-1 font-mono text-xs">cookie_consent</td>
                      <td className="py-1">Stores your cookie preferences</td>
                      <td className="py-1">1 year</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Functional */}
              <div className="bg-slate-700/50 rounded-xl p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">⚙️</span>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Functional Cookies</h3>
                    <span className="text-xs text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded">Optional</span>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  These cookies enable enhanced functionality and personalization. If you disable these, 
                  some features may not work as expected.
                </p>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="pb-2">Cookie Name</th>
                      <th className="pb-2">Purpose</th>
                      <th className="pb-2">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="text-slate-400">
                    <tr>
                      <td className="py-1 font-mono text-xs">user_preferences</td>
                      <td className="py-1">Dashboard layout and theme preferences</td>
                      <td className="py-1">1 year</td>
                    </tr>
                    <tr>
                      <td className="py-1 font-mono text-xs">last_sync_reminder</td>
                      <td className="py-1">Tracks when to show sync reminders</td>
                      <td className="py-1">7 days</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Analytics */}
              <div className="bg-slate-700/50 rounded-xl p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">📊</span>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Analytics Cookies</h3>
                    <span className="text-xs text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded">Optional</span>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  These cookies help us understand how visitors interact with our website. All data is anonymized 
                  and aggregated. We currently do NOT use third-party analytics services.
                </p>
                <p className="text-sm text-green-400">
                  ✓ We do not use Google Analytics or similar third-party tracking
                </p>
              </div>

              {/* Marketing */}
              <div className="bg-slate-700/50 rounded-xl p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">📢</span>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Marketing Cookies</h3>
                    <span className="text-xs text-purple-400 bg-purple-400/10 px-2 py-0.5 rounded">Optional</span>
                  </div>
                </div>
                <p className="text-sm text-slate-400 mb-4">
                  Marketing cookies may be used to track visitors across websites and display relevant advertisements.
                </p>
                <p className="text-sm text-green-400">
                  ✓ We do NOT use marketing or advertising cookies
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">4. Third-Party Cookies</h2>
            <p className="mb-4">
              Some cookies may be set by third-party services that appear on our pages:
            </p>
            <div className="bg-slate-700/50 rounded-xl p-4 space-y-3">
              <div className="flex items-start gap-3">
                <span className="text-xl">🔐</span>
                <div>
                  <h4 className="font-medium text-white">Amazon Cognito (AWS)</h4>
                  <p className="text-sm text-slate-400">Authentication service - sets session cookies for secure login</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-xl">🌐</span>
                <div>
                  <h4 className="font-medium text-white">Google OAuth</h4>
                  <p className="text-sm text-slate-400">Single sign-on authentication when you log in with Google</p>
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">5. Managing Cookies</h2>
            <p className="mb-4">
              You have several options for managing cookies:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Our Cookie Settings:</strong> Use the cookie preferences panel to control which optional cookies we use</li>
              <li><strong>Browser Settings:</strong> Most browsers allow you to block or delete cookies through their settings</li>
              <li><strong>Device Settings:</strong> Mobile devices have settings to limit ad tracking</li>
            </ul>
            
            <div className="mt-4 bg-amber-500/10 border border-amber-500/20 rounded-xl p-4">
              <p className="text-amber-300 text-sm">
                ⚠️ <strong>Note:</strong> Blocking essential cookies may prevent you from using our service, 
                as they are required for authentication and security.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">6. Your Rights</h2>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4">
                <h3 className="font-semibold text-white mb-2 flex items-center gap-2">
                  <span>🇪🇺</span> EU/EEA Residents (GDPR)
                </h3>
                <ul className="text-sm text-slate-400 space-y-1">
                  <li>• Right to access your data</li>
                  <li>• Right to rectification</li>
                  <li>• Right to erasure</li>
                  <li>• Right to restrict processing</li>
                  <li>• Right to data portability</li>
                  <li>• Right to withdraw consent</li>
                </ul>
              </div>
              
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
                <h3 className="font-semibold text-white mb-2 flex items-center gap-2">
                  <span>🇺🇸</span> US Residents (CCPA/CPRA)
                </h3>
                <ul className="text-sm text-slate-400 space-y-1">
                  <li>• Right to know what data is collected</li>
                  <li>• Right to delete personal information</li>
                  <li>• Right to opt-out of sale/sharing</li>
                  <li>• Right to non-discrimination</li>
                  <li>• Right to correct inaccurate data</li>
                  <li>• Right to limit sensitive data use</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">7. Do Not Sell My Personal Information</h2>
            <p className="mb-4">
              Under the California Consumer Privacy Act (CCPA) and other US state privacy laws, you have the right 
              to opt out of the "sale" or "sharing" of your personal information.
            </p>
            <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4">
              <p className="text-green-400 font-medium">
                ✓ TONND does NOT sell your personal information to third parties.
              </p>
              <p className="text-slate-400 text-sm mt-2">
                We do not share your health data with advertisers, data brokers, or any third parties for monetary 
                or other valuable consideration.
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">8. Changes to This Policy</h2>
            <p>
              We may update this Cookie Policy from time to time. If we make significant changes, we will notify 
              you by updating the "Last updated" date and, if necessary, requesting your consent again through 
              the cookie banner.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">9. Contact Us</h2>
            <p className="mb-4">
              If you have questions about our use of cookies, please contact us:
            </p>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <p><strong>Contact:</strong> <a href="https://github.com/hemati/tonnd/issues" className="text-cyan-400 underline">GitHub Issues</a></p>
            </div>
          </section>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center text-slate-400">
          <Link to="/terms" className="text-cyan-400 hover:text-cyan-300">Terms of Service</Link>
          <span className="mx-4">|</span>
          <Link to="/privacy" className="text-cyan-400 hover:text-cyan-300">Privacy Policy</Link>
          <span className="mx-4">|</span>
          <Link to="/" className="text-cyan-400 hover:text-cyan-300">Back to Home</Link>
        </div>
      </div>
    </div>
  )
}

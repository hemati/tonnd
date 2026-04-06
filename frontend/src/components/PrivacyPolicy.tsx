import { Link } from 'react-router-dom'

export function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <Link to="/" className="text-cyan-400 hover:text-cyan-300 flex items-center gap-2 mb-6">
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-white mb-2">Privacy Policy</h1>
          <p className="text-slate-400">Last updated: January 11, 2026</p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 space-y-8 text-slate-300">
          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">1. Introduction</h2>
            <p>
              At TONND ("we", "our", or "us"), we take your privacy seriously. This Privacy Policy 
              explains how we collect, use, disclose, and safeguard your information when you use our health 
              data aggregation service. Please read this policy carefully.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">2. Information We Collect</h2>
            
            <h3 className="text-xl font-medium text-white mt-6 mb-3">2.1 Account Information</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Email address (from Google authentication)</li>
              <li>Name (from Google profile)</li>
              <li>Profile picture (optional, from Google)</li>
              <li>Account creation date</li>
            </ul>

            <h3 className="text-xl font-medium text-white mt-6 mb-3">2.2 Health and Fitness Data</h3>
            <p className="mb-3">With your explicit consent, we collect data from connected services including:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Activity Data:</strong> Steps, distance, calories burned, active minutes, floors climbed</li>
              <li><strong>Sleep Data:</strong> Sleep duration, sleep stages (deep, light, REM), sleep efficiency</li>
              <li><strong>Heart Data:</strong> Resting heart rate, heart rate zones, HRV (Heart Rate Variability)</li>
              <li><strong>Body Metrics:</strong> Weight, BMI, body fat percentage</li>
              <li><strong>Vital Signs:</strong> SpO2 (blood oxygen), breathing rate, skin temperature</li>
              <li><strong>Fitness Metrics:</strong> VO2 Max, Active Zone Minutes, cardio fitness score</li>
            </ul>

            <h3 className="text-xl font-medium text-white mt-6 mb-3">2.3 Technical Data</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>IP address and approximate location</li>
              <li>Browser type and version</li>
              <li>Device information</li>
              <li>Usage patterns and feature interactions</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">3. How We Use Your Information</h2>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Service Delivery:</strong> To provide, maintain, and improve our health tracking services</li>
              <li><strong>Personalization:</strong> To customize your dashboard and provide relevant insights</li>
              <li><strong>AI Recommendations:</strong> To generate personalized health and fitness suggestions based on your goals</li>
              <li><strong>Analytics:</strong> To understand usage patterns and improve our service</li>
              <li><strong>Communication:</strong> To send important updates about your account or our service</li>
              <li><strong>Security:</strong> To detect, prevent, and address technical issues or fraudulent activity</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">4. Data Storage and Security</h2>
            
            <h3 className="text-xl font-medium text-white mt-6 mb-3">4.1 Where We Store Your Data</h3>
            <p className="mb-3">Your data is stored securely on Amazon Web Services (AWS) servers located in the European Union (Frankfurt, Germany - eu-central-1).</p>
            
            <h3 className="text-xl font-medium text-white mt-6 mb-3">4.2 Security Measures</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Encryption at Rest:</strong> All health data is encrypted using AWS KMS (Key Management Service)</li>
              <li><strong>Encryption in Transit:</strong> All data transfers use TLS 1.2 or higher</li>
              <li><strong>Token Security:</strong> Third-party OAuth tokens are encrypted before storage</li>
              <li><strong>Access Control:</strong> Strict IAM policies limit data access to authorized services only</li>
              <li><strong>Authentication:</strong> Secure authentication via AWS Cognito and Google OAuth 2.0</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">5. Third-Party Services</h2>
            <p className="mb-4">We integrate with the following third-party services:</p>
            
            <div className="space-y-4">
              <div className="bg-slate-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-white">Fitbit</h4>
                <p className="text-sm">Activity, sleep, heart rate, and health metrics</p>
                <a href="https://www.fitbit.com/legal/privacy-policy" className="text-cyan-400 text-sm hover:underline" target="_blank" rel="noopener noreferrer">
                  View Fitbit Privacy Policy →
                </a>
              </div>
              
              <div className="bg-slate-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-white">Google</h4>
                <p className="text-sm">Authentication and account management</p>
                <a href="https://policies.google.com/privacy" className="text-cyan-400 text-sm hover:underline" target="_blank" rel="noopener noreferrer">
                  View Google Privacy Policy →
                </a>
              </div>
              
              <div className="bg-slate-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-white">Renpho (Coming Soon)</h4>
                <p className="text-sm">Weight and body composition data</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">6. Data Sharing</h2>
            <p className="mb-4 text-green-400 font-medium">
              ✓ We do NOT sell your personal or health data to third parties.
            </p>
            <p className="mb-4">We may share your information only in the following circumstances:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>With Your Consent:</strong> When you explicitly authorize sharing</li>
              <li><strong>Service Providers:</strong> With trusted vendors who assist in operating our service (AWS)</li>
              <li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
              <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
            </ul>
          </section>

          <section id="gdpr">
            <h2 className="text-2xl font-semibold text-white mb-4">7. Your Rights (GDPR) 🇪🇺</h2>
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4 mb-4">
              <p className="text-blue-300 text-sm">
                This section applies to residents of the European Union, European Economic Area, and the United Kingdom.
              </p>
            </div>
            <p className="mb-4">Under the General Data Protection Regulation (GDPR), you have the right to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Rectification:</strong> Request correction of inaccurate data</li>
              <li><strong>Erasure:</strong> Request deletion of your data ("right to be forgotten")</li>
              <li><strong>Portability:</strong> Receive your data in a structured, machine-readable format</li>
              <li><strong>Restriction:</strong> Request limitation of processing</li>
              <li><strong>Objection:</strong> Object to processing of your personal data</li>
              <li><strong>Withdraw Consent:</strong> Revoke consent at any time</li>
            </ul>
            <p className="mt-4">
              <strong>Legal Basis for Processing:</strong> We process your data based on:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4 mt-2">
              <li><strong>Consent:</strong> You explicitly consent to health data collection when connecting devices</li>
              <li><strong>Contract:</strong> Processing is necessary to provide our service to you</li>
              <li><strong>Legitimate Interests:</strong> For security, fraud prevention, and service improvement</li>
            </ul>
            <p className="mt-4">
              To exercise these rights, contact us at <span className="text-cyan-400">GitHub Issues</span>
            </p>
            <p className="mt-2 text-sm text-slate-400">
              You also have the right to lodge a complaint with your local data protection authority.
            </p>
          </section>

          <section id="ccpa">
            <h2 className="text-2xl font-semibold text-white mb-4">8. Your Rights (CCPA/CPRA) 🇺🇸</h2>
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-4">
              <p className="text-red-300 text-sm">
                This section applies to California residents under the California Consumer Privacy Act (CCPA) and 
                California Privacy Rights Act (CPRA).
              </p>
            </div>
            
            <h3 className="text-xl font-medium text-white mt-6 mb-3">Your Rights</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Right to Know:</strong> Request what personal information we collect, use, and disclose</li>
              <li><strong>Right to Delete:</strong> Request deletion of your personal information</li>
              <li><strong>Right to Correct:</strong> Request correction of inaccurate information</li>
              <li><strong>Right to Portability:</strong> Receive your data in a portable format</li>
              <li><strong>Right to Opt-Out:</strong> Opt out of sale or sharing of personal information</li>
              <li><strong>Right to Limit:</strong> Limit use of sensitive personal information</li>
              <li><strong>Right to Non-Discrimination:</strong> We will not discriminate against you for exercising your rights</li>
            </ul>

            <h3 className="text-xl font-medium text-white mt-6 mb-3" id="do-not-sell">Do Not Sell or Share My Personal Information</h3>
            <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4">
              <p className="text-green-400 font-medium mb-2">
                ✓ TONND does NOT sell your personal information.
              </p>
              <p className="text-slate-400 text-sm">
                We do not sell, rent, or share your personal information or health data with third parties for 
                monetary consideration or cross-context behavioral advertising. Your health data is never shared 
                with advertisers, data brokers, or marketing companies.
              </p>
            </div>

            <h3 className="text-xl font-medium text-white mt-6 mb-3">Categories of Personal Information Collected</h3>
            <table className="w-full text-sm mt-4 border border-slate-600 rounded-lg overflow-hidden">
              <thead className="bg-slate-700">
                <tr>
                  <th className="text-left p-3">Category</th>
                  <th className="text-left p-3">Examples</th>
                  <th className="text-left p-3">Sold?</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-slate-600">
                  <td className="p-3">Identifiers</td>
                  <td className="p-3 text-slate-400">Email, name, account ID</td>
                  <td className="p-3 text-green-400">No</td>
                </tr>
                <tr className="border-t border-slate-600">
                  <td className="p-3">Protected Health Information</td>
                  <td className="p-3 text-slate-400">Heart rate, sleep, weight, activity</td>
                  <td className="p-3 text-green-400">No</td>
                </tr>
                <tr className="border-t border-slate-600">
                  <td className="p-3">Internet Activity</td>
                  <td className="p-3 text-slate-400">Browser type, IP address</td>
                  <td className="p-3 text-green-400">No</td>
                </tr>
                <tr className="border-t border-slate-600">
                  <td className="p-3">Inferences</td>
                  <td className="p-3 text-slate-400">Health insights, AI recommendations</td>
                  <td className="p-3 text-green-400">No</td>
                </tr>
              </tbody>
            </table>

            <p className="mt-4">
              To exercise your CCPA rights, contact us at <span className="text-cyan-400">GitHub Issues</span> 
              or call us at <span className="text-cyan-400">+1 (555) 123-4567</span>.
            </p>
            <p className="text-sm text-slate-400 mt-2">
              We will verify your identity before processing your request. Response time: within 45 days.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">9. Additional State Privacy Rights</h2>
            <p className="mb-4">
              If you are a resident of Virginia, Colorado, Connecticut, Utah, or other states with consumer 
              privacy laws, you may have similar rights to those described in the CCPA section above.
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-2">Virginia (VCDPA)</h4>
                <p className="text-sm text-slate-400">Access, correct, delete, portability, opt-out of targeted advertising</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-2">Colorado (CPA)</h4>
                <p className="text-sm text-slate-400">Access, correct, delete, portability, opt-out of profiling</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-2">Connecticut (CTDPA)</h4>
                <p className="text-sm text-slate-400">Access, correct, delete, portability, opt-out of sale</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-2">Utah (UCPA)</h4>
                <p className="text-sm text-slate-400">Access, delete, portability, opt-out of targeted advertising</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">10. Data Retention</h2>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Active Accounts:</strong> Data is retained as long as your account is active</li>
              <li><strong>Deleted Accounts:</strong> Data is permanently deleted within 30 days of account deletion</li>
              <li><strong>Legal Requirements:</strong> Some data may be retained longer if required by law</li>
              <li><strong>Anonymized Data:</strong> Aggregated, anonymized data may be retained for analytics</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">11. Cookies and Tracking</h2>
            <p className="mb-4">For detailed information about our cookie practices, please see our <Link to="/cookies" className="text-cyan-400 hover:underline">Cookie Policy</Link>.</p>
            <p className="mb-4">We use minimal cookies essential for service operation:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li><strong>Authentication Cookies:</strong> To keep you logged in</li>
              <li><strong>Session Cookies:</strong> To maintain your session state</li>
              <li><strong>Preference Cookies:</strong> To remember your settings</li>
            </ul>
            <p className="mt-4">We do NOT use third-party advertising or tracking cookies.</p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">12. Children's Privacy</h2>
            <p>
              Our Service is not intended for children under 16 years of age. We do not knowingly collect 
              personal information from children under 16. If you believe we have collected data from a child 
              under 16, please contact us immediately.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">13. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of significant changes 
              by email or through a notice on our Service. The "Last updated" date at the top indicates when 
              the policy was last revised.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">14. Contact Us</h2>
            <p className="mb-4">
              If you have questions or concerns about this Privacy Policy or our data practices, please contact us:
            </p>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <p><strong>Email:</strong> <span className="text-cyan-400">GitHub Issues</span></p>
              <p className="mt-2"><strong>Data Protection Officer:</strong> <span className="text-cyan-400">GitHub Issues</span></p>
            </div>
          </section>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center text-slate-400">
          <Link to="/terms" className="text-cyan-400 hover:text-cyan-300">Terms of Service</Link>
          <span className="mx-4">|</span>
          <Link to="/cookies" className="text-cyan-400 hover:text-cyan-300">Cookie Policy</Link>
          <span className="mx-4">|</span>
          <Link to="/" className="text-cyan-400 hover:text-cyan-300">Back to Home</Link>
        </div>
      </div>
    </div>
  )
}

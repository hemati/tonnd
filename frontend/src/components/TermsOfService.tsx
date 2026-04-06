import { Link } from 'react-router-dom'

export function TermsOfService() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <Link to="/" className="text-cyan-400 hover:text-cyan-300 flex items-center gap-2 mb-6">
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-white mb-2">Terms of Service</h1>
          <p className="text-slate-400">Last updated: January 11, 2026</p>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700/50 space-y-8 text-slate-300">
          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">1. Acceptance of Terms</h2>
            <p>
              By accessing and using TONND ("the Service"), you accept and agree to be bound by these Terms of Service. 
              If you do not agree to these terms, please do not use our Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">2. Description of Service</h2>
            <p className="mb-4">
              TONND is a health data aggregation platform that:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Connects to various health and fitness tracking devices and services (Fitbit, Renpho, and more)</li>
              <li>Aggregates your health data in one centralized dashboard</li>
              <li>Provides AI-powered insights and recommendations based on your goals</li>
              <li>Helps you track progress toward your health and fitness objectives</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">3. User Accounts</h2>
            <p className="mb-4">
              To use our Service, you must:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Be at least 18 years old or have parental consent</li>
              <li>Create an account using Google authentication</li>
              <li>Provide accurate and complete information</li>
              <li>Maintain the security of your account credentials</li>
              <li>Notify us immediately of any unauthorized access</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">4. Health Data and Medical Disclaimer</h2>
            <p className="mb-4 text-amber-400 font-medium">
              ⚠️ Important: TONND is NOT a medical device and does NOT provide medical advice.
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>The Service is for informational and educational purposes only</li>
              <li>AI-generated recommendations are not substitutes for professional medical advice</li>
              <li>Always consult with a qualified healthcare provider before making health decisions</li>
              <li>Do not disregard professional medical advice based on information from our Service</li>
              <li>In case of medical emergency, contact emergency services immediately</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">5. Third-Party Integrations</h2>
            <p className="mb-4">
              Our Service connects to third-party services including but not limited to:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Fitbit - Activity, sleep, and health metrics</li>
              <li>Renpho - Weight and body composition data</li>
              <li>Google - Authentication services</li>
            </ul>
            <p className="mt-4">
              Your use of these third-party services is subject to their respective terms of service and privacy policies. 
              We are not responsible for the practices of these third-party services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">6. Acceptable Use</h2>
            <p className="mb-4">You agree NOT to:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Use the Service for any unlawful purpose</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Interfere with or disrupt the Service</li>
              <li>Share your account credentials with others</li>
              <li>Use automated systems to access the Service without permission</li>
              <li>Reverse engineer or attempt to extract source code</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">7. Intellectual Property</h2>
            <p>
              All content, features, and functionality of the Service are owned by TONND and are protected 
              by international copyright, trademark, and other intellectual property laws. You may not copy, modify, 
              distribute, or create derivative works without our express written permission.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">8. Data Retention and Deletion</h2>
            <p className="mb-4">
              You have the right to:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Request a copy of your data at any time</li>
              <li>Request deletion of your account and associated data</li>
              <li>Disconnect third-party integrations and revoke data access</li>
            </ul>
            <p className="mt-4">
              Upon account deletion, we will remove your personal data within 30 days, except where retention 
              is required by law.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">9. Limitation of Liability</h2>
            <p>
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, AI HEALTH COACH SHALL NOT BE LIABLE FOR ANY INDIRECT, 
              INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF 
              PROFITS, DATA, OR HEALTH OUTCOMES, ARISING FROM YOUR USE OF THE SERVICE.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">10. Changes to Terms</h2>
            <p>
              We reserve the right to modify these Terms at any time. We will notify users of significant changes 
              via email or through the Service. Continued use of the Service after changes constitutes acceptance 
              of the modified Terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">11. Governing Law</h2>
            <p>
              These Terms shall be governed by and construed in accordance with the laws of the European Union 
              and the Federal Republic of Germany, without regard to conflict of law principles.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-white mb-4">12. Contact Us</h2>
            <p>
              If you have any questions about these Terms of Service, please contact us at:
            </p>
            <p className="mt-2 text-cyan-400">
              <a href="https://github.com/hemati/tonnd/issues" className="underline">GitHub Issues</a>
            </p>
          </section>
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-center text-slate-400">
          <Link to="/privacy" className="text-cyan-400 hover:text-cyan-300">Privacy Policy</Link>
          <span className="mx-4">|</span>
          <Link to="/" className="text-cyan-400 hover:text-cyan-300">Back to Home</Link>
        </div>
      </div>
    </div>
  )
}

import { Link } from 'react-router-dom'
import { LegalPage, LegalHeading, LegalSubheading } from './LegalPage'
import { GITHUB_URL } from '../config/theme'

export function PrivacyPolicy() {
  return (
    <LegalPage title="Privacy Policy" lastUpdated="April 6, 2026">
      <section>
        <LegalHeading>1. Introduction</LegalHeading>
        <p>TONND ("we", "our", or "us") takes your privacy seriously. This policy explains how we collect, use, and safeguard your information. TONND is open source and can be self-hosted — when self-hosted, you control all data storage and processing.</p>
      </section>

      <section>
        <LegalHeading>2. Information We Collect</LegalHeading>

        <LegalSubheading>2.1 Account Information</LegalSubheading>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Email address (from Google OAuth or registration)</li>
          <li>Hashed password (if using email/password login)</li>
          <li>Account creation date</li>
        </ul>

        <LegalSubheading>2.2 Health and Fitness Data</LegalSubheading>
        <p className="mb-2">With your explicit consent, we collect data from connected services:</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Activity: steps, distance, calories, active minutes, floors</li>
          <li>Sleep: duration, stages (deep, light, REM), efficiency</li>
          <li>Heart: resting heart rate, zones, HRV</li>
          <li>Body: weight, BMI, body fat, muscle mass, body composition</li>
          <li>Vitals: SpO2, breathing rate, skin temperature, VO2 Max</li>
        </ul>

        <LegalSubheading>2.3 Technical Data</LegalSubheading>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>IP address (for security purposes)</li>
          <li>Browser type and version</li>
        </ul>
      </section>

      <section>
        <LegalHeading>3. How We Use Your Information</LegalHeading>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>To provide and maintain the health tracking service</li>
          <li>To display your data on your personal dashboard</li>
          <li>To sync data from connected devices (Fitbit, Renpho)</li>
          <li>To detect and prevent security issues</li>
        </ul>
      </section>

      <section>
        <LegalHeading>4. Data Storage and Security</LegalHeading>

        <LegalSubheading>4.1 Hosted Version (tonnd.com)</LegalSubheading>
        <p className="mb-2">Data is stored on servers in the European Union (Frankfurt, Germany).</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>OAuth tokens are encrypted at rest using Fernet symmetric encryption</li>
          <li>All data transfers use TLS encryption</li>
          <li>Passwords are hashed with Argon2</li>
          <li>Database: PostgreSQL with standard access controls</li>
        </ul>

        <LegalSubheading>4.2 Self-Hosted</LegalSubheading>
        <p>When you self-host TONND, all data remains on your own server. We have no access to your data.</p>
      </section>

      <section>
        <LegalHeading>5. Third-Party Services</LegalHeading>
        <div className="space-y-3">
          {[
            { name: 'Fitbit', desc: 'Activity, sleep, heart rate, and health metrics via OAuth', url: 'https://www.fitbit.com/legal/privacy-policy' },
            { name: 'Renpho', desc: 'Weight and body composition via cloud API', url: 'https://renpho.com/pages/privacy-policy' },
            { name: 'Google', desc: 'Authentication (OAuth 2.0)', url: 'https://policies.google.com/privacy' },
          ].map((s) => (
            <div key={s.name} className="rounded-lg border border-white/[.06] bg-white/[.02] p-4">
              <h4 className="font-semibold text-white/80 text-sm">{s.name}</h4>
              <p>{s.desc}</p>
              <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-white/50 underline hover:text-white/70 text-[13px]">{s.name} Privacy Policy</a>
            </div>
          ))}
        </div>
      </section>

      <section>
        <LegalHeading>6. Data Sharing</LegalHeading>
        <p className="text-white/60 font-medium mb-3">We do NOT sell your personal or health data.</p>
        <p className="mb-2">We may share information only:</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>With your explicit consent</li>
          <li>With infrastructure providers necessary to run the service</li>
          <li>When required by law</li>
        </ul>
      </section>

      <section id="gdpr">
        <LegalHeading>7. Your Rights (GDPR)</LegalHeading>
        <p className="text-[13px] text-white/30 mb-3">Applies to EU/EEA/UK residents.</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Access — request a copy of your personal data</li>
          <li>Rectification — request correction of inaccurate data</li>
          <li>Erasure — request deletion ("right to be forgotten")</li>
          <li>Portability — receive data in a machine-readable format</li>
          <li>Restriction — limit processing of your data</li>
          <li>Objection — object to processing</li>
          <li>Withdraw consent at any time</li>
        </ul>
        <p className="mt-3">Legal basis: consent (device connections), contract (service delivery), legitimate interests (security).</p>
        <p className="mt-2">To exercise these rights: <a href={`${GITHUB_URL}/issues`} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">GitHub Issues</a>.</p>
      </section>

      <section id="ccpa">
        <LegalHeading>8. Your Rights (CCPA/CPRA)</LegalHeading>
        <p className="text-[13px] text-white/30 mb-3">Applies to California residents.</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Right to know what personal information we collect</li>
          <li>Right to delete your personal information</li>
          <li>Right to correct inaccurate information</li>
          <li>Right to opt-out of sale of personal information</li>
          <li>Right to non-discrimination</li>
        </ul>
        <div className="rounded-lg border border-white/[.06] bg-white/[.02] p-4 mt-4">
          <p className="text-white/60 font-medium mb-1">We do NOT sell your personal information.</p>
          <p>We do not sell, rent, or share your data with third parties for advertising or monetary consideration.</p>
        </div>
        <p className="mt-3">To exercise your rights: <a href={`${GITHUB_URL}/issues`} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">GitHub Issues</a>. Response time: within 45 days.</p>
      </section>

      <section>
        <LegalHeading>9. Data Retention</LegalHeading>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Active accounts: data retained while account is active</li>
          <li>Deleted accounts: data removed within 30 days</li>
          <li>Legal requirements may extend retention</li>
        </ul>
      </section>

      <section>
        <LegalHeading>10. Cookies</LegalHeading>
        <p className="mb-2">We use minimal, essential cookies only:</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Authentication token (JWT in localStorage)</li>
          <li>Cookie consent preference</li>
        </ul>
        <p className="mt-2">No advertising or tracking cookies. See our <Link to="/cookies" className="text-white/60 underline hover:text-white/80">Cookie Policy</Link>.</p>
      </section>

      <section>
        <LegalHeading>11. Children's Privacy</LegalHeading>
        <p>The Service is not intended for children under 16. We do not knowingly collect data from children.</p>
      </section>

      <section>
        <LegalHeading>12. Changes</LegalHeading>
        <p>We may update this policy. The "Last updated" date indicates the most recent revision.</p>
      </section>

      <section>
        <LegalHeading>13. Contact</LegalHeading>
        <p>Questions? <a href={`${GITHUB_URL}/issues`} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">GitHub Issues</a>.</p>
      </section>
    </LegalPage>
  )
}

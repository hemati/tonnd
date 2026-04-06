import { LegalPage, LegalHeading } from './LegalPage'
import { GITHUB_URL } from '../config/theme'

export function TermsOfService() {
  return (
    <LegalPage title="Terms of Service" lastUpdated="April 6, 2026">
      <section>
        <LegalHeading>1. Acceptance of Terms</LegalHeading>
        <p>By accessing and using TONND ("the Service"), you accept and agree to be bound by these Terms of Service. If you do not agree, do not use the Service.</p>
      </section>

      <section>
        <LegalHeading>2. Description of Service</LegalHeading>
        <p className="mb-3">TONND is an open-source, self-hosted health data platform that:</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Connects to Fitbit and Renpho smart scales via their APIs</li>
          <li>Aggregates health data in a unified dashboard</li>
          <li>Provides trend analysis and recovery scoring</li>
          <li>Can be self-hosted on your own server via Docker</li>
        </ul>
      </section>

      <section>
        <LegalHeading>3. User Accounts</LegalHeading>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>You must be at least 16 years old</li>
          <li>You may create an account via Google OAuth or email/password</li>
          <li>You are responsible for maintaining the security of your credentials</li>
          <li>Notify us immediately of any unauthorized access</li>
        </ul>
      </section>

      <section>
        <LegalHeading>4. Medical Disclaimer</LegalHeading>
        <p className="text-white/60 font-medium mb-3">TONND is NOT a medical device and does NOT provide medical advice.</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>The Service is for informational purposes only</li>
          <li>Always consult a qualified healthcare provider before making health decisions</li>
          <li>Do not disregard medical advice based on information from this Service</li>
          <li>In a medical emergency, contact emergency services immediately</li>
        </ul>
      </section>

      <section>
        <LegalHeading>5. Third-Party Integrations</LegalHeading>
        <p className="mb-3">The Service connects to:</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Fitbit — activity, sleep, heart rate, and health metrics</li>
          <li>Renpho — weight and body composition data</li>
          <li>Google — authentication</li>
        </ul>
        <p className="mt-3">Your use of these services is subject to their respective terms and privacy policies.</p>
      </section>

      <section>
        <LegalHeading>6. Open Source License</LegalHeading>
        <p>TONND is licensed under the <a href={`${GITHUB_URL}/blob/main/LICENSE`} target="_blank" rel="noopener noreferrer" className="text-white/70 underline hover:text-white">GNU Affero General Public License v3.0 (AGPL-3.0)</a>. You may copy, modify, and distribute the software under the terms of this license. If you modify or deploy the software, you must make your source code available.</p>
      </section>

      <section>
        <LegalHeading>7. Acceptable Use</LegalHeading>
        <p className="mb-3">You agree not to:</p>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>Use the Service for any unlawful purpose</li>
          <li>Attempt unauthorized access to our systems</li>
          <li>Interfere with or disrupt the Service</li>
          <li>Use automated systems to access the Service without permission</li>
        </ul>
      </section>

      <section>
        <LegalHeading>8. Data Retention and Deletion</LegalHeading>
        <ul className="list-disc list-inside space-y-1.5 ml-2">
          <li>You may request a copy of your data at any time</li>
          <li>You may request deletion of your account and all associated data</li>
          <li>You may disconnect third-party integrations and revoke data access</li>
          <li>Upon account deletion, data is removed within 30 days</li>
        </ul>
      </section>

      <section>
        <LegalHeading>9. Limitation of Liability</LegalHeading>
        <p>TO THE MAXIMUM EXTENT PERMITTED BY LAW, TONND SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM YOUR USE OF THE SERVICE.</p>
      </section>

      <section>
        <LegalHeading>10. Changes to Terms</LegalHeading>
        <p>We may modify these Terms at any time. Continued use of the Service after changes constitutes acceptance.</p>
      </section>

      <section>
        <LegalHeading>11. Governing Law</LegalHeading>
        <p>These Terms are governed by the laws of the European Union and the Federal Republic of Germany.</p>
      </section>

      <section>
        <LegalHeading>12. Contact</LegalHeading>
        <p>Questions? Open an issue on <a href={`${GITHUB_URL}/issues`} target="_blank" rel="noopener noreferrer" className="text-white/70 underline hover:text-white">GitHub</a>.</p>
      </section>
    </LegalPage>
  )
}

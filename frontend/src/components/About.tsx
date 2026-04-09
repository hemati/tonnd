import { Link } from 'react-router-dom'
import { GITHUB_URL, DISCORD_URL, LOGO_PATH } from '../config/theme'
import SEO from './SEO'

export default function About() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <SEO title="About" description="TONND is built by Wahed Hemati — a developer who has been tracking health data in spreadsheets since he was 12." path="/about" />

      {/* nav */}
      <div className="max-w-3xl mx-auto px-5">
        <div className="h-14 flex items-center">
          <Link to="/" className="flex items-center gap-2 group">
            <svg viewBox="0 0 24 24" className="w-5 h-5 text-white/70 group-hover:text-white transition-colors" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
              <path d={LOGO_PATH} />
            </svg>
            <span className="text-sm font-semibold text-white/90">TONND</span>
          </Link>
        </div>
      </div>

      {/* content */}
      <div className="max-w-3xl mx-auto px-5 py-16">
        <h1 className="text-3xl font-bold mb-8">About TONND</h1>

        <div className="space-y-6 text-[15px] text-white/50 leading-relaxed">
          <p>
            TONND is built by <strong className="text-white/80">Wahed Hemati</strong>, a developer based in Germany.
          </p>

          <p>
            The idea started simple: I've been tracking my body data in spreadsheets since I was 12.
            Back then it was a bathroom scale and an Excel sheet. Today it's Fitbit, Renpho smart scales,
            and a dozen health metrics that live in five different apps. The devices got better. The central
            dashboard that ties it all together never got built. So I'm building it.
          </p>

          <p>
            TONND is an open-source, self-hosted health tracking platform. You connect your Fitbit and
            Renpho scale, and everything shows up in one dashboard: weight, sleep, steps, heart rate, HRV,
            VO&#x2082; Max, SpO&#x2082;, body composition. It runs on Docker, you own the data, and the source code is
            on GitHub for anyone to read, fork, or contribute to.
          </p>

          <p>
            The project is licensed under AGPL-3.0. If you modify or deploy it, you must make your
            source code available.
          </p>

          <h2 className="text-xl font-bold text-white/90 pt-4">Where to find me</h2>

          <div className="space-y-2">
            <p>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">GitHub</a> — Source code, issues, contributions
            </p>
            <p>
              <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">Discord</a> — Community, questions, feature requests
            </p>
          </div>

          <h2 className="text-xl font-bold text-white/90 pt-4">The roadmap</h2>

          <p>
            Phase one (now): collect data from Fitbit and Renpho, display it in a unified dashboard
            with trends, recovery scores, and body composition tracking.
          </p>
          <p>
            Phase two: connect your health data to AI. Feed 30 days of sleep, HRV, activity, and
            weight data to Claude or GPT and get back specific analysis — not generic advice.
          </p>
          <p>
            Phase three: have the AI built directly into the platform. No copy-pasting, no switching tools.
            Open your dashboard and the coach is already looking at your data.
          </p>
        </div>

        <div className="mt-12 pt-6 border-t border-white/[.06] flex gap-6 text-[13px] text-white/30">
          <Link to="/" className="hover:text-white/60 transition-colors">Home</Link>
          <Link to="/terms" className="hover:text-white/60 transition-colors">Terms</Link>
          <Link to="/privacy" className="hover:text-white/60 transition-colors">Privacy</Link>
        </div>
      </div>
    </div>
  )
}

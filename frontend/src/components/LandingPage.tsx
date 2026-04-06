import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  DevicePhoneMobileIcon,
  ScaleIcon,
  MoonIcon,
  BoltIcon,
  HeartIcon,
  ChartBarSquareIcon,
  CodeBracketIcon,
  ServerIcon,
  LinkIcon,
  ArrowRightIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

/* ─── data ───────────────────────────────────────────────────────────────── */

const GITHUB_URL = 'https://github.com/hemati/tonnd'

const features = [
  { icon: DevicePhoneMobileIcon, color: 'text-teal-400', bg: 'bg-teal-400/10', ring: 'ring-teal-400/20', title: 'Fitbit Sync', desc: 'Real-time sync of sleep stages, heart rate zones, activity, and 10+ daily metrics.' },
  { icon: ScaleIcon, color: 'text-rose-400', bg: 'bg-rose-400/10', ring: 'ring-rose-400/20', title: 'Renpho Smart Scale', desc: 'Weight, body fat, muscle mass, BMI, and full body composition from your scale.' },
  { icon: MoonIcon, color: 'text-violet-400', bg: 'bg-violet-400/10', ring: 'ring-violet-400/20', title: 'Sleep Analysis', desc: 'Deep, light, REM, and awake stages. Efficiency trends over weeks and months.' },
  { icon: BoltIcon, color: 'text-amber-400', bg: 'bg-amber-400/10', ring: 'ring-amber-400/20', title: 'Activity Tracking', desc: 'Steps, calories, distance, active zone minutes, and floors — all in one view.' },
  { icon: HeartIcon, color: 'text-rose-400', bg: 'bg-rose-400/10', ring: 'ring-rose-400/20', title: 'Heart Rate & HRV', desc: 'Resting heart rate, zones, and HRV trends for recovery and readiness monitoring.' },
  { icon: ChartBarSquareIcon, color: 'text-sky-400', bg: 'bg-sky-400/10', ring: 'ring-sky-400/20', title: 'VO\u2082 Max & SpO\u2082', desc: 'Cardiovascular fitness score and blood oxygen saturation tracked over time.' },
  { icon: CodeBracketIcon, color: 'text-emerald-400', bg: 'bg-emerald-400/10', ring: 'ring-emerald-400/20', title: 'Open Source', desc: 'MIT licensed. Read every line, contribute features, or fork it for yourself.' },
  { icon: ServerIcon, color: 'text-orange-400', bg: 'bg-orange-400/10', ring: 'ring-orange-400/20', title: 'Self-Hosted', desc: 'One command: docker compose up. Your health data stays on your own server.' },
]

const steps = [
  { n: '01', title: 'Create an account', desc: 'Sign up free with Google or email. No credit card, ever.', color: 'from-teal-500 to-cyan-500' },
  { n: '02', title: 'Connect your devices', desc: 'Link Fitbit, Renpho, or any supported source in seconds.', color: 'from-violet-500 to-purple-500' },
  { n: '03', title: 'See your dashboard', desc: 'All your health metrics unified. Trends, scores, insights.', color: 'from-rose-500 to-pink-500' },
]

const techStack = ['React', 'TypeScript', 'Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Tailwind CSS']

/* ─── mock dashboard card ────────────────────────────────────────────────── */

const mockBars = [38, 62, 45, 78, 56, 70, 82]
const mockDays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

function DashboardMock() {

  return (
    <div className="relative lp-float">
      {/* glow behind */}
      <div className="absolute -inset-4 rounded-3xl bg-gradient-to-br from-teal-500/20 via-violet-500/10 to-rose-500/20 blur-2xl lp-pulse" />

      <div className="relative rounded-2xl border border-white/[.08] bg-[#0c1322]/80 backdrop-blur-xl p-5 shadow-2xl lp-glow">
        {/* top bar */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-teal-400 lp-pulse" />
            <span className="text-[11px] font-medium tracking-wider uppercase text-white/50">Live Dashboard</span>
          </div>
          <span className="text-[10px] text-white/30 font-mono">tonnd.com</span>
        </div>

        {/* metric row */}
        <div className="grid grid-cols-4 gap-3 mb-5">
          {[
            { label: 'Weight', value: '70.7', unit: 'kg', color: 'text-rose-400' },
            { label: 'Steps', value: '8,432', unit: '', color: 'text-teal-400' },
            { label: 'Sleep', value: '7h 23m', unit: '', color: 'text-violet-400' },
            { label: 'Heart', value: '62', unit: 'bpm', color: 'text-rose-400' },
          ].map((m) => (
            <div key={m.label} className="rounded-lg bg-white/[.04] border border-white/[.06] p-2.5">
              <div className="text-[9px] uppercase tracking-wider text-white/40 mb-1">{m.label}</div>
              <div className={`text-sm font-semibold ${m.color}`}>
                {m.value}
                {m.unit && <span className="text-[10px] font-normal text-white/30 ml-0.5">{m.unit}</span>}
              </div>
            </div>
          ))}
        </div>

        {/* mini bar chart */}
        <div className="rounded-lg bg-white/[.03] border border-white/[.05] p-3">
          <div className="text-[9px] uppercase tracking-wider text-white/40 mb-3">Weekly Steps</div>
          <div className="flex items-end justify-between gap-1.5 h-16">
            {mockBars.map((h, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className="w-full rounded-sm bg-gradient-to-t from-teal-500 to-teal-300 lp-bar-grow"
                  style={{ '--h': `${h}%`, height: `${h}%`, animationDelay: `${i * 0.08}s` } as React.CSSProperties}
                />
                <span className="text-[8px] text-white/30">{mockDays[i]}</span>
              </div>
            ))}
          </div>
        </div>

        {/* heartbeat line */}
        <div className="mt-3 flex items-center gap-2">
          <HeartIcon className="w-3.5 h-3.5 text-rose-400 lp-heartbeat" />
          <div className="flex-1 h-px bg-gradient-to-r from-rose-400/40 via-rose-400/10 to-transparent" />
          <span className="text-[9px] text-white/30 font-mono">62 bpm</span>
        </div>
      </div>
    </div>
  )
}

/* ─── component ──────────────────────────────────────────────────────────── */

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#060a13] text-white overflow-x-hidden" style={{ scrollBehavior: 'smooth' }}>

      {/* ═══ ambient background blobs ═══ */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-teal-500/[.07] blur-[120px] lp-pulse" />
        <div className="absolute top-1/3 right-0 w-[500px] h-[500px] rounded-full bg-violet-500/[.06] blur-[100px] lp-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-rose-500/[.05] blur-[100px] lp-pulse" style={{ animationDelay: '4s' }} />
      </div>

      {/* ═══ NAV ═══ */}
      <nav className="sticky top-0 z-50 border-b border-white/[.06] bg-[#060a13]/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
          {/* logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center shadow-lg shadow-teal-500/20 group-hover:shadow-teal-500/40 transition-shadow">
              <svg viewBox="0 0 24 24" className="w-4.5 h-4.5 text-white" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <span className="text-lg font-bold tracking-tight">TONND</span>
          </Link>

          {/* desktop links */}
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-white/50 hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm text-white/50 hover:text-white transition-colors">How it Works</a>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="text-sm text-white/50 hover:text-white transition-colors">GitHub</a>
            <Link to="/login" className="text-sm text-white/60 hover:text-white transition-colors">Sign In</Link>
            <Link to="/login" className="text-sm font-medium px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 transition-all shadow-lg shadow-teal-500/20 hover:shadow-teal-500/30">
              Get Started Free
            </Link>
          </div>

          {/* mobile toggle */}
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-2 text-white/60 hover:text-white">
            {menuOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
          </button>
        </div>

        {/* mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-white/[.06] bg-[#060a13]/95 backdrop-blur-xl px-5 py-4 space-y-3">
            <a href="#features" onClick={() => setMenuOpen(false)} className="block text-sm text-white/60 hover:text-white">Features</a>
            <a href="#how-it-works" onClick={() => setMenuOpen(false)} className="block text-sm text-white/60 hover:text-white">How it Works</a>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="block text-sm text-white/60 hover:text-white">GitHub</a>
            <Link to="/login" onClick={() => setMenuOpen(false)} className="block text-sm text-white/60 hover:text-white">Sign In</Link>
            <Link to="/login" onClick={() => setMenuOpen(false)} className="block text-center text-sm font-medium px-4 py-2.5 rounded-lg bg-gradient-to-r from-teal-500 to-cyan-500">
              Get Started Free
            </Link>
          </div>
        )}
      </nav>

      {/* ═══ HERO ═══ */}
      <section className="max-w-6xl mx-auto px-5 pt-20 pb-24 lg:pt-28 lg:pb-32">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* copy */}
          <div className="lp-appear">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-teal-400/20 bg-teal-400/5 text-teal-400 text-xs font-medium tracking-wide mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 lp-pulse" />
              Open Source & Free Forever
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-extrabold leading-[1.1] tracking-tight mb-6">
              All your health data.{' '}
              <span className="bg-gradient-to-r from-teal-400 via-cyan-300 to-teal-400 bg-clip-text text-transparent">
                One place.
              </span>
            </h1>

            <p className="text-lg text-white/50 leading-relaxed mb-8 max-w-lg">
              Connect Fitbit, Renpho, and more. See weight, sleep, heart rate, HRV, VO&#x2082; Max, and body composition in a single unified dashboard — self-hosted on your own server.
            </p>

            <div className="flex flex-wrap gap-3 mb-6">
              <Link to="/login" className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-medium bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 transition-all shadow-xl shadow-teal-500/20 hover:shadow-teal-500/30 hover:-translate-y-0.5">
                Get Started Free
                <ArrowRightIcon className="w-4 h-4" />
              </Link>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-medium border border-white/10 hover:border-white/20 text-white/70 hover:text-white transition-all hover:-translate-y-0.5">
                <CodeBracketIcon className="w-4 h-4" />
                View on GitHub
              </a>
            </div>

            <p className="text-xs text-white/30">No credit card required. Self-host with Docker.</p>
          </div>

          {/* mock dashboard */}
          <div className="lp-appear lp-appear-d2 hidden lg:block">
            <DashboardMock />
          </div>
        </div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section id="features" className="max-w-6xl mx-auto px-5 py-24">
        <div className="text-center mb-16 lp-appear">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Everything you need to{' '}
            <span className="bg-gradient-to-r from-violet-400 to-rose-400 bg-clip-text text-transparent">track your health</span>
          </h2>
          <p className="text-white/40 max-w-xl mx-auto">Eight integrations and metrics, one beautiful dashboard. More devices and data sources coming soon.</p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map((f, i) => (
            <div
              key={f.title}
              className={`group relative rounded-xl border border-white/[.06] bg-white/[.02] hover:bg-white/[.04] p-5 transition-all duration-300 hover:-translate-y-1 lp-appear`}
              style={{ animationDelay: `${0.05 * i}s` }}
            >
              <div className={`w-10 h-10 rounded-lg ${f.bg} ring-1 ${f.ring} flex items-center justify-center mb-4 transition-transform group-hover:scale-110`}>
                <f.icon className={`w-5 h-5 ${f.color}`} />
              </div>
              <h3 className="font-semibold text-sm mb-1.5">{f.title}</h3>
              <p className="text-xs text-white/40 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section id="how-it-works" className="max-w-4xl mx-auto px-5 py-24">
        <div className="text-center mb-16 lp-appear">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Up and running in{' '}
            <span className="bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">three steps</span>
          </h2>
          <p className="text-white/40">From zero to health dashboard in under two minutes.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {steps.map((s, i) => (
            <div key={s.n} className="relative lp-appear" style={{ animationDelay: `${0.15 * i}s` }}>
              {/* connector line */}
              {i < steps.length - 1 && (
                <div className="hidden md:block absolute top-10 left-full w-6 border-t border-dashed border-white/10 z-10" />
              )}

              <div className="rounded-xl border border-white/[.06] bg-white/[.02] p-6 text-center hover:bg-white/[.04] transition-colors">
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br ${s.color} text-white font-bold text-lg mb-4 shadow-lg`}>
                  {s.n}
                </div>
                <h3 className="font-semibold mb-2">{s.title}</h3>
                <p className="text-sm text-white/40">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-10 lp-appear lp-appear-d3">
          <Link to="/login" className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-medium bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 transition-all shadow-xl shadow-teal-500/20 hover:shadow-teal-500/30 hover:-translate-y-0.5">
            Get Started Free
            <ArrowRightIcon className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ═══ TRUST / SOCIAL PROOF ═══ */}
      <section className="max-w-5xl mx-auto px-5 py-24">
        <div className="rounded-2xl border border-white/[.06] bg-white/[.02] p-8 md:p-12">
          <div className="text-center mb-10 lp-appear">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-3">Built with modern, trusted technology</h2>
            <p className="text-sm text-white/40">Fully open source. Inspect every line. Contribute or fork.</p>
          </div>

          {/* tech pills */}
          <div className="flex flex-wrap justify-center gap-2.5 mb-10 lp-appear lp-appear-d1">
            {techStack.map((t) => (
              <span key={t} className="px-4 py-2 rounded-full border border-white/[.08] bg-white/[.03] text-sm text-white/60 font-medium hover:border-white/15 hover:text-white/80 transition-colors">
                {t}
              </span>
            ))}
          </div>

          {/* trust row */}
          <div className="flex flex-wrap justify-center gap-8 text-white/30 text-xs lp-appear lp-appear-d2">
            <div className="flex items-center gap-1.5">
              <CodeBracketIcon className="w-4 h-4" />
              <span>MIT License</span>
            </div>
            <div className="flex items-center gap-1.5">
              <ServerIcon className="w-4 h-4" />
              <span>Self-Hostable</span>
            </div>
            <div className="flex items-center gap-1.5">
              <LinkIcon className="w-4 h-4" />
              <span>No Vendor Lock-in</span>
            </div>
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              <span>Your Data, Your Server</span>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ FINAL CTA ═══ */}
      <section className="max-w-4xl mx-auto px-5 py-24">
        <div className="relative rounded-2xl overflow-hidden lp-appear">
          {/* gradient bg */}
          <div className="absolute inset-0 bg-gradient-to-br from-teal-500/15 via-violet-500/10 to-rose-500/15" />
          <div className="absolute inset-0 bg-[#060a13]/60" />

          <div className="relative text-center py-16 px-8">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              Take control of your health data
            </h2>
            <p className="text-white/50 max-w-md mx-auto mb-8">
              Join the open-source health tracking movement. Free forever, no strings attached.
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              <Link to="/login" className="inline-flex items-center gap-2 px-7 py-3.5 rounded-lg font-medium bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 transition-all shadow-xl shadow-teal-500/20 hover:shadow-teal-500/30 hover:-translate-y-0.5">
                Get Started Free
                <ArrowRightIcon className="w-4 h-4" />
              </Link>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-7 py-3.5 rounded-lg font-medium border border-white/10 hover:border-white/20 text-white/70 hover:text-white transition-all hover:-translate-y-0.5">
                <CodeBracketIcon className="w-4 h-4" />
                View on GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-white/[.06] bg-[#060a13]">
        <div className="max-w-6xl mx-auto px-5 py-12">
          <div className="grid sm:grid-cols-3 gap-8 mb-10">
            {/* brand */}
            <div>
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-7 h-7 rounded-md bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                </div>
                <span className="font-bold tracking-tight">TONND</span>
              </div>
              <p className="text-xs text-white/30 leading-relaxed">
                Open-source fitness tracking.<br />
                Your data, your server.
              </p>
            </div>

            {/* product */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-3">Product</h4>
              <div className="space-y-2">
                <Link to="/login" className="block text-sm text-white/40 hover:text-white transition-colors">Sign In</Link>
                <a href="#features" className="block text-sm text-white/40 hover:text-white transition-colors">Features</a>
                <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="block text-sm text-white/40 hover:text-white transition-colors">GitHub</a>
              </div>
            </div>

            {/* legal */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-3">Legal</h4>
              <div className="space-y-2">
                <Link to="/terms" className="block text-sm text-white/40 hover:text-white transition-colors">Terms of Service</Link>
                <Link to="/privacy" className="block text-sm text-white/40 hover:text-white transition-colors">Privacy Policy</Link>
                <Link to="/cookies" className="block text-sm text-white/40 hover:text-white transition-colors">Cookie Policy</Link>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-white/[.06] flex flex-wrap justify-between items-center gap-4">
            <p className="text-xs text-white/20">&copy; {new Date().getFullYear()} TONND. All rights reserved.</p>
            <div className="flex gap-4 text-xs text-white/20">
              <Link to="/privacy#gdpr" className="hover:text-white/40 transition-colors">GDPR Rights</Link>
              <Link to="/privacy#ccpa" className="hover:text-white/40 transition-colors">Do Not Sell My Info</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

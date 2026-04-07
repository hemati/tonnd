import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bars3Icon, XMarkIcon, ArrowRightIcon, MoonIcon, BoltIcon, HeartIcon, ChartBarSquareIcon } from '@heroicons/react/24/outline'
import { GITHUB_URL, DISCORD_URL } from '../config/theme'
import { getAllPosts } from '../lib/blog'
import SEO from './SEO'
import Logo from './Logo'
import Footer from './Footer'

/* ─── mock dashboard ─────────────────────────────────────────────────────── */

const mockBars = [38, 62, 45, 78, 56, 70, 82]
const mockDays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

function DashboardMock() {
  return (
    <div className="rounded-xl border border-white/[.08] bg-white/[.02] p-5 shadow-2xl">
      {/* top bar */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-[11px] font-medium tracking-wider uppercase text-white/40">Health Dashboard</span>
        </div>
        <span className="text-[10px] text-white/25 font-mono">tonnd.com</span>
      </div>

      {/* metrics */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        {[
          { label: 'Weight', value: '70.7', unit: 'kg' },
          { label: 'Steps', value: '8,432', unit: '' },
          { label: 'Sleep', value: '7h 23m', unit: '' },
          { label: 'Heart', value: '62', unit: 'bpm' },
        ].map((m) => (
          <div key={m.label} className="rounded-lg bg-white/[.03] border border-white/[.06] p-2.5">
            <div className="text-[9px] uppercase tracking-wider text-white/30 mb-1">{m.label}</div>
            <div className="text-sm font-semibold text-white/80">
              {m.value}
              {m.unit && <span className="text-[10px] font-normal text-white/30 ml-0.5">{m.unit}</span>}
            </div>
          </div>
        ))}
      </div>

      {/* bar chart */}
      <div className="rounded-lg bg-white/[.02] border border-white/[.05] p-3">
        <div className="text-[9px] uppercase tracking-wider text-white/30 mb-3">Weekly Steps</div>
        <div className="flex items-end justify-between gap-1.5" style={{ height: 64 }}>
          {mockBars.map((h, i) => (
            <div key={i} className="flex-1 flex flex-col items-center justify-end gap-1" style={{ height: '100%' }}>
              <div className="rounded-sm bg-white/30" style={{ height: `${(h / 100) * 52}px`, width: 32 }} />
              <span className="text-[8px] text-white/25 self-center">{mockDays[i]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ─── component ──────────────────────────────────────────────────────────── */

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <SEO path="/" />

      {/* ═══ NAV ═══ */}
      <nav className="sticky top-0 z-50 border-b border-white/[.06] bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-5 h-14 flex items-center justify-between">
          <Logo />

          <div className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-[13px] text-white/40 hover:text-white/80 transition-colors">Features</a>
            <a href="#how-it-works" className="text-[13px] text-white/40 hover:text-white/80 transition-colors">How it Works</a>
            <Link to="/blog" className="text-[13px] text-white/40 hover:text-white/80 transition-colors">Blog</Link>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="text-[13px] text-white/40 hover:text-white/80 transition-colors">GitHub</a>
            <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer" className="text-[13px] text-white/40 hover:text-white/80 transition-colors">Discord</a>
            <Link to="/login" className="text-[13px] text-white/40 hover:text-white/80 transition-colors">Sign In</Link>
            <Link to="/login" className="text-[13px] font-medium px-3.5 py-1.5 rounded-md bg-white text-black hover:bg-white/90 transition-colors">
              Get Started
            </Link>
          </div>

          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-1.5 text-white/50 hover:text-white">
            {menuOpen ? <XMarkIcon className="w-5 h-5" /> : <Bars3Icon className="w-5 h-5" />}
          </button>
        </div>

        {menuOpen && (
          <div className="md:hidden border-t border-white/[.06] bg-[#0a0a0a]/95 backdrop-blur-xl px-5 py-4 space-y-3">
            <a href="#features" onClick={() => setMenuOpen(false)} className="block text-sm text-white/50">Features</a>
            <a href="#how-it-works" onClick={() => setMenuOpen(false)} className="block text-sm text-white/50">How it Works</a>
            <Link to="/blog" onClick={() => setMenuOpen(false)} className="block text-sm text-white/50">Blog</Link>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="block text-sm text-white/50">GitHub</a>
            <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer" className="block text-sm text-white/50">Discord</a>
            <Link to="/login" onClick={() => setMenuOpen(false)} className="block text-sm text-white/50">Sign In</Link>
            <Link to="/login" onClick={() => setMenuOpen(false)} className="block text-center text-sm font-medium px-4 py-2 rounded-md bg-white text-black">
              Get Started
            </Link>
          </div>
        )}
      </nav>

      {/* ═══ HERO ═══ */}
      <section className="max-w-5xl mx-auto px-5 pt-20 pb-16 lg:pt-28 lg:pb-24">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="lp-appear">
            <p className="text-[13px] text-white/30 font-medium tracking-wide mb-5">
              Open source &middot; Self-hosted &middot; Free
            </p>

            <h1 className="text-[2.75rem] sm:text-5xl lg:text-[3.5rem] font-bold leading-[1.08] tracking-tight mb-6 text-white">
              The open-source dashboard for your health data.
            </h1>

            <p className="text-[17px] text-white/45 leading-relaxed mb-10 max-w-md">
              A self-hosted fitness tracker that connects Fitbit and Renpho. Sleep tracking, weight tracking, heart rate, HRV, and body composition &mdash; all in one place, on your own server.
            </p>

            <div className="flex flex-wrap items-center gap-3 mb-4">
              <Link to="/login" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium bg-white text-black hover:bg-white/90 transition-colors">
                Get Started Free
                <ArrowRightIcon className="w-3.5 h-3.5" />
              </Link>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium border border-white/[.12] text-white/60 hover:text-white hover:border-white/25 transition-colors">
                View on GitHub
              </a>
            </div>

            <p className="text-[13px] text-white/25">
              No credit card. <code className="text-white/35">docker compose up</code>
            </p>
          </div>

          <div className="lp-appear lp-appear-d2 hidden lg:block">
            <DashboardMock />
          </div>
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ FEATURES ═══ */}
      <section id="features" className="max-w-5xl mx-auto px-5 py-20">

        {/* Connect */}
        <div className="mb-20">
          <p className="text-[13px] text-white/25 font-medium tracking-wide mb-3 lp-appear">Connect</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Bring your devices together.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg lp-appear">
            Link your Fitbit account and Renpho smart scale. Data flows automatically into your dashboard.
          </p>
          <div className="grid sm:grid-cols-2 gap-px bg-white/[.06] rounded-lg overflow-hidden lp-appear">
            <div className="bg-[#0a0a0a] p-6">
              <div className="flex items-start gap-4">
                <svg className="w-8 h-8 flex-shrink-0 text-white/50" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="23.9" cy="24" r="2.56"/><circle cx="23.9" cy="16" r="2.56"/><circle cx="23.9" cy="8.06" r="2.56"/>
                  <circle cx="23.9" cy="31.97" r="2.56"/><circle cx="23.9" cy="39.94" r="2.56"/>
                  <circle cx="15.93" cy="24" r="2.13"/><circle cx="15.93" cy="16" r="2.13"/><circle cx="15.93" cy="31.97" r="2.13"/>
                  <circle cx="31.87" cy="24" r="2.99"/><circle cx="31.87" cy="16" r="2.99"/><circle cx="31.87" cy="31.97" r="2.99"/>
                  <circle cx="7.96" cy="24" r="1.71"/><circle cx="39.83" cy="24" r="3.42"/>
                </svg>
                <div>
                  <h3 className="text-sm font-semibold text-white/80 mb-2">Fitbit</h3>
                  <p className="text-sm text-white/40 leading-relaxed">Sleep stages, heart rate zones, activity, HRV, SpO&#x2082;, VO&#x2082; Max, and 10+ metrics via OAuth.</p>
                </div>
              </div>
            </div>
            <div className="bg-[#0a0a0a] p-6">
              <div className="flex items-start gap-4">
                <svg className="w-8 h-8 flex-shrink-0 text-white/50" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m5.83 42.5 18.17-17.69a12.45 12.45 0 0 0 9.94-3.36 10.59 10.59 0 0 0 3.19-9.42"/>
                  <ellipse cx="23.74" cy="11.52" rx="6.18" ry="6.02"/>
                  <path d="m42.17 42.49-10.37-10.1c-7.8 3.08-15.22-.35-15.22-.35"/>
                </svg>
                <div>
                  <h3 className="text-sm font-semibold text-white/80 mb-2">Renpho Smart Scale</h3>
                  <p className="text-sm text-white/40 leading-relaxed">Weight, body fat, muscle mass, BMI, visceral fat, and full body composition.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Track */}
        <div className="mb-20">
          <p className="text-[13px] text-white/25 font-medium tracking-wide mb-3 lp-appear">Track</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Every metric that matters.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg lp-appear">
            All your health data in a single view. Trends over days, weeks, and months.
          </p>
          <div className="grid sm:grid-cols-2 gap-px bg-white/[.06] rounded-lg overflow-hidden lp-appear">
            {[
              { icon: MoonIcon, title: 'Sleep', desc: 'Deep, light, REM, awake. Nightly efficiency and trends over weeks.' },
              { icon: BoltIcon, title: 'Activity', desc: 'Steps, calories, distance, active zone minutes, and floors.' },
              { icon: HeartIcon, title: 'Heart Rate & HRV', desc: 'Resting HR, zones, and heart rate variability for recovery monitoring.' },
              { icon: ChartBarSquareIcon, title: 'VO\u2082 Max & SpO\u2082', desc: 'Cardio fitness score and blood oxygen saturation tracked over time.' },
            ].map((f) => (
              <div key={f.title} className="bg-[#0a0a0a] p-6">
                <div className="flex items-start gap-4">
                  <f.icon className="w-6 h-6 flex-shrink-0 text-white/40" />
                  <div>
                    <h3 className="text-sm font-semibold text-white/80 mb-2">{f.title}</h3>
                    <p className="text-sm text-white/40 leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Own */}
        <div>
          <p className="text-[13px] text-white/25 font-medium tracking-wide mb-3 lp-appear">Own</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Your data, your rules.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg lp-appear">
            TONND is fully open source and self-hosted. No cloud dependency, no vendor lock-in.
          </p>
          <div className="grid sm:grid-cols-3 gap-px bg-white/[.06] rounded-lg overflow-hidden lp-appear">
            {[
              { title: 'Open Source', desc: 'AGPL-3.0 licensed. Read every line, contribute, or fork.' },
              { title: 'Self-Hosted', desc: 'docker compose up. Your health data on your own server.' },
              { title: 'No Lock-in', desc: 'Standard PostgreSQL. Export anytime. No cloud dependency.' },
            ].map((f) => (
              <div key={f.title} className="bg-[#0a0a0a] p-6">
                <h3 className="text-sm font-semibold text-white/80 mb-2">{f.title}</h3>
                <p className="text-sm text-white/40 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ HOW IT WORKS ═══ */}
      <section id="how-it-works" className="max-w-5xl mx-auto px-5 py-20">
        <p className="text-[13px] text-white/25 font-medium tracking-wide mb-3 lp-appear">How it works</p>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-12 lp-appear">Up and running in three steps.</h2>

        <div className="grid md:grid-cols-3 gap-12 lp-appear">
          {[
            { n: '1', title: 'Create an account', desc: 'Sign up with Google or email. No credit card, ever.' },
            { n: '2', title: 'Connect your devices', desc: 'Link Fitbit, Renpho, or any supported source in seconds.' },
            { n: '3', title: 'See your dashboard', desc: 'All metrics unified. Trends, recovery scores, insights.' },
          ].map((s) => (
            <div key={s.n}>
              <div className="text-[13px] font-mono text-white/20 mb-3">{s.n}.</div>
              <h3 className="text-base font-semibold text-white/80 mb-2">{s.title}</h3>
              <p className="text-sm text-white/40 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ WHY SELF-HOST ═══ */}
      <section className="max-w-5xl mx-auto px-5 py-20">
        <p className="text-[13px] text-white/25 font-medium tracking-wide mb-3 lp-appear">Why self-host</p>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Your health data is personal.</h2>
        <p className="text-[15px] text-white/40 mb-12 max-w-lg lp-appear">
          Health monitoring belongs on your own server. TONND gives you full control over where your data lives and who can access it.
        </p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-12 lp-appear">
          {[
            { title: 'Your server', desc: 'Runs on any machine with Docker. No cloud required.' },
            { title: 'Your database', desc: 'Standard PostgreSQL. Query, export, or back up anytime.' },
            { title: 'Your code', desc: 'AGPL-3.0 licensed. Inspect, audit, or modify freely.' },
            { title: 'Your privacy', desc: 'No tracking, no ads, no third-party data sharing.' },
          ].map((item) => (
            <div key={item.title}>
              <h3 className="text-sm font-semibold text-white/80 mb-2">{item.title}</h3>
              <p className="text-sm text-white/40 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ FINAL CTA ═══ */}
      <section className="max-w-5xl mx-auto px-5 py-24 text-center lp-appear">
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
          Built for the future.<br />Available today.
        </h2>
        <p className="text-[15px] text-white/40 max-w-md mx-auto mb-10">
          Self-host your fitness dashboard. Open source, free forever.
        </p>
        <div className="flex flex-wrap justify-center items-center gap-3">
          <Link to="/login" className="inline-flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium bg-white text-black hover:bg-white/90 transition-colors">
            Get Started Free
            <ArrowRightIcon className="w-3.5 h-3.5" />
          </Link>
          <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium border border-white/[.12] text-white/60 hover:text-white hover:border-white/25 transition-colors">
            View on GitHub
          </a>
        </div>
      </section>

      {/* ═══ BLOG ═══ */}
      {(() => {
        const posts = getAllPosts().slice(0, 3)
        if (posts.length === 0) return null
        return (
          <>
            <div className="border-t border-white/[.06]" />
            <section className="max-w-5xl mx-auto px-5 py-20">
              <div className="flex items-baseline justify-between mb-8">
                <div>
                  <p className="text-[13px] text-white/25 font-medium tracking-wide mb-3">From the blog</p>
                  <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90">Latest posts</h2>
                </div>
                <Link to="/blog" className="text-[13px] text-white/40 hover:text-white/70 transition-colors">View all &rarr;</Link>
              </div>
              <div className="grid md:grid-cols-3 gap-6">
                {posts.map((post) => (
                  <Link key={post.slug} to={`/blog/${post.slug}`} className="block rounded-lg border border-white/[.06] bg-white/[.02] p-5 hover:bg-white/[.04] transition-colors">
                    <time className="text-[12px] text-white/25">{post.date}</time>
                    <h3 className="text-sm font-semibold text-white/80 mt-2 mb-2 line-clamp-2">{post.title}</h3>
                    <p className="text-[13px] text-white/35 line-clamp-2">{post.description}</p>
                  </Link>
                ))}
              </div>
            </section>
          </>
        )
      })()}

      <Footer />
    </div>
  )
}

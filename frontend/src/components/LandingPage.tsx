import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { Bars3Icon, XMarkIcon, ArrowRightIcon, MoonIcon, BoltIcon, HeartIcon, ChartBarSquareIcon, ScaleIcon, FireIcon, BeakerIcon } from '@heroicons/react/24/outline'
import { GITHUB_URL, DISCORD_URL } from '../config/theme'
import Body from '@mjcdev/react-body-highlighter'
import { FitbitIcon, RenphoIcon, HevyIcon } from './SourceIcons'
import { getAllPosts } from '../lib/blog'
import SEO from './SEO'
import Logo from './Logo'
import Footer from './Footer'

/* ─── mock dashboard ─────────────────────────────────────────────────────── */

const mockBars = [38, 62, 45, 78, 56, 70, 82]
const mockDays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

function DashboardMock() {
  return (
    <div className="rounded-xl border border-white/[.08] bg-white/[.02] p-4 shadow-2xl">
      {/* top bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#22d3ee' }} />
          <span className="text-[11px] font-medium tracking-wider uppercase text-white/40">Health Dashboard</span>
        </div>
        <span className="text-[10px] text-white/25 font-mono">tonnd.com</span>
      </div>

      {/* metrics row 1 */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        {[
          { label: 'Weight', value: '76.3', unit: 'kg' },
          { label: 'Steps', value: '8,432', unit: '' },
          { label: 'Sleep', value: '7h 23m', unit: '' },
          { label: 'Heart', value: '62', unit: 'bpm' },
        ].map((m) => (
          <div key={m.label} className="rounded-lg bg-white/[.03] border border-white/[.06] p-2">
            <div className="text-[8px] uppercase tracking-wider text-white/30 mb-0.5">{m.label}</div>
            <div className="text-[13px] font-semibold text-white/80">
              {m.value}
              {m.unit && <span className="text-[9px] font-normal text-white/30 ml-0.5">{m.unit}</span>}
            </div>
          </div>
        ))}
      </div>

      {/* row 2+3: left 61.8% (body comp, volume, steps) | right 38.2% (workout) — golden ratio */}
      <div className="flex gap-2">
        <div style={{ flex: '0 0 61.8%' }} className="space-y-2">
          {/* Body Composition */}
          <div className="rounded-lg bg-white/[.02] border border-white/[.05] p-2.5">
            <div className="text-[8px] uppercase tracking-wider text-white/30 mb-2">Body Comp</div>
            <div className="space-y-1.5">
              {[
                { label: 'Body Fat', value: '18.2%' },
                { label: 'Muscle', value: '35.1 kg' },
                { label: 'BMI', value: '23.4' },
              ].map((r) => (
                <div key={r.label} className="flex justify-between">
                  <span className="text-[9px] text-white/30">{r.label}</span>
                  <span className="text-[10px] font-medium text-white/60">{r.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Volume Trend */}
          <div className="rounded-lg bg-white/[.02] border border-white/[.05] p-2.5">
            <div className="text-[8px] uppercase tracking-wider text-white/30 mb-2">Volume</div>
            <div className="flex items-end justify-between gap-1" style={{ height: 36 }}>
              {[3200, 4100, 0, 4500, 0, 3800, 4200].map((v, i) => (
                <div key={i} className="flex-1 flex flex-col items-center justify-end gap-0.5" style={{ height: '100%' }}>
                  <div
                    className="w-full rounded-sm"
                    style={{
                      height: v ? `${(v / 5000) * 30}px` : '0px',
                      backgroundColor: v ? 'rgba(34,211,238,0.5)' : 'transparent',
                    }}
                  />
                  <span className="text-[7px] text-white/20">{mockDays[i]}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Steps */}
          <div className="rounded-lg bg-white/[.02] border border-white/[.05] p-2.5">
            <div className="text-[8px] uppercase tracking-wider text-white/30 mb-2">Weekly Steps</div>
            <div className="flex items-end justify-between gap-1" style={{ height: 36 }}>
              {mockBars.map((h, i) => (
                <div key={i} className="flex-1 flex flex-col items-center justify-end gap-0.5" style={{ height: '100%' }}>
                  <div className="w-full rounded-sm bg-white/25" style={{ height: `${(h / 100) * 28}px` }} />
                  <span className="text-[7px] text-white/20">{mockDays[i]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Workout body — right side, full height */}
        <div className="rounded-lg bg-white/[.02] border border-white/[.05] p-2.5 flex-1 flex flex-col">
          <div className="text-[8px] uppercase tracking-wider text-white/30 mb-1">Workout</div>
          <div className="flex-1 flex items-center justify-center">
            <div style={{ width: '100%', maxWidth: 130, marginRight: 0 }}>
              <Body
                data={[
                  { slug: 'chest', intensity: 3 },
                  { slug: 'upper-back', intensity: 3 },
                  { slug: 'quadriceps', intensity: 2 },
                  { slug: 'deltoids', intensity: 2 },
                  { slug: 'abs', intensity: 2 },
                  { slug: 'biceps', intensity: 1 },
                  { slug: 'gluteal', intensity: 2 },
                  { slug: 'hamstring', intensity: 1 },
                  { slug: 'trapezius', intensity: 1 },
                ]}
                side="front"
                gender="male"
                scale={0.6}
                colors={['#0c4a5e', '#0e7490', '#22d3ee']}
                border="#1e293b"
              />
            </div>
          </div>
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
      <Helmet>
        <script type="application/ld+json">{JSON.stringify({
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'WebPage',
              '@id': 'https://tonnd.com/',
              'name': 'TONND — Your health data in one dashboard',
              'description': 'Open-source health dashboard. Connect Fitbit, Renpho, and Hevy to track sleep, weight, workouts, heart rate, HRV, and 15+ metrics in one place.',
              'url': 'https://tonnd.com/',
              'isPartOf': { '@id': 'https://tonnd.com/#website' },
              'about': { '@id': 'https://tonnd.com/#software' }
            },
            {
              '@type': 'SoftwareApplication',
              '@id': 'https://tonnd.com/#software',
              'name': 'TONND',
              'url': 'https://tonnd.com/',
              'applicationCategory': 'HealthApplication',
              'operatingSystem': 'Web',
              'description': 'Open-source health dashboard. Connect Fitbit, Renpho, and Hevy to track sleep, weight, workouts, heart rate, HRV, and 15+ metrics.',
              'screenshot': 'https://tonnd.com/og-image.png',
              'license': 'https://github.com/hemati/tonnd/blob/main/LICENSE',
              'offers': {
                '@type': 'Offer',
                'price': '0',
                'priceCurrency': 'USD',
                'availability': 'https://schema.org/InStock'
              },
              'author': { '@id': 'https://tonnd.com/#organization' }
            }
          ]
        })}</script>
      </Helmet>

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

          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-1.5 text-white/50 hover:text-white" aria-label={menuOpen ? 'Close menu' : 'Open menu'}>
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
            <p className="text-[13px] text-white/45 font-medium tracking-wide mb-5">
              Open source &middot; All your metrics in one place
            </p>

            <h1 className="text-[2.75rem] sm:text-5xl lg:text-[3.5rem] font-bold leading-[1.08] tracking-tight mb-6 text-white">
              The open-source dashboard for your health data.
            </h1>

            <p className="text-[17px] text-white/65 leading-relaxed mb-10 max-w-md">
              Connect Fitbit, Renpho, and Hevy. Track sleep, weight, workouts, heart rate, HRV, body composition, and 15+ metrics &mdash; all in one place. Use it on tonnd.com or self-host on your own server.
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

            <p className="text-[13px] text-white/40">
              No credit card required.
            </p>
          </div>

          <div className="lp-appear lp-appear-d2 hidden lg:block">
            <DashboardMock />
          </div>
        </div>
      </section>

      {/* ═══ WHAT IS TONND ═══ */}
      <section className="max-w-5xl mx-auto px-5 py-16">
        <div className="lp-appear">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4">What is TONND?</h2>
          <p className="text-[15px] text-white/55 leading-relaxed mb-4">
            TONND is a free, open-source health dashboard that pulls data from Fitbit wearables, Renpho smart scales, and Hevy workout logs into a single interface. It tracks over 15 metrics including sleep stages, heart rate variability (HRV), VO&#x2082; Max, SpO&#x2082;, weight, body fat percentage, muscle mass, workout volume, and recovery scores. Users can view trends over 7, 14, or 30 days and see which muscle groups they trained as an interactive heatmap.
          </p>
          <p className="text-[15px] text-white/55 leading-relaxed">
            The project was started in 2024 after Google shut down the Fitbit web dashboard, leaving millions of users without a way to view their health data on a full screen. TONND runs on Docker and can be self-hosted on any server, or used as a managed service at tonnd.com. It is licensed under AGPL-3.0 and built with FastAPI, PostgreSQL, and React.
          </p>
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ FEATURES ═══ */}
      <section id="features" className="max-w-5xl mx-auto px-5 py-20">

        {/* Connect */}
        <div className="mb-20">
          <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3 lp-appear">Connect</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Bring your devices together.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg lp-appear">
            Link Fitbit, Renpho, and Hevy. Data flows automatically into your dashboard.
          </p>
          <div className="grid sm:grid-cols-3 gap-px bg-white/[.06] rounded-lg overflow-hidden lp-appear">
            <div className="bg-[#0a0a0a] p-6">
              <div className="flex items-start gap-4">
                <FitbitIcon className="w-8 h-8 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-white/80 mb-2">Fitbit</h3>
                  <p className="text-sm text-white/40 leading-relaxed">Sleep stages, heart rate zones, activity, HRV, SpO&#x2082;, VO&#x2082; Max, and 10+ metrics via OAuth.</p>
                </div>
              </div>
            </div>
            <div className="bg-[#0a0a0a] p-6">
              <div className="flex items-start gap-4">
                <RenphoIcon className="w-8 h-8 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-white/80 mb-2">Renpho Smart Scale</h3>
                  <p className="text-sm text-white/40 leading-relaxed">Weight, body fat, muscle mass, BMI, visceral fat, and full body composition.</p>
                </div>
              </div>
            </div>
            <div className="bg-[#0a0a0a] p-6">
              <div className="flex items-start gap-4">
                <HevyIcon className="w-8 h-8 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-white/80 mb-2">Hevy</h3>
                  <p className="text-sm text-white/40 leading-relaxed">Workout tracking — exercises, sets, reps, volume, and muscle group analysis.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Track */}
        <div className="mb-20">
          <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3 lp-appear">Track</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Every metric that matters.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg lp-appear">
            15+ health metrics in a single dashboard. Trends over days, weeks, and months.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-white/[.06] rounded-lg overflow-hidden lp-appear">
            {[
              { icon: MoonIcon, title: 'Sleep', desc: 'Stages, efficiency, and duration trends.' },
              { icon: BoltIcon, title: 'Activity', desc: 'Steps, calories, distance, active zone minutes.' },
              { icon: HeartIcon, title: 'Heart Rate & HRV', desc: 'Resting HR, zones, and recovery tracking.' },
              { icon: ScaleIcon, title: 'Weight & Body Comp', desc: 'Weight, body fat, muscle mass, BMI.' },
              { icon: FireIcon, title: 'Workouts', desc: 'Exercises, volume, muscle heatmap.' },
              { icon: ChartBarSquareIcon, title: 'Recovery Score', desc: 'Composite from HRV, sleep, and resting HR.' },
              { icon: BeakerIcon, title: 'VO\u2082 Max & SpO\u2082', desc: 'Cardio fitness and blood oxygen.' },
              { icon: BoltIcon, title: 'Breathing & Temp', desc: 'Breathing rate and skin temperature.' },
            ].map((f) => (
              <div key={f.title} className="bg-[#0a0a0a] p-5">
                <div className="flex items-start gap-3">
                  <f.icon className="w-5 h-5 flex-shrink-0 text-white/30 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-semibold text-white/80 mb-1">{f.title}</h3>
                    <p className="text-[13px] text-white/35 leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Own */}
        <div>
          <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3 lp-appear">Open source</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Your data, your rules.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg lp-appear">
            TONND is fully open source. Use our managed cloud or run it on your own server &mdash; you always own your data.
          </p>
          <div className="grid sm:grid-cols-3 gap-px bg-white/[.06] rounded-lg overflow-hidden lp-appear">
            {[
              { title: 'Open Source', desc: 'AGPL-3.0 licensed. Read every line, contribute, or fork.' },
              { title: 'Self-Host Option', desc: 'docker compose up. Run TONND on your own hardware if you prefer.' },
              { title: 'No Lock-in', desc: 'Standard PostgreSQL. Export your data anytime.' },
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
        <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3 lp-appear">How it works</p>
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

      {/* ═══ WHY TONND ═══ */}
      <section className="max-w-5xl mx-auto px-5 py-20">
        <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3 lp-appear">Why TONND</p>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4 lp-appear">Your health data is personal.</h2>
        <p className="text-[15px] text-white/40 mb-12 max-w-lg lp-appear">
          TONND gives you full control over your health data. Use our cloud or self-host &mdash; either way, your data stays yours.
        </p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-12 lp-appear">
          {[
            { title: 'Privacy first', desc: 'No tracking, no ads, no third-party data sharing. Ever.' },
            { title: 'Your data', desc: 'Standard PostgreSQL. Export or back up anytime.' },
            { title: 'Open code', desc: 'AGPL-3.0 licensed. Inspect, audit, or modify freely.' },
            { title: 'Self-host ready', desc: 'Want full control? Run TONND on any machine with Docker.' },
          ].map((item) => (
            <div key={item.title}>
              <h3 className="text-sm font-semibold text-white/80 mb-2">{item.title}</h3>
              <p className="text-sm text-white/40 leading-relaxed">{item.desc}</p>
            </div>
          ))}
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
                  <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3">From the blog</p>
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

      {/* ═══ FINAL CTA ═══ */}
      <div className="border-t border-white/[.06]" />
      <section className="max-w-5xl mx-auto px-5 py-24 text-center lp-appear">
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
          Built for the future.<br />Available today.
        </h2>
        <p className="text-[15px] text-white/40 max-w-md mx-auto mb-10">
          Start tracking what matters. Open source, no strings attached.
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

      <Footer />
    </div>
  )
}

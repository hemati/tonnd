import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { Bars3Icon, XMarkIcon, ArrowRightIcon, MoonIcon, BoltIcon, HeartIcon, ChartBarSquareIcon, ScaleIcon, FireIcon, BeakerIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'
import { GITHUB_URL, DISCORD_URL } from '../config/theme'
import Body from '@mjcdev/react-body-highlighter'
import { FitbitIcon, RenphoIcon, HevyIcon } from './SourceIcons'
import { getAllPosts } from '../lib/blog'
import SEO from './SEO'
import Logo from './Logo'
import Footer from './Footer'

const ACCENT = '#22d3ee'

/* ─── conversation mock (hero) ──────────────────────────────────────────── */

function ConversationMock() {
  return (
    <div className="rounded-xl border border-white/[.08] bg-white/[.02] p-4 shadow-2xl">
      {/* top bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ACCENT }} />
          <span className="text-[11px] font-medium tracking-wider uppercase text-white/40">Claude + TONND</span>
        </div>
        <span className="text-[10px] text-white/25 font-mono">claude.ai</span>
      </div>

      {/* user message */}
      <div className="mb-3">
        <div className="rounded-lg bg-white/[.05] border border-white/[.08] p-3">
          <p className="text-[13px] text-white/70 leading-relaxed">My HRV dropped from 48 to 28 over the last three days. What happened?</p>
        </div>
        <span className="text-[9px] text-white/20 mt-1 block">You</span>
      </div>

      {/* claude response */}
      <div className="mb-2">
        <div className="rounded-lg bg-white/[.02] border border-white/[.06] p-3">
          <p className="text-[12px] text-white/55 leading-relaxed mb-2">I checked your Fitbit vitals, Hevy workouts, and sleep data. Here's what I found:</p>
          <ul className="space-y-1.5 text-[11px] text-white/45 leading-relaxed">
            <li className="flex gap-2"><span className="text-white/25">&#8226;</span>You did deadlifts and squats on back-to-back days for the first time</li>
            <li className="flex gap-2"><span className="text-white/25">&#8226;</span>Sleep efficiency dropped 12 points the night after</li>
            <li className="flex gap-2"><span className="text-white/25">&#8226;</span>Resting heart rate is still 8 bpm above your baseline</li>
          </ul>
          <div className="flex gap-1.5 mt-3">
            <span className="text-[10px] px-2 py-0.5 rounded bg-white/[.08] text-white/50 border border-white/[.08]">Fitbit</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-white/[.08] text-white/50 border border-white/[.08]">Hevy</span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-white/[.08] text-white/50 border border-white/[.08]">Sleep</span>
          </div>
        </div>
        <span className="text-[9px] text-white/20 mt-1 block">Claude</span>
      </div>
    </div>
  )
}

/* ─── dashboard mock (features section) ─────────────────────────────────── */

const mockBars = [38, 62, 45, 78, 56, 70, 82]
const mockDays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

function DashboardMock() {
  return (
    <div className="rounded-xl border border-white/[.08] bg-white/[.02] p-4 shadow-2xl">
      {/* top bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: ACCENT }} />
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

      {/* row 2+3: left 61.8% | right 38.2% — golden ratio */}
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

        {/* Workout body — right side */}
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
                colors={['#0c4a5e', '#0e7490', ACCENT]}
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
              'name': 'TONND — Ask your health data anything',
              'description': 'Open-source health dashboard with AI. Connect Fitbit, Renpho, and Hevy. Track 15+ metrics. Ask Claude AI questions about your health data in plain language.',
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
              'description': 'Open-source health dashboard with AI. Connect Fitbit, Renpho, and Hevy. Track 15+ metrics. Ask Claude AI questions about your data in plain language.',
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
            <a href="#ai" className="text-[13px] text-white/40 hover:text-white/80 transition-colors">AI</a>
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
            <a href="#ai" onClick={() => setMenuOpen(false)} className="block text-sm text-white/50">AI</a>
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
          <div>
            <p className="text-[13px] text-white/45 font-medium tracking-wide mb-5">
              Fitbit &middot; Renpho &middot; Hevy &middot; Claude AI &mdash; no code required
            </p>

            <h1 className="text-[2.75rem] sm:text-5xl lg:text-[3.5rem] font-bold leading-[1.08] tracking-tight mb-6 text-white">
              Ask your health data anything.
            </h1>

            <p className="text-[17px] text-white/65 leading-relaxed mb-10 max-w-md">
              Connect your fitness devices. See everything on one dashboard. Then open Claude and ask questions in plain language &mdash; Why did my HRV drop? Am I recovering enough? Real answers from your real data.
            </p>

            <div className="flex flex-wrap items-center gap-3 mb-4">
              <Link to="/login" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium bg-white text-black hover:bg-white/90 transition-colors">
                Get Started Free
                <ArrowRightIcon className="w-3.5 h-3.5" />
              </Link>
              <a href="#how-it-works" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-medium border border-white/[.12] text-white/60 hover:text-white hover:border-white/25 transition-colors">
                See how it works
              </a>
            </div>

            <p className="text-[13px] text-white/40">
              Free forever. No credit card. Open source.
            </p>
          </div>

          <div className="hidden lg:block">
            <ConversationMock />
          </div>
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ HOW IT WORKS ═══ */}
      <section id="how-it-works" className="max-w-5xl mx-auto px-5 py-20">
        <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3">How it works</p>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-12">Up and running in four steps.</h2>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-12">
          {[
            { n: '1', title: 'Create an account', desc: 'Sign up with Google or email. Takes 30 seconds.' },
            { n: '2', title: 'Connect your devices', desc: 'Link Fitbit, Renpho, and Hevy. Data flows automatically.' },
            { n: '3', title: 'See your dashboard', desc: '15+ metrics in one place. Sleep, heart rate, workouts, body composition.' },
            { n: '4', title: 'Ask Claude', desc: 'Open claude.ai, connect TONND, and ask anything. No code needed.', accent: true },
          ].map((s) => (
            <div key={s.n}>
              <div className={`text-[13px] font-mono mb-3 ${s.accent ? 'text-cyan-400/60' : 'text-white/20'}`}>{s.n}.</div>
              <h3 className="text-base font-semibold text-white/80 mb-2">{s.title}</h3>
              <p className="text-sm text-white/40 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ AI SHOWCASE ═══ */}
      <section id="ai" className="max-w-5xl mx-auto px-5 py-20">
        <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3">Ask your data</p>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4">Dashboards show data. Claude explains it.</h2>
        <p className="text-[15px] text-white/40 mb-12 max-w-lg">
          Connect your TONND account in Claude.ai and ask questions in plain language. Claude pulls from your Fitbit, Renpho, and Hevy data and gives you answers no chart can.
        </p>

        <div className="grid lg:grid-cols-5 gap-8">
          {/* example questions — 3 columns */}
          <div className="lg:col-span-3 space-y-3">
            {[
              { q: 'My HRV dropped from 48 to 28. What did I do differently?', sources: ['Fitbit Vitals', 'Hevy', 'Sleep'] },
              { q: "What's my sleep like on workout days vs. rest days?", sources: ['Sleep', 'Hevy'] },
              { q: 'My weight stalled for two weeks. What changed?', sources: ['Renpho', 'Hevy', 'Fitbit Sleep'] },
              { q: "Am I gaining weight because I'm training less or sleeping worse?", sources: ['Renpho', 'Hevy', 'Fitbit Activity'] },
            ].map((item) => (
              <div key={item.q} className="rounded-lg border border-white/[.06] bg-white/[.02] p-4">
                <p className="text-[14px] text-white/70 leading-relaxed mb-2">{item.q}</p>
                <div className="flex gap-1.5">
                  {item.sources.map((s) => (
                    <span key={s} className="text-[10px] px-2 py-0.5 rounded bg-white/[.08] text-white/50 border border-white/[.08]">{s}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* setup card — 2 columns */}
          <div className="lg:col-span-2">
            <div className="rounded-lg border border-white/[.06] bg-white/[.02] p-6 sticky top-20">
              <h3 className="text-base font-semibold text-white/80 mb-1">Two accounts. Zero code.</h3>
              <p className="text-[13px] text-white/35 mb-6">Works with any Claude plan.</p>
              <div className="space-y-4 mb-6">
                {[
                  { n: '1', text: 'Sign up at tonnd.com' },
                  { n: '2', text: 'Connect TONND in Claude.ai Connectors' },
                  { n: '3', text: 'Start asking' },
                ].map((step) => (
                  <div key={step.n} className="flex gap-3 items-start">
                    <span className="text-[12px] font-mono text-cyan-400/60 mt-0.5">{step.n}.</span>
                    <span className="text-[13px] text-white/55">{step.text}</span>
                  </div>
                ))}
              </div>
              <Link to="/login" className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium bg-white text-black hover:bg-white/90 transition-colors w-full justify-center">
                Get Started Free
                <ArrowRightIcon className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ DIVIDER ═══ */}
      <div className="border-t border-white/[.06]" />

      {/* ═══ FEATURES ═══ */}
      <section id="features" className="max-w-5xl mx-auto px-5 py-20">

        {/* Connect */}
        <div className="mb-20">
          <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3">Connect</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4">Bring your devices together.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg">
            Link Fitbit, Renpho, and Hevy. Data flows automatically into your dashboard.
          </p>
          <div className="grid sm:grid-cols-3 gap-px bg-white/[.06] rounded-lg overflow-hidden">
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
                  <p className="text-sm text-white/40 leading-relaxed">Workout tracking &mdash; exercises, sets, reps, volume, and muscle group analysis.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Track */}
        <div className="mb-20">
          <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3">Track</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4">Every metric that matters.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg">
            15+ health metrics in a single dashboard. Trends over days, weeks, and months.
          </p>

          <div className="grid lg:grid-cols-2 gap-8 items-start">
            {/* metric grid */}
            <div className="grid sm:grid-cols-2 gap-px bg-white/[.06] rounded-lg overflow-hidden">
              {[
                { icon: MoonIcon, title: 'Sleep', desc: 'Stages, efficiency, and duration trends.' },
                { icon: BoltIcon, title: 'Activity', desc: 'Steps, calories, distance, active zone minutes.' },
                { icon: HeartIcon, title: 'Heart Rate & HRV', desc: 'Resting HR, zones, and recovery tracking.' },
                { icon: ScaleIcon, title: 'Weight & Body Comp', desc: 'Weight, body fat, muscle mass, BMI.' },
                { icon: FireIcon, title: 'Workouts', desc: 'Exercises, volume, muscle heatmap.' },
                { icon: ChartBarSquareIcon, title: 'Recovery Score', desc: 'Composite from HRV, sleep, and resting HR.' },
                { icon: BeakerIcon, title: 'VO\u2082 Max & SpO\u2082', desc: 'Cardio fitness and blood oxygen.' },
                { icon: ChatBubbleLeftRightIcon, title: 'AI Analysis', desc: 'Ask Claude anything about your data.' },
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

            {/* dashboard mock */}
            <div className="hidden lg:block">
              <DashboardMock />
            </div>
          </div>
        </div>

        {/* Own */}
        <div>
          <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3">Open source</p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4">Your data, your rules.</h2>
          <p className="text-[15px] text-white/40 mb-8 max-w-lg">
            TONND is fully open source. Use our managed cloud or run it on your own server &mdash; you always own your data.
          </p>
          <div className="grid sm:grid-cols-3 gap-px bg-white/[.06] rounded-lg overflow-hidden">
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

      {/* ═══ PRIVACY ═══ */}
      <section className="max-w-5xl mx-auto px-5 py-20">
        <p className="text-[13px] text-white/40 font-medium tracking-wide mb-3">Privacy</p>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white/90 mb-4">Your health data is personal.</h2>
        <p className="text-[15px] text-white/40 mb-12 max-w-lg">
          TONND gives you full control. Use our cloud or self-host &mdash; either way, your data stays yours.
        </p>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-12">
          {[
            { title: 'Privacy first', desc: 'No tracking, no ads, no third-party data sharing. Your health data never enters a training dataset.' },
            { title: 'Your data', desc: 'Standard PostgreSQL. Export or delete anytime.' },
            { title: 'Open code', desc: 'AGPL-3.0 licensed. Inspect every line, including the AI server.' },
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
      <section className="max-w-5xl mx-auto px-5 py-24 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
          Your health data has stories to tell.
        </h2>
        <p className="text-[15px] text-white/40 max-w-md mx-auto mb-10">
          Connect your devices. Ask your questions. Free and open source.
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

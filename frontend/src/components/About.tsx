import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { GITHUB_URL, DISCORD_URL, LOGO_PATH } from '../config/theme'
import SEO from './SEO'

export default function About() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <SEO title="About" description="TONND is built by Dr. Wahed Hemati — a developer and researcher who has been tracking health data since he was 12. Open source, self-hosted, built in Frankfurt." path="/about" />
      <Helmet>
        <script type="application/ld+json">{JSON.stringify({
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'AboutPage',
              '@id': 'https://tonnd.com/about',
              'name': 'About TONND',
              'url': 'https://tonnd.com/about',
              'isPartOf': { '@id': 'https://tonnd.com/#website' },
              'mainEntity': { '@id': 'https://tonnd.com/#person-wahed' }
            },
            {
              '@type': 'Person',
              '@id': 'https://tonnd.com/#person-wahed',
              'name': 'Dr. Wahed Hemati',
              'url': 'https://tonnd.com/about',
              'jobTitle': 'Founder & Developer',
              'worksFor': { '@id': 'https://tonnd.com/#organization' },
              'sameAs': [
                'https://github.com/hemati'
              ]
            },
            {
              '@type': 'BreadcrumbList',
              'itemListElement': [
                { '@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': 'https://tonnd.com/' },
                { '@type': 'ListItem', 'position': 2, 'name': 'About', 'item': 'https://tonnd.com/about' }
              ]
            }
          ]
        })}</script>
      </Helmet>

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

          <h2 className="text-xl font-bold text-white/90 pt-2">Why this exists</h2>

          <p>
            I have a Fitbit on my wrist, a Renpho scale in the bathroom, and Hevy on my phone for workouts. Three devices, three apps, three dashboards. None of them talk to each other. I can't look at my sleep data next to my HRV next to my training volume and see what's actually going on.
          </p>

          <p>
            Then in July 2024, Google killed the Fitbit web dashboard. Millions of people lost the only way to look at their health data on a real screen. The phone app stayed, but the detailed analysis, the long-term trends, the stuff you actually need a monitor for? Gone.
          </p>

          <p>
            So I built TONND. One dashboard for everything: sleep stages, HRV, VO&#x2082; Max, SpO&#x2082;, weight, body fat, muscle mass, workout volume, recovery scores. Connect your Fitbit, Renpho, and Hevy, and it all shows up in one place. You can look at 7 days or 30 days. You can see which muscles you worked this week as a heatmap on a body diagram.
          </p>

          <h2 className="text-xl font-bold text-white/90 pt-4">Who I am</h2>

          <p>
            I'm <strong className="text-white/80">Wahed Hemati</strong>. I have a PhD in computational linguistics (natural language processing, specifically) and I've been building software for a while. I live in Frankfurt.
          </p>

          <p>
            I started tracking my weight in Excel when I was 12. Bathroom scale, manual entry, formulas to calculate weekly averages. I was a chubby kid trying to figure out what worked. The devices got better over the years but nobody ever built the thing that brings it all together. I kept waiting for Fitbit or Apple or Google to do it. They didn't. So here we are.
          </p>

          <p>
            I also built <a href="https://www.ceve.guru" target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">ceve.guru</a>, an AI resume builder for the German job market.
          </p>

          <h2 className="text-xl font-bold text-white/90 pt-4">How it's built</h2>

          <p>
            The whole thing is open source (AGPL-3.0). Backend is FastAPI with PostgreSQL. Frontend is React and TypeScript. You deploy it with Docker Compose. Auth goes through fastapi-users (JWT + Google OAuth). Fitbit tokens are Fernet-encrypted at rest. There's a scheduler that syncs everything daily.
          </p>

          <p>
            For the workout muscle data, I pull the actual muscle groups from the Hevy exercise template API instead of trying to guess from exercise names. Each exercise gets its real primary and secondary muscles, weighted proportionally. The result shows up as an interactive body heatmap you can click on.
          </p>

          <h2 className="text-xl font-bold text-white/90 pt-4">How I think about this project</h2>

          <p>
            Data is stored on EU servers in Frankfurt. I don't run ads, I don't sell data, I don't share it with anyone. If you want even more control, self-host the whole thing on your own hardware.
          </p>

          <p>
            The code is on GitHub. All of it. The database is plain PostgreSQL, so you can export or back up your data whenever you want. There's no lock-in.
          </p>

          <p>
            I don't do gamification. There are no streaks, no badges, no push notifications trying to get you to open the app. Just your data, your trends, and the context you need to make sense of them.
          </p>

          <h2 className="text-xl font-bold text-white/90 pt-4">Where TONND is now</h2>

          <p>
            Phase one (done): all your devices in one dashboard. Fitbit vitals, Renpho body composition, Hevy workouts, recovery scores, muscle heatmaps. 15+ metrics unified.
          </p>
          <p>
            Phase two (done): TONND connects to Claude via the <Link to="/blog/mcp-blog-post" className="text-white/60 underline hover:text-white/80">Model Context Protocol</Link>. You can ask your health data questions in plain language. No code, no exports. Just connect your TONND account in Claude.ai and start asking.
          </p>
          <p>
            Phase three (in progress): the AI notices things you didn't ask about. HRV trending down while training volume is up. Sleep efficiency dropping every Sunday. Recomposition happening even though the scale isn't moving.
          </p>

          <p className="text-[13px] text-white/30 italic mt-4">
            TONND is a data tracking tool, not a medical device. Recovery scores and training insights are based on your personal data and general research, not clinical guidance. Consult a healthcare provider for medical decisions.
          </p>

          <h2 className="text-xl font-bold text-white/90 pt-4">Get in touch</h2>

          <div className="space-y-2">
            <p>
              Email: <a href="mailto:info@tonnd.com" className="text-white/60 underline hover:text-white/80">info@tonnd.com</a>
            </p>
            <p>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">GitHub</a> for code, bugs, and contributions
            </p>
            <p>
              <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer" className="text-white/60 underline hover:text-white/80">Discord</a> for questions and feature ideas
            </p>
            <p>
              Frankfurt am Main, Germany
            </p>
            <p className="text-white/30 text-sm pt-2">
              <Link to="/impressum" className="underline hover:text-white/50">Impressum</Link> · <Link to="/privacy" className="underline hover:text-white/50">Privacy Policy</Link>
            </p>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-white/[.06] flex gap-6 text-[13px] text-white/30">
          <Link to="/" className="hover:text-white/60 transition-colors">Home</Link>
          <Link to="/terms" className="hover:text-white/60 transition-colors">Terms</Link>
          <Link to="/privacy" className="hover:text-white/60 transition-colors">Privacy</Link>
          <Link to="/impressum" className="hover:text-white/60 transition-colors">Impressum</Link>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  BeakerIcon, LinkIcon, ChartBarSquareIcon, CpuChipIcon, FlagIcon,
  RocketLaunchIcon, DevicePhoneMobileIcon, ScaleIcon, SparklesIcon,
  LockClosedIcon, GlobeEuropeAfricaIcon, CloudIcon, ArrowTrendingUpIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline'

export default function Login() {
  const { login, register, loginWithGoogle } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      if (isRegister) {
        await register(email, password)
      } else {
        await login(email, password)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleGoogleLogin = () => {
    loginWithGoogle()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Side - Mission & Info */}
          <div className="space-y-8">
            {/* Logo and Title */}
            <div>
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-emerald-500 mb-4">
                <BeakerIcon className="h-8 w-8 text-white" />
              </div>
              <h1 className="text-4xl lg:text-5xl font-bold text-white mb-4">
                TONND
              </h1>
              <p className="text-xl text-slate-300">
                Your personal health intelligence hub
              </p>
            </div>

            {/* Mission Statement */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700/50">
              <h2 className="text-lg font-semibold text-cyan-400 mb-3 flex items-center gap-2">
                <FlagIcon className="h-5 w-5" /> Our Mission
              </h2>
              <p className="text-slate-300 leading-relaxed">
                We're building the <strong className="text-white">ultimate health data hub</strong> that brings together 
                all your health information from different devices and apps into one place. 
                No more switching between Fitbit, Renpho, Apple Health, and other apps – 
                see your complete health picture in a single, beautiful dashboard.
              </p>
            </div>

            {/* What We Do */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <SparklesIcon className="h-5 w-5 text-yellow-400" /> What TONND Does
              </h2>
              
              <div className="grid gap-3">
                <div className="flex items-start gap-3 bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                  <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                    <LinkIcon className="h-5 w-5 text-cyan-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">Connect All Your Devices</h3>
                    <p className="text-sm text-slate-400">
                      Fitbit, Renpho, Withings, Oura Ring, Apple Watch, and more – all in one place.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                    <ChartBarSquareIcon className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">Unified Health Dashboard</h3>
                    <p className="text-sm text-slate-400">
                      Track weight, sleep, activity, heart rate, HRV, SpO2, and body composition together.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                    <CpuChipIcon className="h-5 w-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">AI-Powered Insights</h3>
                    <p className="text-sm text-slate-400">
                      Get personalized daily recommendations based on your goals and real data.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                  <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                    <FlagIcon className="h-5 w-5 text-amber-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">Goal-Based Coaching</h3>
                    <p className="text-sm text-slate-400">
                      Whether it's weight loss, better sleep, or peak performance – we help you get there.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Coming Soon */}
            <div className="bg-gradient-to-r from-purple-500/10 to-cyan-500/10 rounded-xl p-4 border border-purple-500/20">
              <h3 className="font-medium text-white mb-2 flex items-center gap-2">
                <RocketLaunchIcon className="h-5 w-5 text-purple-400" /> Coming Soon
              </h3>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300">Renpho Integration</span>
                <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300">Withings Sync</span>
                <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300">Oura Ring</span>
                <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300">Daily AI Tips</span>
                <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300">Meal Tracking</span>
                <span className="px-3 py-1 bg-slate-700/50 rounded-full text-xs text-slate-300">Workout Plans</span>
              </div>
            </div>
          </div>

          {/* Right Side - Login Card */}
          <div className="lg:pl-8">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-3xl p-8 border border-slate-700/50 shadow-2xl">
              <h2 className="text-2xl font-semibold text-white mb-2 text-center">
                Get Started Free
              </h2>
              <p className="text-slate-400 text-center mb-8">
                Connect your first device in under 2 minutes
              </p>

              <button
                onClick={handleGoogleLogin}
                className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-100 text-gray-800 font-medium py-4 px-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-[1.02]"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </button>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-700"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-slate-800/50 text-slate-400">or continue with email</span>
                </div>
              </div>

              {/* Email/Password Form */}
              <form onSubmit={handleSubmit} className="space-y-3">
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                />
                {error && (
                  <p className="text-red-400 text-sm">{error}</p>
                )}
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-600 hover:to-emerald-600 text-white font-medium rounded-xl transition-all duration-200 disabled:opacity-50"
                >
                  {isSubmitting ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
                </button>
                <p className="text-center text-sm text-slate-400">
                  {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
                  <button
                    type="button"
                    onClick={() => { setIsRegister(!isRegister); setError(null) }}
                    className="text-cyan-400 hover:text-cyan-300"
                  >
                    {isRegister ? 'Sign In' : 'Create one'}
                  </button>
                </p>
              </form>

              {/* Supported Devices */}
              <div className="mt-8">
                <p className="text-xs text-slate-500 text-center mb-4">Currently supporting</p>
                <div className="flex justify-center items-center gap-6">
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 rounded-xl bg-[#00B0B9]/20 flex items-center justify-center mb-1">
                      <DevicePhoneMobileIcon className="h-6 w-6 text-[#00B0B9]" />
                    </div>
                    <span className="text-xs text-slate-400">Fitbit</span>
                  </div>
                  <div className="flex flex-col items-center opacity-50">
                    <div className="w-12 h-12 rounded-xl bg-slate-700/50 flex items-center justify-center mb-1">
                      <ScaleIcon className="h-6 w-6 text-slate-400" />
                    </div>
                    <span className="text-xs text-slate-500">Renpho</span>
                    <span className="text-[10px] text-slate-600">Soon</span>
                  </div>
                  <div className="flex flex-col items-center opacity-50">
                    <div className="w-12 h-12 rounded-xl bg-slate-700/50 flex items-center justify-center mb-1">
                      <SparklesIcon className="h-6 w-6 text-slate-400" />
                    </div>
                    <span className="text-xs text-slate-500">Oura</span>
                    <span className="text-[10px] text-slate-600">Soon</span>
                  </div>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-slate-700/50">
                <p className="text-xs text-slate-500 text-center">
                  By signing in, you agree to our{' '}
                  <Link to="/terms" className="text-cyan-400 hover:text-cyan-300">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link to="/privacy" className="text-cyan-400 hover:text-cyan-300">
                    Privacy Policy
                  </Link>
                </p>
              </div>
            </div>

            {/* Trust Badges */}
            <div className="mt-6 flex justify-center items-center gap-6 text-slate-500 text-xs">
              <div className="flex items-center gap-1">
                <LockClosedIcon className="h-4 w-4" /> SSL Encrypted
              </div>
              <div className="flex items-center gap-1">
                <GlobeEuropeAfricaIcon className="h-4 w-4" /> GDPR Compliant
              </div>
              <div className="flex items-center gap-1">
                <CloudIcon className="h-4 w-4" /> Open Source
              </div>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-20 grid md:grid-cols-3 gap-6">
          <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/30 text-center">
            <div className="w-14 h-14 rounded-2xl bg-cyan-500/20 flex items-center justify-center mx-auto mb-4">
              <ArrowTrendingUpIcon className="h-7 w-7 text-cyan-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Track Everything</h3>
            <p className="text-slate-400 text-sm">
              Weight, sleep, steps, heart rate, HRV, VO2 Max, and more – all visualized beautifully.
            </p>
          </div>
          
          <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/30 text-center">
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/20 flex items-center justify-center mx-auto mb-4">
              <FlagIcon className="h-7 w-7 text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Set Your Goals</h3>
            <p className="text-slate-400 text-sm">
              Define what matters to you – weight loss, better sleep, or athletic performance.
            </p>
          </div>
          
          <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/30 text-center">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center mx-auto mb-4">
              <LightBulbIcon className="h-7 w-7 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Get Smart Tips</h3>
            <p className="text-slate-400 text-sm">
              Our AI analyzes your data and gives you actionable advice every single day.
            </p>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-20 pt-8 border-t border-slate-800 text-center">
          <div className="flex flex-wrap justify-center gap-6 text-sm text-slate-500">
            <Link to="/terms" className="hover:text-slate-300 transition-colors">Terms of Service</Link>
            <Link to="/privacy" className="hover:text-slate-300 transition-colors">Privacy Policy</Link>
            <Link to="/cookies" className="hover:text-slate-300 transition-colors">Cookie Policy</Link>
            <a href="https://github.com/hemati/tonnd/issues" className="hover:text-slate-300 transition-colors">Contact</a>
          </div>
          <div className="mt-4 flex flex-wrap justify-center gap-4 text-xs text-slate-600">
            <span className="flex items-center gap-1">
              <GlobeEuropeAfricaIcon className="h-3 w-3" />
              <Link to="/privacy#ccpa" className="hover:text-slate-400">Do Not Sell My Personal Information</Link>
            </span>
            <span className="flex items-center gap-1">
              <GlobeEuropeAfricaIcon className="h-3 w-3" />
              <Link to="/privacy#gdpr" className="hover:text-slate-400">GDPR Rights</Link>
            </span>
          </div>
          <p className="mt-4 text-xs text-slate-600">
            © 2026 TONND. All rights reserved.
          </p>
        </footer>
      </div>
    </div>
  )
}

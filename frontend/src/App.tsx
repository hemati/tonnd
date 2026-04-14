import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { initAnalytics, trackPageView } from './lib/analytics'
import LandingPage from './components/LandingPage'
import Login from './components/Login'
import AuthCallback from './components/AuthCallback'
import Layout from './components/Layout'
import { CookieConsent } from './components/CookieConsent'
import NotFound from './components/NotFound'

// Lazy-loaded routes for code splitting
const Dashboard = lazy(() => import('./components/Dashboard'))
const Sources = lazy(() => import('./components/Sources'))
const BlogIndex = lazy(() => import('./components/BlogIndex'))
const BlogPost = lazy(() => import('./components/BlogPost'))
const About = lazy(() => import('./components/About'))
const TermsOfService = lazy(() => import('./components/TermsOfService').then(m => ({ default: m.TermsOfService })))
const PrivacyPolicy = lazy(() => import('./components/PrivacyPolicy').then(m => ({ default: m.PrivacyPolicy })))
const CookiePolicy = lazy(() => import('./components/CookiePolicy').then(m => ({ default: m.CookiePolicy })))
const Impressum = lazy(() => import('./components/Impressum').then(m => ({ default: m.Impressum })))
const Settings = lazy(() => import('./components/Settings'))

function LoadingSpinner() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
    </div>
  )
}

function PageViewTracker() {
  const location = useLocation()
  useEffect(() => { trackPageView(location.pathname) }, [location.pathname])
  return null
}

function App() {
  const { isAuthenticated, isLoading, user } = useAuth()

  useEffect(() => { initAnalytics() }, [])

  // Signal to prerenderer that the page is ready
  useEffect(() => {
    if (!isLoading) {
      document.dispatchEvent(new Event('app-rendered'))
    }
  }, [isLoading])

  // Auth callback must render before the loading gate — it sets the token
  // that checkAuth() then validates. Without this, the protected route
  // redirects to /login before the callback can store the token.
  if (typeof window !== 'undefined' && window.location.pathname === '/auth/callback') {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/auth/callback" element={<AuthCallback />} />
        </Routes>
      </BrowserRouter>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/terms" element={<Suspense fallback={<LoadingSpinner />}><TermsOfService /></Suspense>} />
        <Route path="/privacy" element={<Suspense fallback={<LoadingSpinner />}><PrivacyPolicy /></Suspense>} />
        <Route path="/cookies" element={<Suspense fallback={<LoadingSpinner />}><CookiePolicy /></Suspense>} />
        <Route path="/impressum" element={<Suspense fallback={<LoadingSpinner />}><Impressum /></Suspense>} />
        <Route path="/about" element={<Suspense fallback={<LoadingSpinner />}><About /></Suspense>} />
        <Route path="/blog" element={<Suspense fallback={<LoadingSpinner />}><BlogIndex /></Suspense>} />
        <Route path="/blog/:slug" element={<Suspense fallback={<LoadingSpinner />}><BlogPost /></Suspense>} />
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/dashboard"
          element={
            isAuthenticated ? (
              <Layout user={user}>
                <Suspense fallback={<LoadingSpinner />}>
                  <Dashboard />
                </Suspense>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Login />
            )
          }
        />
        <Route
          path="/sources"
          element={
            isAuthenticated ? (
              <Layout user={user}>
                <Suspense fallback={<LoadingSpinner />}>
                  <Sources />
                </Suspense>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/settings"
          element={
            isAuthenticated ? (
              <Layout user={user}>
                <Suspense fallback={<LoadingSpinner />}>
                  <Settings />
                </Suspense>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <PageViewTracker />
      <CookieConsent />
    </BrowserRouter>
  )
}

export default App

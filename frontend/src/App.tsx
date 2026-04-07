import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { initAnalytics, trackPageView } from './lib/analytics'
import LandingPage from './components/LandingPage'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import AuthCallback from './components/AuthCallback'
import FitbitConnect from './components/FitbitConnect'
import Layout from './components/Layout'
import { TermsOfService } from './components/TermsOfService'
import { PrivacyPolicy } from './components/PrivacyPolicy'
import { CookiePolicy } from './components/CookiePolicy'
import { CookieConsent } from './components/CookieConsent'
import NotFound from './components/NotFound'
import BlogIndex from './components/BlogIndex'
import BlogPost from './components/BlogPost'

function PageViewTracker() {
  const location = useLocation()
  useEffect(() => { trackPageView(location.pathname) }, [location.pathname])
  return null
}

function App() {
  const { isAuthenticated, isLoading, user } = useAuth()

  useEffect(() => { initAnalytics() }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/cookies" element={<CookiePolicy />} />
        <Route path="/blog" element={<BlogIndex />} />
        <Route path="/blog/:slug" element={<BlogPost />} />
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Layout user={user}>
                <Dashboard />
              </Layout>
            ) : (
              <LandingPage />
            )
          }
        />
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <Login />
            )
          }
        />
        <Route
          path="/connect-fitbit"
          element={
            isAuthenticated ? (
              <Layout user={user}>
                <FitbitConnect />
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

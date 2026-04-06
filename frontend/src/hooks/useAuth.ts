import { useState, useEffect, useCallback } from 'react'
import { API_URL, TOKEN_KEY } from '../config/constants'
import { trackEvent } from '../lib/analytics'

export interface User {
  userId: string
  email: string
}

export interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  accessToken: string | null
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    accessToken: null,
  })

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      setAuthState({ isAuthenticated: false, isLoading: false, user: null, accessToken: null })
      return
    }

    try {
      const res = await fetch(`${API_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Invalid token')

      const data = await res.json()
      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        user: { userId: data.id, email: data.email },
        accessToken: token,
      })
    } catch {
      localStorage.removeItem(TOKEN_KEY)
      setAuthState({ isAuthenticated: false, isLoading: false, user: null, accessToken: null })
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/auth/jwt/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Login failed')
    }

    const data = await res.json()
    localStorage.setItem(TOKEN_KEY, data.access_token)
    trackEvent('login', { method: 'email' })
    window.location.href = '/'
  }

  const register = async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Registration failed')
    }

    trackEvent('sign_up', { method: 'email' })
    await login(email, password)
  }

  const loginWithGoogle = async () => {
    const res = await fetch(`${API_URL}/auth/google/authorize`)
    const data = await res.json()
    window.location.href = data.authorization_url
  }

  const handleSignOut = () => {
    localStorage.removeItem(TOKEN_KEY)
    setAuthState({ isAuthenticated: false, isLoading: false, user: null, accessToken: null })
  }

  return {
    ...authState,
    login,
    register,
    loginWithGoogle,
    signOut: handleSignOut,
    checkAuth,
  }
}

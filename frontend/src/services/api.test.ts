import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Track interceptor registrations
const { requestInterceptors, responseInterceptors, mockGet, mockPost } = vi.hoisted(() => {
  const requestInterceptors: Array<{ fulfilled: (config: any) => any; rejected?: (error: any) => any }> = []
  const responseInterceptors: Array<{ fulfilled: (response: any) => any; rejected?: (error: any) => any }> = []
  const mockGet = vi.fn()
  const mockPost = vi.fn()
  return { requestInterceptors, responseInterceptors, mockGet, mockPost }
})

vi.mock('axios', () => {
  const instance = {
    get: mockGet,
    post: mockPost,
    interceptors: {
      request: {
        use: (fulfilled: any, rejected?: any) => {
          requestInterceptors.push({ fulfilled, rejected })
          return requestInterceptors.length - 1
        },
      },
      response: {
        use: (fulfilled: any, rejected?: any) => {
          responseInterceptors.push({ fulfilled, rejected })
          return responseInterceptors.length - 1
        },
      },
    },
  }

  return {
    default: {
      create: vi.fn(() => instance),
    },
  }
})

// Import after mock so the module gets our mocked axios
import { fetchUser, fetchDashboardData, initFitbitAuth, syncFitbitData } from './api'
import type { UserProfile, FitbitInitResponse, SyncResponse } from './api'

describe('api module', () => {
  const originalLocation = window.location

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { ...originalLocation, href: '' },
    })
  })

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      writable: true,
      value: originalLocation,
    })
  })

  describe('interceptor registration', () => {
    it('registers a request interceptor', () => {
      expect(requestInterceptors.length).toBeGreaterThanOrEqual(1)
    })

    it('registers a response interceptor', () => {
      expect(responseInterceptors.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('request interceptor', () => {
    function getRequestInterceptor() {
      return requestInterceptors[0].fulfilled
    }

    it('adds Authorization header when token exists in localStorage', () => {
      localStorage.setItem('access_token', 'test-token-123')
      const config = { headers: {} as Record<string, string> }
      const result = getRequestInterceptor()(config)
      expect(result.headers.Authorization).toBe('Bearer test-token-123')
    })

    it('does not add Authorization header when no token', () => {
      const config = { headers: {} as Record<string, string> }
      const result = getRequestInterceptor()(config)
      expect(result.headers.Authorization).toBeUndefined()
    })

    it('returns the config object', () => {
      const config = { headers: {} as Record<string, string> }
      const result = getRequestInterceptor()(config)
      expect(result).toBe(config)
    })
  })

  describe('response interceptor', () => {
    function getResponseSuccessHandler() {
      return responseInterceptors[0].fulfilled
    }

    function getResponseErrorHandler() {
      return responseInterceptors[0].rejected!
    }

    it('passes through successful responses', () => {
      const response = { status: 200, data: { ok: true } }
      const result = getResponseSuccessHandler()(response)
      expect(result).toBe(response)
    })

    it('clears token and redirects on 401 error', async () => {
      localStorage.setItem('access_token', 'old-token')
      const error = {
        response: { status: 401, data: { detail: 'Unauthorized' } },
        message: 'Request failed',
      }

      await expect(getResponseErrorHandler()(error)).rejects.toThrow('Unauthorized')
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(window.location.href).toBe('/')
    })

    it('extracts detail message from error response', async () => {
      const error = {
        response: { status: 400, data: { detail: 'Bad request data' } },
        message: 'Request failed',
      }

      await expect(getResponseErrorHandler()(error)).rejects.toThrow('Bad request data')
    })

    it('extracts message field from error response when no detail', async () => {
      const error = {
        response: { status: 500, data: { message: 'Server error occurred' } },
        message: 'Request failed',
      }

      await expect(getResponseErrorHandler()(error)).rejects.toThrow('Server error occurred')
    })

    it('falls back to error.message when no response data fields', async () => {
      const error = {
        response: { status: 500, data: {} },
        message: 'Network Error',
      }

      await expect(getResponseErrorHandler()(error)).rejects.toThrow('Network Error')
    })

    it('does not clear token for non-401 errors', async () => {
      localStorage.setItem('access_token', 'valid-token')
      const error = {
        response: { status: 403, data: { detail: 'Forbidden' } },
        message: 'Forbidden',
      }

      await expect(getResponseErrorHandler()(error)).rejects.toThrow('Forbidden')
      expect(localStorage.getItem('access_token')).toBe('valid-token')
    })
  })

  describe('API functions', () => {
    beforeEach(() => {
      mockGet.mockReset()
      mockPost.mockReset()
    })

    it('fetchUser calls GET /api/user and returns data', async () => {
      const mockUser: UserProfile = {
        user_id: '123',
        email: 'test@example.com',
        fitbit_connected: true,
        fitbit_user_id: 'fb123',
        renpho_connected: false,
        hevy_connected: false,
        last_sync: '2025-01-01T00:00:00Z',
      }
      mockGet.mockResolvedValueOnce({ data: mockUser })

      const result = await fetchUser()
      expect(mockGet).toHaveBeenCalledWith('/api/user')
      expect(result).toEqual(mockUser)
    })

    it('fetchDashboardData calls GET /api/data with default days=30', async () => {
      const mockData = { fitbit_connected: true }
      mockGet.mockResolvedValueOnce({ data: mockData })

      const result = await fetchDashboardData()
      expect(mockGet).toHaveBeenCalledWith('/api/data?days=30')
      expect(result).toEqual(mockData)
    })

    it('fetchDashboardData calls GET /api/data with custom days', async () => {
      const mockData = { fitbit_connected: true }
      mockGet.mockResolvedValueOnce({ data: mockData })

      await fetchDashboardData(7)
      expect(mockGet).toHaveBeenCalledWith('/api/data?days=7')
    })

    it('initFitbitAuth calls GET /auth/fitbit/init', async () => {
      const mockResponse: FitbitInitResponse = {
        authorization_url: 'https://fitbit.com/auth',
        state: 'abc123',
      }
      mockGet.mockResolvedValueOnce({ data: mockResponse })

      const result = await initFitbitAuth()
      expect(mockGet).toHaveBeenCalledWith('/auth/fitbit/init')
      expect(result).toEqual(mockResponse)
    })

    it('syncFitbitData calls POST /api/sync with default params', async () => {
      const mockResponse: SyncResponse = {
        success: true,
        message: 'Synced',
        synced_metrics: ['weight'],
        errors: [],
      }
      mockPost.mockResolvedValueOnce({ data: mockResponse })

      const result = await syncFitbitData()
      expect(mockPost).toHaveBeenCalledWith('/api/sync', { days: 1 })
      expect(result).toEqual(mockResponse)
    })

    it('syncFitbitData calls POST /api/sync with custom days', async () => {
      mockPost.mockResolvedValueOnce({ data: { success: true } })

      await syncFitbitData({ days: 7 })
      expect(mockPost).toHaveBeenCalledWith('/api/sync', { days: 7 })
    })

    it('syncFitbitData includes date when provided', async () => {
      mockPost.mockResolvedValueOnce({ data: { success: true } })

      await syncFitbitData({ days: 1, date: '2025-01-15' })
      expect(mockPost).toHaveBeenCalledWith('/api/sync', { days: 1, date: '2025-01-15' })
    })
  })

})

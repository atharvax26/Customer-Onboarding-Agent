/**
 * Test suite for API Client
 * Tests error handling, retry logic, loading states, and caching functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { apiClient, ApiError, NetworkError, TimeoutError } from '../services/apiClient'
import { apiCache } from '../utils/apiCache'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    apiCache.clear()
    mockLocalStorage.getItem.mockReturnValue('mock-token')
  })

  afterEach(() => {
    apiClient.cancelAllRequests()
  })

  describe('Authentication', () => {
    it('should include auth token in headers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1, email: 'test@example.com' })
      })

      await apiClient.auth.getCurrentUser()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/auth/me',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token'
          })
        })
      )
    })

    it('should handle login and store token', async () => {
      const mockResponse = {
        access_token: 'new-token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com', role: 'Developer' }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await apiClient.auth.login({
        email: 'test@example.com',
        password: 'password'
      })

      expect(result).toEqual(mockResponse)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'new-token')
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_user', JSON.stringify(mockResponse.user))
    })

    it('should handle logout and clear storage', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logged out' })
      })

      await apiClient.auth.logout()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_user')
    })
  })

  describe('Error Handling', () => {
    it('should throw ApiError for HTTP errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' })
      })

      await expect(apiClient.auth.getCurrentUser()).rejects.toThrow(ApiError)
      await expect(apiClient.auth.getCurrentUser()).rejects.toThrow('Not found')
    })

    it('should throw NetworkError for network failures', async () => {
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      await expect(apiClient.auth.getCurrentUser()).rejects.toThrow(NetworkError)
    })

    it('should throw TimeoutError for timeout', async () => {
      // Mock a request that never resolves to simulate timeout
      mockFetch.mockImplementationOnce(() => new Promise(() => {}))

      await expect(
        apiClient.auth.getCurrentUser()
      ).rejects.toThrow(TimeoutError)
    }, 35000) // Increase timeout for this test
  })

  describe('Retry Logic', () => {
    it('should retry on 5xx errors', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ detail: 'Server error' })
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ detail: 'Server error' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: 1, email: 'test@example.com' })
        })

      const result = await apiClient.auth.getCurrentUser()

      expect(mockFetch).toHaveBeenCalledTimes(3)
      expect(result).toEqual({ id: 1, email: 'test@example.com' })
    })

    it('should retry on 429 rate limit', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          json: async () => ({ detail: 'Rate limit exceeded' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: 1, email: 'test@example.com' })
        })

      const result = await apiClient.auth.getCurrentUser()

      expect(mockFetch).toHaveBeenCalledTimes(2)
      expect(result).toEqual({ id: 1, email: 'test@example.com' })
    })

    it('should not retry on 4xx client errors (except 429)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' })
      })

      await expect(apiClient.auth.getCurrentUser()).rejects.toThrow(ApiError)
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('Loading States', () => {
    it('should track loading states', async () => {
      let loadingDuringRequest = false

      mockFetch.mockImplementationOnce(async () => {
        loadingDuringRequest = apiClient.isLoading('GET:/auth/me')
        return {
          ok: true,
          json: async () => ({ id: 1, email: 'test@example.com' })
        }
      })

      const promise = apiClient.auth.getCurrentUser()
      
      // Check loading state immediately after starting request
      expect(apiClient.isLoading('GET:/auth/me')).toBe(true)
      
      await promise
      
      // Check that loading was true during request
      expect(loadingDuringRequest).toBe(true)
      
      // Check loading state after completion
      expect(apiClient.isLoading('GET:/auth/me')).toBe(false)
    })
  })

  describe('Caching', () => {
    it('should cache GET requests when enabled', async () => {
      const mockData = { id: 1, email: 'test@example.com' }
      
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockData
      })

      // First request
      const result1 = await apiClient.auth.getCurrentUser()
      expect(result1).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledTimes(1)

      // Second request should use cache
      const result2 = await apiClient.auth.getCurrentUser()
      expect(result2).toEqual(mockData)
      expect(mockFetch).toHaveBeenCalledTimes(1) // Still only 1 call
    })
  })

  describe('Document API', () => {
    it('should handle file upload with progress', async () => {
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
      const mockResponse = { document_id: 1, message: 'Upload successful' }
      
      // Mock XMLHttpRequest
      const mockXHR = {
        open: vi.fn(),
        send: vi.fn(),
        setRequestHeader: vi.fn(),
        upload: {
          addEventListener: vi.fn()
        },
        addEventListener: vi.fn(),
        status: 200,
        responseText: JSON.stringify(mockResponse)
      }

      // Mock XMLHttpRequest constructor
      global.XMLHttpRequest = vi.fn(() => mockXHR) as any

      const progressCallback = vi.fn()
      
      // Simulate successful upload
      setTimeout(() => {
        const loadHandler = mockXHR.addEventListener.mock.calls.find(
          call => call[0] === 'load'
        )?.[1]
        if (loadHandler) loadHandler()
      }, 0)

      const result = await apiClient.documents.upload(mockFile, progressCallback)

      expect(result).toEqual(mockResponse)
      expect(mockXHR.open).toHaveBeenCalledWith('POST', '/api/scaledown/upload')
      expect(mockXHR.send).toHaveBeenCalledWith(expect.any(FormData))
    })
  })

  describe('Analytics API', () => {
    it('should build query parameters correctly', async () => {
      const mockData = { total_users: 100, activation_rate: 0.75 }
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      })

      await apiClient.analytics.getActivationRates({
        role: 'Developer',
        start_date: '2024-01-01',
        end_date: '2024-01-31'
      })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/analytics/activation-rates?role=Developer&start_date=2024-01-01&end_date=2024-01-31',
        expect.any(Object)
      )
    })
  })

  describe('Request Cancellation', () => {
    it('should cancel specific requests', async () => {
      const mockAbortController = {
        abort: vi.fn(),
        signal: {}
      }
      
      global.AbortController = vi.fn(() => mockAbortController) as any

      // Start a request
      const promise = apiClient.auth.getCurrentUser()
      
      // Cancel it
      apiClient.cancelRequest('GET', '/auth/me')
      
      expect(mockAbortController.abort).toHaveBeenCalled()
    })

    it('should cancel all requests', async () => {
      const mockAbortController1 = { abort: vi.fn(), signal: {} }
      const mockAbortController2 = { abort: vi.fn(), signal: {} }
      
      let controllerIndex = 0
      global.AbortController = vi.fn(() => {
        return controllerIndex++ === 0 ? mockAbortController1 : mockAbortController2
      }) as any

      // Start multiple requests
      const promise1 = apiClient.auth.getCurrentUser()
      const promise2 = apiClient.documents.getAll()
      
      // Cancel all
      apiClient.cancelAllRequests()
      
      expect(mockAbortController1.abort).toHaveBeenCalled()
      expect(mockAbortController2.abort).toHaveBeenCalled()
    })
  })
})

describe('API Client Integration', () => {
  it('should handle complete authentication flow', async () => {
    // Mock successful login
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'test-token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com', role: 'Developer' }
      })
    })

    // Mock successful user fetch
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 1, email: 'test@example.com', role: 'Developer' })
    })

    // Login
    const loginResult = await apiClient.auth.login({
      email: 'test@example.com',
      password: 'password'
    })

    expect(loginResult.access_token).toBe('test-token')
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'test-token')

    // Update mock to return the new token
    mockLocalStorage.getItem.mockReturnValue('test-token')

    // Get current user
    const userResult = await apiClient.auth.getCurrentUser()
    expect(userResult.email).toBe('test@example.com')

    // Verify the new token was used
    expect(mockFetch).toHaveBeenLastCalledWith(
      '/api/auth/me',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-token'
        })
      })
    )
  })
})
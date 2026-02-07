/**
 * Comprehensive API Client for Customer Onboarding Agent
 * Provides typed API client with error handling, retry logic, loading states, and caching
 * Integrates with ScaleDown AI for document processing and intelligence
 */

import { 
  OnboardingSession, 
  OnboardingStep, 
  OnboardingProgress, 
  InteractionEvent, 
  InteractionTrackingResponse 
} from '../types/onboarding'
import { 
  Document, 
  ProcessedDocument, 
  DocumentUploadResponse, 
  DocumentStats 
} from '../types/document'
import { 
  HelpMessageResponse, 
  InterventionFeedback, 
  InterventionLog 
} from '../types/intervention'
import { 
  ActivationMetrics, 
  DropoffAnalysisResponse, 
  TrendData, 
  DashboardData, 
  RealTimeMetrics, 
  MetricsSummary, 
  AnalyticsFilters 
} from '../types/analytics'
import { 
  User, 
  UserCreate, 
  UserLogin, 
  UserLoginResponse 
} from '../types/auth'

// Configuration
const API_BASE_URL = '/api'
const DEFAULT_TIMEOUT = 30000 // 30 seconds
const MAX_RETRIES = 3
const RETRY_DELAY = 1000 // 1 second base delay

// Cache configuration
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
const cache = new Map<string, { data: any; timestamp: number }>()

// Error classes
export class ApiError extends Error {
  constructor(
    public status: number, 
    message: string, 
    public response?: Response
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network error occurred') {
    super(message)
    this.name = 'NetworkError'
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timeout') {
    super(message)
    this.name = 'TimeoutError'
  }
}

// Request configuration interface
interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: Record<string, string>
  body?: any
  timeout?: number
  retries?: number
  cache?: boolean
  cacheKey?: string
}

// Loading state management
type LoadingState = {
  [key: string]: boolean
}

class ApiClient {
  private loadingStates: LoadingState = {}
  private abortControllers: Map<string, AbortController> = new Map()

  // Token management
  private getAuthToken(): string | null {
    return localStorage.getItem('auth_token')
  }

  private createAuthHeaders(): Record<string, string> {
    const token = this.getAuthToken()
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  }

  // Cache management
  private getCacheKey(url: string, config?: RequestConfig): string {
    return config?.cacheKey || `${config?.method || 'GET'}:${url}`
  }

  private getFromCache(key: string): any | null {
    const cached = cache.get(key)
    if (!cached) return null
    
    const isExpired = Date.now() - cached.timestamp > CACHE_DURATION
    if (isExpired) {
      cache.delete(key)
      return null
    }
    
    return cached.data
  }

  private setCache(key: string, data: any): void {
    cache.set(key, { data, timestamp: Date.now() })
  }

  private clearCache(pattern?: string): void {
    if (!pattern) {
      cache.clear()
      return
    }
    
    for (const key of cache.keys()) {
      if (key.includes(pattern)) {
        cache.delete(key)
      }
    }
  }

  // Loading state management
  private setLoading(key: string, loading: boolean): void {
    this.loadingStates[key] = loading
  }

  public isLoading(key: string): boolean {
    return this.loadingStates[key] || false
  }

  public getAllLoadingStates(): LoadingState {
    return { ...this.loadingStates }
  }

  // Request timeout handling
  private createTimeoutPromise(timeout: number): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => reject(new TimeoutError()), timeout)
    })
  }

  // Retry logic with exponential backoff
  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private shouldRetry(error: any, attempt: number, maxRetries: number): boolean {
    if (attempt >= maxRetries) return false
    
    // Retry on network errors, timeouts, and 5xx server errors
    if (error instanceof NetworkError || error instanceof TimeoutError) {
      return true
    }
    
    if (error instanceof ApiError) {
      return error.status >= 500 || error.status === 429 // Server errors or rate limiting
    }
    
    return false
  }

  // Core request method with retry logic
  private async makeRequest<T>(
    url: string, 
    config: RequestConfig = {}
  ): Promise<T> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = DEFAULT_TIMEOUT,
      retries = MAX_RETRIES,
      cache: useCache = false
    } = config

    const fullUrl = `${API_BASE_URL}${url}`
    const cacheKey = this.getCacheKey(url, config)
    const loadingKey = `${method}:${url}`

    // Check cache for GET requests
    if (method === 'GET' && useCache) {
      const cached = this.getFromCache(cacheKey)
      if (cached) return cached
    }

    // Set loading state
    this.setLoading(loadingKey, true)

    let lastError: Error
    
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        // Create abort controller for this request
        const abortController = new AbortController()
        this.abortControllers.set(loadingKey, abortController)

        const requestInit: RequestInit = {
          method,
          headers: {
            ...this.createAuthHeaders(),
            ...headers
          },
          signal: abortController.signal
        }

        if (body && method !== 'GET') {
          requestInit.body = typeof body === 'string' ? body : JSON.stringify(body)
        }

        // Race between fetch and timeout
        const fetchPromise = fetch(fullUrl, requestInit)
        const timeoutPromise = this.createTimeoutPromise(timeout)
        
        const response = await Promise.race([fetchPromise, timeoutPromise])
        
        // Clean up abort controller
        this.abortControllers.delete(loadingKey)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
          throw new ApiError(
            response.status, 
            errorData.detail || `HTTP ${response.status}`, 
            response
          )
        }

        const data = await response.json()
        
        // Cache successful GET requests
        if (method === 'GET' && useCache) {
          this.setCache(cacheKey, data)
        }

        // Clear loading state and return data
        this.setLoading(loadingKey, false)
        return data

      } catch (error: any) {
        lastError = error
        
        // Handle different error types
        if (error.name === 'AbortError') {
          throw new Error('Request was cancelled')
        }
        
        if (error instanceof TypeError && error.message.includes('fetch')) {
          lastError = new NetworkError('Network request failed')
        }

        // Check if we should retry
        if (this.shouldRetry(lastError, attempt, retries)) {
          const delay = RETRY_DELAY * Math.pow(2, attempt) // Exponential backoff
          await this.sleep(delay)
          continue
        }

        break
      }
    }

    // Clear loading state and throw the last error
    this.setLoading(loadingKey, false)
    this.abortControllers.delete(loadingKey)
    throw lastError!
  }

  // Cancel specific request
  public cancelRequest(method: string, url: string): void {
    const loadingKey = `${method}:${url}`
    const controller = this.abortControllers.get(loadingKey)
    if (controller) {
      controller.abort()
      this.abortControllers.delete(loadingKey)
      this.setLoading(loadingKey, false)
    }
  }

  // Cancel all pending requests
  public cancelAllRequests(): void {
    for (const [key, controller] of this.abortControllers.entries()) {
      controller.abort()
      this.setLoading(key, false)
    }
    this.abortControllers.clear()
  }

  // Generic HTTP methods
  public async get<T = any>(url: string, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<T> {
    return this.makeRequest<T>(url, { ...config, method: 'GET' })
  }

  public async post<T = any>(url: string, body?: any, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<T> {
    return this.makeRequest<T>(url, { ...config, method: 'POST', body })
  }

  public async put<T = any>(url: string, body?: any, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<T> {
    return this.makeRequest<T>(url, { ...config, method: 'PUT', body })
  }

  public async patch<T = any>(url: string, body?: any, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<T> {
    return this.makeRequest<T>(url, { ...config, method: 'PATCH', body })
  }

  public async delete<T = any>(url: string, config?: Omit<RequestConfig, 'method' | 'body'>): Promise<T> {
    return this.makeRequest<T>(url, { ...config, method: 'DELETE' })
  }

  // Authentication API
  public auth = {
    register: async (userData: UserCreate): Promise<User> => {
      const response = await this.makeRequest<User>('/auth/register', {
        method: 'POST',
        body: userData
      })
      this.clearCache('auth')
      return response
    },

    login: async (credentials: UserLogin): Promise<UserLoginResponse> => {
      const response = await this.makeRequest<UserLoginResponse>('/auth/login', {
        method: 'POST',
        body: credentials
      })
      
      // Store token
      localStorage.setItem('auth_token', response.access_token)
      localStorage.setItem('auth_user', JSON.stringify(response.user))
      
      this.clearCache('auth')
      return response
    },

    logout: async (): Promise<{ message: string }> => {
      const response = await this.makeRequest<{ message: string }>('/auth/logout', {
        method: 'POST'
      })
      
      // Clear stored auth data
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      this.clearCache()
      
      return response
    },

    getCurrentUser: async (): Promise<User> => {
      return this.makeRequest<User>('/auth/me', {
        cache: true,
        cacheKey: 'current_user'
      })
    }
  }

  // Document/ScaleDown API
  public documents = {
    upload: async (
      file: File, 
      onProgress?: (progress: number) => void
    ): Promise<DocumentUploadResponse> => {
      return new Promise((resolve, reject) => {
        const formData = new FormData()
        formData.append('file', file)
        
        const xhr = new XMLHttpRequest()
        const token = this.getAuthToken()
        
        if (onProgress) {
          xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
              const progress = (event.loaded / event.total) * 100
              onProgress(progress)
            }
          })
        }
        
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText)
              this.clearCache('documents')
              resolve(response)
            } catch (e) {
              reject(new ApiError(xhr.status, 'Invalid JSON response'))
            }
          } else {
            try {
              const errorData = JSON.parse(xhr.responseText)
              reject(new ApiError(xhr.status, errorData.detail || 'Upload failed'))
            } catch (e) {
              reject(new ApiError(xhr.status, 'Upload failed'))
            }
          }
        })
        
        xhr.addEventListener('error', () => {
          reject(new NetworkError('Network error during upload'))
        })
        
        xhr.open('POST', `${API_BASE_URL}/scaledown/upload`)
        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`)
        }
        xhr.send(formData)
      })
    },

    uploadAndProcess: async (
      file: File, 
      onProgress?: (progress: number) => void
    ): Promise<ProcessedDocument> => {
      return new Promise((resolve, reject) => {
        const formData = new FormData()
        formData.append('file', file)
        
        const xhr = new XMLHttpRequest()
        const token = this.getAuthToken()
        
        if (onProgress) {
          xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
              const progress = (event.loaded / event.total) * 50 // Upload is 50%
              onProgress(progress)
            }
          })
          
          // Simulate processing progress after upload completes
          xhr.upload.addEventListener('load', () => {
            onProgress(50) // Upload complete, processing starting
            
            // Simulate processing progress
            let processingProgress = 50
            const processingInterval = setInterval(() => {
              processingProgress += 5
              if (processingProgress < 95) {
                onProgress(processingProgress)
              }
            }, 500) // Update every 500ms
            
            // Store interval ID to clear it later
            ;(xhr as any)._processingInterval = processingInterval
          })
        }
        
        xhr.addEventListener('load', () => {
          // Clear processing interval if it exists
          if ((xhr as any)._processingInterval) {
            clearInterval((xhr as any)._processingInterval)
          }
          
          if (onProgress) {
            onProgress(100) // Processing complete
          }
          
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText)
              this.clearCache('documents')
              resolve(response)
            } catch (e) {
              reject(new ApiError(xhr.status, 'Invalid JSON response'))
            }
          } else {
            try {
              const errorData = JSON.parse(xhr.responseText)
              reject(new ApiError(xhr.status, errorData.detail || 'Processing failed'))
            } catch (e) {
              reject(new ApiError(xhr.status, 'Processing failed'))
            }
          }
        })
        
        xhr.addEventListener('error', () => {
          // Clear processing interval if it exists
          if ((xhr as any)._processingInterval) {
            clearInterval((xhr as any)._processingInterval)
          }
          reject(new NetworkError('Network error during processing'))
        })
        
        xhr.addEventListener('abort', () => {
          // Clear processing interval if it exists
          if ((xhr as any)._processingInterval) {
            clearInterval((xhr as any)._processingInterval)
          }
          reject(new Error('Upload cancelled'))
        })
        
        xhr.open('POST', `${API_BASE_URL}/scaledown/upload-and-process`)
        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`)
        }
        xhr.send(formData)
      })
    },

    getAll: async (): Promise<Document[]> => {
      return this.makeRequest<Document[]>('/scaledown/documents', {
        cache: true,
        cacheKey: 'all_documents'
      })
    },

    getById: async (documentId: number): Promise<Document> => {
      return this.makeRequest<Document>(`/scaledown/documents/${documentId}`, {
        cache: true,
        cacheKey: `document_${documentId}`
      })
    },

    delete: async (documentId: number): Promise<{ message: string }> => {
      const response = await this.makeRequest<{ message: string }>(
        `/scaledown/documents/${documentId}`, 
        { method: 'DELETE' }
      )
      this.clearCache('documents')
      return response
    },

    process: async (documentId: number): Promise<ProcessedDocument> => {
      const response = await this.makeRequest<ProcessedDocument>(
        `/scaledown/documents/${documentId}/process`, 
        { method: 'POST' }
      )
      this.clearCache('documents')
      return response
    },

    getStats: async (documentId: number): Promise<DocumentStats> => {
      return this.makeRequest<DocumentStats>(
        `/scaledown/documents/${documentId}/stats`,
        { cache: true }
      )
    }
  }

  // Onboarding API
  public onboarding = {
    start: async (documentId: number): Promise<OnboardingSession> => {
      const response = await this.makeRequest<OnboardingSession>('/onboarding/start', {
        method: 'POST',
        body: { document_id: documentId }
      })
      this.clearCache('onboarding')
      return response
    },

    getCurrentStep: async (sessionId: number): Promise<OnboardingStep> => {
      return this.makeRequest<OnboardingStep>(
        `/onboarding/current-step/${sessionId}`,
        { cache: true }
      )
    },

    advanceStep: async (sessionId: number): Promise<any> => {
      const response = await this.makeRequest(`/onboarding/advance-step/${sessionId}`, {
        method: 'POST'
      })
      this.clearCache('onboarding')
      return response
    },

    getProgress: async (sessionId: number): Promise<OnboardingProgress> => {
      return this.makeRequest<OnboardingProgress>(
        `/onboarding/progress/${sessionId}`,
        { cache: true }
      )
    },

    getUserSessions: async (): Promise<OnboardingSession[]> => {
      return this.makeRequest<OnboardingSession[]>('/onboarding/sessions', {
        cache: true,
        cacheKey: 'user_sessions'
      })
    },

    getSessionDetails: async (sessionId: number): Promise<OnboardingSession> => {
      return this.makeRequest<OnboardingSession>(
        `/onboarding/session/${sessionId}`,
        { cache: true }
      )
    }
  }

  // Engagement API
  public engagement = {
    trackInteraction: async (event: InteractionEvent): Promise<InteractionTrackingResponse> => {
      return this.makeRequest<InteractionTrackingResponse>('/engagement/track-interaction', {
        method: 'POST',
        body: event
      })
    },

    getScore: async (userId?: number): Promise<any> => {
      const url = userId ? `/engagement/score/${userId}` : '/engagement/score'
      return this.makeRequest(url, { cache: true })
    }
  }

  // Intervention API
  public intervention = {
    checkForIntervention: async (sessionId: number): Promise<HelpMessageResponse | { help_message: null }> => {
      return this.makeRequest(`/intervention/check/${sessionId}`)
    },

    triggerManualHelp: async (sessionId: number, stepNumber: number): Promise<HelpMessageResponse> => {
      return this.makeRequest<HelpMessageResponse>('/intervention/manual-help', {
        method: 'POST',
        body: { session_id: sessionId, step_number: stepNumber }
      })
    },

    submitFeedback: async (feedback: InterventionFeedback): Promise<{ success: boolean }> => {
      return this.makeRequest<{ success: boolean }>('/intervention/feedback', {
        method: 'POST',
        body: feedback
      })
    },

    getHistory: async (sessionId?: number): Promise<InterventionLog[]> => {
      const url = sessionId 
        ? `/intervention/history?session_id=${sessionId}`
        : '/intervention/history'
      return this.makeRequest<InterventionLog[]>(url, { cache: true })
    }
  }

  // Analytics API
  public analytics = {
    getActivationRates: async (filters: AnalyticsFilters = {}): Promise<ActivationMetrics> => {
      const params = new URLSearchParams()
      if (filters.role) params.append('role', filters.role)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)
      if (filters.user_id) params.append('user_id', filters.user_id.toString())
      
      const url = `/analytics/activation-rates${params.toString() ? `?${params.toString()}` : ''}`
      return this.makeRequest<ActivationMetrics>(url, { cache: true })
    },

    getDropoffAnalysis: async (filters: AnalyticsFilters = {}): Promise<DropoffAnalysisResponse> => {
      const params = new URLSearchParams()
      if (filters.role) params.append('role', filters.role)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)
      if (filters.user_id) params.append('user_id', filters.user_id.toString())
      
      const url = `/analytics/dropoff-analysis${params.toString() ? `?${params.toString()}` : ''}`
      return this.makeRequest<DropoffAnalysisResponse>(url, { cache: true })
    },

    getEngagementTrends: async (userId?: number, daysBack: number = 30): Promise<TrendData> => {
      const params = new URLSearchParams()
      if (userId) params.append('user_id', userId.toString())
      params.append('days_back', daysBack.toString())
      
      return this.makeRequest<TrendData>(
        `/analytics/engagement-trends?${params.toString()}`,
        { cache: true }
      )
    },

    getDashboardData: async (): Promise<DashboardData> => {
      return this.makeRequest<DashboardData>('/analytics/dashboard', { cache: true })
    },

    getRealTimeMetrics: async (): Promise<RealTimeMetrics> => {
      return this.makeRequest<RealTimeMetrics>('/analytics/real-time-metrics')
    },

    getMetricsSummary: async (role?: string): Promise<MetricsSummary> => {
      const params = role ? `?role=${role}` : ''
      return this.makeRequest<MetricsSummary>(`/analytics/metrics/summary${params}`, {
        cache: true
      })
    },

    exportData: async (filters: AnalyticsFilters = {}, format: string = 'json'): Promise<any> => {
      const params = new URLSearchParams()
      if (filters.role) params.append('role', filters.role)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)
      if (filters.user_id) params.append('user_id', filters.user_id.toString())
      params.append('export_format', format)
      
      return this.makeRequest(`/analytics/export?${params.toString()}`)
    },

    refreshCache: async (): Promise<any> => {
      const response = await this.makeRequest('/analytics/metrics/refresh', {
        method: 'POST'
      })
      this.clearCache('analytics')
      return response
    },

    getAvailableRoles: async (): Promise<{ available_roles: string[], user_role: string, access_level: string }> => {
      return this.makeRequest('/analytics/filters/roles', { cache: true })
    },

    getUserAnalytics: async (userId: number): Promise<any> => {
      return this.makeRequest(`/analytics/user-analytics/${userId}`, { cache: true })
    }
  }
}

// Create singleton instance
export const apiClient = new ApiClient()

// Export types and utilities
export type { RequestConfig, LoadingState }
export { ApiClient }
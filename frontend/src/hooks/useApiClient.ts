/**
 * React hook for managing API client state and operations
 * Provides loading states, error handling, and convenient API access
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient, ApiError, NetworkError, TimeoutError } from '../services/apiClient'

// Hook return type
interface UseApiClientReturn {
  // Loading states
  isLoading: (key: string) => boolean
  getAllLoadingStates: () => Record<string, boolean>
  
  // Error handling
  error: string | null
  clearError: () => void
  
  // API client instance
  api: typeof apiClient
  
  // Request cancellation
  cancelRequest: (method: string, url: string) => void
  cancelAllRequests: () => void
  
  // Utilities
  handleApiError: (error: any) => string
  retry: <T>(operation: () => Promise<T>, maxRetries?: number) => Promise<T>
}

// Configuration options
interface UseApiClientOptions {
  // Auto-clear errors after specified time (ms)
  errorTimeout?: number
  
  // Enable automatic retry for failed requests
  enableAutoRetry?: boolean
  
  // Default number of retries
  defaultRetries?: number
}

export const useApiClient = (options: UseApiClientOptions = {}): UseApiClientReturn => {
  const {
    errorTimeout = 5000,
    enableAutoRetry = false,
    defaultRetries = 2
  } = options

  const [error, setError] = useState<string | null>(null)
  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({})
  const errorTimeoutRef = useRef<NodeJS.Timeout>()

  // Update loading states from API client
  useEffect(() => {
    const interval = setInterval(() => {
      const currentStates = apiClient.getAllLoadingStates()
      setLoadingStates(prev => {
        // Only update if states have changed
        const hasChanged = Object.keys(currentStates).some(
          key => currentStates[key] !== prev[key]
        ) || Object.keys(prev).some(
          key => currentStates[key] !== prev[key]
        )
        
        return hasChanged ? currentStates : prev
      })
    }, 100) // Check every 100ms

    return () => clearInterval(interval)
  }, [])

  // Auto-clear errors
  useEffect(() => {
    if (error && errorTimeout > 0) {
      errorTimeoutRef.current = setTimeout(() => {
        setError(null)
      }, errorTimeout)
    }

    return () => {
      if (errorTimeoutRef.current) {
        clearTimeout(errorTimeoutRef.current)
      }
    }
  }, [error, errorTimeout])

  // Clear error manually
  const clearError = useCallback(() => {
    setError(null)
    if (errorTimeoutRef.current) {
      clearTimeout(errorTimeoutRef.current)
    }
  }, [])

  // Check if specific operation is loading
  const isLoading = useCallback((key: string): boolean => {
    return loadingStates[key] || false
  }, [loadingStates])

  // Get all loading states
  const getAllLoadingStates = useCallback(() => {
    return loadingStates
  }, [loadingStates])

  // Handle API errors with user-friendly messages
  const handleApiError = useCallback((error: any): string => {
    let errorMessage: string

    if (error instanceof ApiError) {
      switch (error.status) {
        case 400:
          errorMessage = 'Invalid request. Please check your input.'
          break
        case 401:
          errorMessage = 'Authentication required. Please log in.'
          break
        case 403:
          errorMessage = 'Access denied. You don\'t have permission for this action.'
          break
        case 404:
          errorMessage = 'Resource not found.'
          break
        case 409:
          errorMessage = 'Conflict. The resource already exists or is in use.'
          break
        case 422:
          errorMessage = 'Validation error. Please check your input.'
          break
        case 429:
          errorMessage = 'Too many requests. Please try again later.'
          break
        case 500:
          errorMessage = 'Server error. Please try again later.'
          break
        case 502:
        case 503:
        case 504:
          errorMessage = 'Service temporarily unavailable. Please try again later.'
          break
        default:
          errorMessage = error.message || 'An unexpected error occurred.'
      }
    } else if (error instanceof NetworkError) {
      errorMessage = 'Network error. Please check your connection and try again.'
    } else if (error instanceof TimeoutError) {
      errorMessage = 'Request timeout. Please try again.'
    } else if (error.name === 'AbortError') {
      errorMessage = 'Request was cancelled.'
    } else {
      errorMessage = error.message || 'An unexpected error occurred.'
    }

    setError(errorMessage)
    return errorMessage
  }, [])

  // Retry mechanism with exponential backoff
  const retry = useCallback(async <T>(
    operation: () => Promise<T>,
    maxRetries: number = defaultRetries
  ): Promise<T> => {
    let lastError: any
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error
        
        // Don't retry on client errors (4xx) except 429 (rate limit)
        if (error instanceof ApiError && error.status >= 400 && error.status < 500 && error.status !== 429) {
          break
        }
        
        // Don't retry on the last attempt
        if (attempt === maxRetries) {
          break
        }
        
        // Wait before retrying (exponential backoff)
        const delay = Math.min(1000 * Math.pow(2, attempt), 10000) // Max 10 seconds
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    
    throw lastError
  }, [defaultRetries])

  // Cancel specific request
  const cancelRequest = useCallback((method: string, url: string) => {
    apiClient.cancelRequest(method, url)
  }, [])

  // Cancel all requests
  const cancelAllRequests = useCallback(() => {
    apiClient.cancelAllRequests()
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (errorTimeoutRef.current) {
        clearTimeout(errorTimeoutRef.current)
      }
    }
  }, [])

  return {
    isLoading,
    getAllLoadingStates,
    error,
    clearError,
    api: apiClient,
    cancelRequest,
    cancelAllRequests,
    handleApiError,
    retry
  }
}

// Specialized hooks for common operations
export const useAuth = () => {
  const { api, handleApiError, isLoading } = useApiClient()
  
  return {
    login: api.auth.login,
    register: api.auth.register,
    logout: api.auth.logout,
    getCurrentUser: api.auth.getCurrentUser,
    isLoading: (operation: 'login' | 'register' | 'logout' | 'getCurrentUser') => 
      isLoading(`POST:/auth/${operation}`) || isLoading(`GET:/auth/me`),
    handleError: handleApiError
  }
}

export const useDocuments = () => {
  const { api, handleApiError, isLoading } = useApiClient()
  
  return {
    upload: api.documents.upload,
    uploadAndProcess: api.documents.uploadAndProcess,
    getAll: api.documents.getAll,
    getById: api.documents.getById,
    delete: api.documents.delete,
    process: api.documents.process,
    getStats: api.documents.getStats,
    isLoading: (operation: string) => isLoading(`POST:/scaledown/${operation}`) || isLoading(`GET:/scaledown/${operation}`),
    handleError: handleApiError
  }
}

export const useOnboarding = () => {
  const { api, handleApiError, isLoading } = useApiClient()
  
  return {
    start: api.onboarding.start,
    getCurrentStep: api.onboarding.getCurrentStep,
    advanceStep: api.onboarding.advanceStep,
    getProgress: api.onboarding.getProgress,
    getUserSessions: api.onboarding.getUserSessions,
    getSessionDetails: api.onboarding.getSessionDetails,
    isLoading: (operation: string) => isLoading(`POST:/onboarding/${operation}`) || isLoading(`GET:/onboarding/${operation}`),
    handleError: handleApiError
  }
}

export const useAnalytics = () => {
  const { api, handleApiError, isLoading } = useApiClient()
  
  return {
    getActivationRates: api.analytics.getActivationRates,
    getDropoffAnalysis: api.analytics.getDropoffAnalysis,
    getEngagementTrends: api.analytics.getEngagementTrends,
    getDashboardData: api.analytics.getDashboardData,
    getRealTimeMetrics: api.analytics.getRealTimeMetrics,
    getMetricsSummary: api.analytics.getMetricsSummary,
    exportData: api.analytics.exportData,
    refreshCache: api.analytics.refreshCache,
    getAvailableRoles: api.analytics.getAvailableRoles,
    getUserAnalytics: api.analytics.getUserAnalytics,
    isLoading: (operation: string) => isLoading(`GET:/analytics/${operation}`) || isLoading(`POST:/analytics/${operation}`),
    handleError: handleApiError
  }
}

export const useEngagement = () => {
  const { api, handleApiError, isLoading } = useApiClient()
  
  return {
    trackInteraction: api.engagement.trackInteraction,
    getScore: api.engagement.getScore,
    isLoading: (operation: string) => isLoading(`POST:/engagement/${operation}`) || isLoading(`GET:/engagement/${operation}`),
    handleError: handleApiError
  }
}

export const useIntervention = () => {
  const { api, handleApiError, isLoading } = useApiClient()
  
  return {
    checkForIntervention: api.intervention.checkForIntervention,
    triggerManualHelp: api.intervention.triggerManualHelp,
    submitFeedback: api.intervention.submitFeedback,
    getHistory: api.intervention.getHistory,
    isLoading: (operation: string) => isLoading(`POST:/intervention/${operation}`) || isLoading(`GET:/intervention/${operation}`),
    handleError: handleApiError
  }
}
/**
 * API Context for global API state management
 * Provides centralized error handling, loading states, and API client access
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react'
import { apiClient, ApiError, NetworkError, TimeoutError } from '../services/apiClient'

// State interface
interface ApiState {
  // Global loading states
  loadingStates: Record<string, boolean>
  
  // Global error state
  error: string | null
  
  // Network status
  isOnline: boolean
  
  // Request queue for offline scenarios
  pendingRequests: Array<{
    id: string
    operation: () => Promise<any>
    retries: number
  }>
}

// Action types
type ApiAction =
  | { type: 'SET_LOADING'; payload: { key: string; loading: boolean } }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_ONLINE'; payload: boolean }
  | { type: 'ADD_PENDING_REQUEST'; payload: { id: string; operation: () => Promise<any> } }
  | { type: 'REMOVE_PENDING_REQUEST'; payload: string }
  | { type: 'UPDATE_LOADING_STATES'; payload: Record<string, boolean> }
  | { type: 'CLEAR_ALL_ERRORS' }
  | { type: 'CLEAR_ALL_LOADING' }

// Initial state
const initialState: ApiState = {
  loadingStates: {},
  error: null,
  isOnline: navigator.onLine,
  pendingRequests: []
}

// Reducer
const apiReducer = (state: ApiState, action: ApiAction): ApiState => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        loadingStates: {
          ...state.loadingStates,
          [action.payload.key]: action.payload.loading
        }
      }
    
    case 'UPDATE_LOADING_STATES':
      return {
        ...state,
        loadingStates: action.payload
      }
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload
      }
    
    case 'SET_ONLINE':
      return {
        ...state,
        isOnline: action.payload
      }
    
    case 'ADD_PENDING_REQUEST':
      return {
        ...state,
        pendingRequests: [
          ...state.pendingRequests,
          { ...action.payload, retries: 0 }
        ]
      }
    
    case 'REMOVE_PENDING_REQUEST':
      return {
        ...state,
        pendingRequests: state.pendingRequests.filter(req => req.id !== action.payload)
      }
    
    case 'CLEAR_ALL_ERRORS':
      return {
        ...state,
        error: null
      }
    
    case 'CLEAR_ALL_LOADING':
      return {
        ...state,
        loadingStates: {}
      }
    
    default:
      return state
  }
}

// Context interface
interface ApiContextValue {
  // State
  state: ApiState
  
  // Actions
  setError: (error: string | null) => void
  clearError: () => void
  clearAllErrors: () => void
  
  // Loading management
  isLoading: (key: string) => boolean
  isAnyLoading: () => boolean
  clearAllLoading: () => void
  
  // API client
  api: typeof apiClient
  
  // Error handling utilities
  handleApiError: (error: any) => string
  
  // Network utilities
  executeWhenOnline: (operation: () => Promise<any>) => Promise<any>
  retryPendingRequests: () => Promise<void>
}

// Create context
const ApiContext = createContext<ApiContextValue | undefined>(undefined)

// Provider component
interface ApiProviderProps {
  children: React.ReactNode
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(apiReducer, initialState)

  // Update loading states from API client
  useEffect(() => {
    const interval = setInterval(() => {
      const currentStates = apiClient.getAllLoadingStates()
      dispatch({ type: 'UPDATE_LOADING_STATES', payload: currentStates })
    }, 100)

    return () => clearInterval(interval)
  }, [])

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      dispatch({ type: 'SET_ONLINE', payload: true })
      // Retry pending requests when back online
      retryPendingRequests()
    }

    const handleOffline = () => {
      dispatch({ type: 'SET_ONLINE', payload: false })
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Error handling
  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error })
  }, [])

  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null })
  }, [])

  const clearAllErrors = useCallback(() => {
    dispatch({ type: 'CLEAR_ALL_ERRORS' })
  }, [])

  // Loading state management
  const isLoading = useCallback((key: string): boolean => {
    return state.loadingStates[key] || false
  }, [state.loadingStates])

  const isAnyLoading = useCallback((): boolean => {
    return Object.values(state.loadingStates).some(loading => loading)
  }, [state.loadingStates])

  const clearAllLoading = useCallback(() => {
    dispatch({ type: 'CLEAR_ALL_LOADING' })
    apiClient.cancelAllRequests()
  }, [])

  // Enhanced error handling with user-friendly messages
  const handleApiError = useCallback((error: any): string => {
    let errorMessage: string

    if (error instanceof ApiError) {
      switch (error.status) {
        case 400:
          errorMessage = 'Invalid request. Please check your input and try again.'
          break
        case 401:
          errorMessage = 'Your session has expired. Please log in again.'
          break
        case 403:
          errorMessage = 'You don\'t have permission to perform this action.'
          break
        case 404:
          errorMessage = 'The requested resource was not found.'
          break
        case 409:
          errorMessage = 'This action conflicts with existing data. Please refresh and try again.'
          break
        case 422:
          errorMessage = 'Please check your input - some fields may be invalid.'
          break
        case 429:
          errorMessage = 'Too many requests. Please wait a moment and try again.'
          break
        case 500:
          errorMessage = 'Server error. Our team has been notified. Please try again later.'
          break
        case 502:
        case 503:
        case 504:
          errorMessage = 'Service temporarily unavailable. Please try again in a few minutes.'
          break
        default:
          errorMessage = error.message || 'An unexpected error occurred. Please try again.'
      }
    } else if (error instanceof NetworkError) {
      errorMessage = state.isOnline 
        ? 'Network error. Please check your connection and try again.'
        : 'You appear to be offline. Please check your connection.'
    } else if (error instanceof TimeoutError) {
      errorMessage = 'Request timeout. The server is taking too long to respond.'
    } else if (error.name === 'AbortError') {
      errorMessage = 'Request was cancelled.'
    } else {
      errorMessage = error.message || 'An unexpected error occurred.'
    }

    setError(errorMessage)
    return errorMessage
  }, [state.isOnline, setError])

  // Execute operation when online, queue when offline
  const executeWhenOnline = useCallback(async (operation: () => Promise<any>): Promise<any> => {
    if (state.isOnline) {
      try {
        return await operation()
      } catch (error) {
        // If it's a network error and we're offline, queue the request
        if (error instanceof NetworkError && !navigator.onLine) {
          const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
          dispatch({ 
            type: 'ADD_PENDING_REQUEST', 
            payload: { id: requestId, operation } 
          })
          throw new Error('Request queued for when connection is restored')
        }
        throw error
      }
    } else {
      // Queue the request for when we're back online
      const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      dispatch({ 
        type: 'ADD_PENDING_REQUEST', 
        payload: { id: requestId, operation } 
      })
      throw new Error('You are offline. Request will be executed when connection is restored.')
    }
  }, [state.isOnline])

  // Retry pending requests
  const retryPendingRequests = useCallback(async (): Promise<void> => {
    if (!state.isOnline || state.pendingRequests.length === 0) {
      return
    }

    const requestsToRetry = [...state.pendingRequests]
    
    for (const request of requestsToRetry) {
      try {
        await request.operation()
        dispatch({ type: 'REMOVE_PENDING_REQUEST', payload: request.id })
      } catch (error) {
        // If still failing and haven't exceeded max retries, keep in queue
        if (request.retries < 3) {
          // Update retry count (this would need to be implemented in the reducer)
          continue
        } else {
          // Remove after max retries
          dispatch({ type: 'REMOVE_PENDING_REQUEST', payload: request.id })
          handleApiError(error)
        }
      }
    }
  }, [state.isOnline, state.pendingRequests, handleApiError])

  const contextValue: ApiContextValue = {
    state,
    setError,
    clearError,
    clearAllErrors,
    isLoading,
    isAnyLoading,
    clearAllLoading,
    api: apiClient,
    handleApiError,
    executeWhenOnline,
    retryPendingRequests
  }

  return (
    <ApiContext.Provider value={contextValue}>
      {children}
    </ApiContext.Provider>
  )
}

// Hook to use the API context
export const useApiContext = (): ApiContextValue => {
  const context = useContext(ApiContext)
  if (context === undefined) {
    throw new Error('useApiContext must be used within an ApiProvider')
  }
  return context
}

// Higher-order component for API error boundaries
interface ApiErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ApiErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<{ error: Error }> },
  ApiErrorBoundaryState
> {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ApiErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('API Error Boundary caught an error:', error, errorInfo)
    
    // You could send this to an error reporting service
    // errorReportingService.captureException(error, { extra: errorInfo })
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback
      return <FallbackComponent error={this.state.error!} />
    }

    return this.props.children
  }
}

// Default error fallback component
const DefaultErrorFallback: React.FC<{ error: Error }> = ({ error }) => (
  <div className="api-error-boundary">
    <h2>Something went wrong</h2>
    <p>An unexpected error occurred while communicating with the server.</p>
    <details>
      <summary>Error details</summary>
      <pre>{error.message}</pre>
    </details>
    <button onClick={() => window.location.reload()}>
      Reload page
    </button>
  </div>
)
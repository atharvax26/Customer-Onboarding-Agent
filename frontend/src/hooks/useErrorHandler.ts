import { useState, useCallback, useRef } from 'react'
import { trackEngagementEvent } from '../services/engagementService'

export interface ErrorState {
  hasError: boolean
  error?: Error
  message?: string
  details?: string
  errorId?: string
  timestamp?: string
  context?: string
  recoverable?: boolean
}

export interface ErrorHandlerOptions {
  trackError?: boolean
  showToast?: boolean
  logToConsole?: boolean
  maxRetries?: number
  retryDelay?: number
  context?: string
}

export interface ErrorRecoveryOptions {
  retry?: () => Promise<void> | void
  fallback?: () => any
  redirect?: string
}

export const useErrorHandler = (options: ErrorHandlerOptions = {}) => {
  const {
    trackError = true,
    showToast = false,
    logToConsole = true,
    maxRetries = 3,
    retryDelay = 1000,
    context = 'unknown'
  } = options

  const [errorState, setErrorState] = useState<ErrorState>({
    hasError: false
  })

  const retryCountRef = useRef<Map<string, number>>(new Map())
  const lastErrorTimeRef = useRef<Map<string, number>>(new Map())

  const handleError = useCallback(async (
    error: Error | string,
    errorContext?: string,
    additionalData?: Record<string, any>,
    recoveryOptions?: ErrorRecoveryOptions
  ) => {
    const errorObj = typeof error === 'string' ? new Error(error) : error
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const timestamp = new Date().toISOString()
    const fullContext = errorContext || context
    
    // Determine if error is recoverable
    const recoverable = !!(recoveryOptions?.retry || recoveryOptions?.fallback)
    
    // Update error state
    setErrorState({
      hasError: true,
      error: errorObj,
      message: errorObj.message,
      details: errorObj.stack,
      errorId,
      timestamp,
      context: fullContext,
      recoverable
    })

    // Log to console if enabled
    if (logToConsole) {
      const logData = {
        error: errorObj,
        context: fullContext,
        errorId,
        additionalData,
        recoveryOptions: !!recoveryOptions
      }
      
      console.group(`🚨 Error in ${fullContext}`)
      console.error('Error:', errorObj)
      console.error('Context:', fullContext)
      console.error('Error ID:', errorId)
      if (additionalData) console.error('Additional Data:', additionalData)
      console.groupEnd()
    }

    // Track error if enabled
    if (trackError) {
      // Only track if we have a valid auth token to avoid errors during initialization
      try {
        const hasAuth = localStorage.getItem('auth_token')
        if (hasAuth) {
          await trackEngagementEvent({
            type: 'error',
            data: {
              error_message: errorObj.message,
              error_stack: errorObj.stack,
              error_type: errorObj.name,
              context: fullContext,
              error_id: errorId,
              timestamp,
              additional_data: additionalData,
              recoverable,
              user_agent: navigator.userAgent,
              url: window.location.href,
              viewport: {
                width: window.innerWidth,
                height: window.innerHeight
              }
            }
          })
        }
      } catch (trackingError) {
        // Silently fail - don't log to avoid error loops
        if (process.env.NODE_ENV === 'development') {
          console.warn('Failed to track error:', trackingError)
        }
      }
    }

    // Show toast notification if enabled
    if (showToast) {
      await showErrorToast(errorObj.message, errorId)
    }

    // Report to external monitoring services
    await reportToExternalServices(errorObj, fullContext, errorId, additionalData)

    return errorId
  }, [trackError, showToast, logToConsole, context])

  const clearError = useCallback(() => {
    setErrorState({ hasError: false })
  }, [])

  const handleAsyncError = useCallback(async <T>(
    asyncOperation: () => Promise<T>,
    operationContext?: string,
    fallbackValue?: T,
    recoveryOptions?: ErrorRecoveryOptions
  ): Promise<T | undefined> => {
    const operationId = operationContext || 'async_operation'
    
    try {
      return await asyncOperation()
    } catch (error) {
      const errorId = await handleError(
        error as Error, 
        operationContext, 
        { operation: operationId },
        recoveryOptions
      )
      
      // Try recovery options
      if (recoveryOptions) {
        const recovered = await attemptRecovery(
          error as Error,
          operationId,
          recoveryOptions,
          errorId
        )
        
        if (recovered !== undefined) {
          return recovered
        }
      }
      
      return fallbackValue
    }
  }, [handleError])

  const retryOperation = useCallback(async <T>(
    operation: () => Promise<T>,
    operationContext?: string,
    maxAttempts?: number
  ): Promise<T | undefined> => {
    const attempts = maxAttempts || maxRetries
    const operationId = operationContext || 'retry_operation'
    
    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        const result = await operation()
        
        // Clear retry count on success
        retryCountRef.current.delete(operationId)
        
        // Track successful retry
        if (attempt > 1) {
          await trackEngagementEvent({
            type: 'error_recovery',
            data: {
              action: 'retry_success',
              operation: operationId,
              attempt,
              total_attempts: attempts,
              timestamp: new Date().toISOString()
            }
          }).catch(console.error)
        }
        
        return result
      } catch (error) {
        const isLastAttempt = attempt === attempts
        
        if (isLastAttempt) {
          // Final attempt failed
          await handleError(
            error as Error,
            `${operationId} (final attempt ${attempt}/${attempts})`,
            { attempt, total_attempts: attempts }
          )
          return undefined
        } else {
          // Log retry attempt
          console.warn(`Retry attempt ${attempt}/${attempts} failed for ${operationId}:`, error)
          
          // Wait before next attempt
          await new Promise(resolve => setTimeout(resolve, retryDelay * attempt))
        }
      }
    }
    
    return undefined
  }, [handleError, maxRetries, retryDelay])

  const attemptRecovery = async <T>(
    error: Error,
    operationId: string,
    recoveryOptions: ErrorRecoveryOptions,
    errorId: string
  ): Promise<T | undefined> => {
    try {
      // Try retry option first
      if (recoveryOptions.retry) {
        const currentRetries = retryCountRef.current.get(operationId) || 0
        
        if (currentRetries < maxRetries) {
          retryCountRef.current.set(operationId, currentRetries + 1)
          
          // Track retry attempt
          await trackEngagementEvent({
            type: 'error_recovery',
            data: {
              action: 'retry_attempt',
              operation: operationId,
              error_id: errorId,
              retry_count: currentRetries + 1,
              max_retries: maxRetries,
              timestamp: new Date().toISOString()
            }
          }).catch(console.error)
          
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, retryDelay))
          
          // Attempt retry
          await recoveryOptions.retry()
          return undefined // Let the operation handle the result
        }
      }
      
      // Try fallback option
      if (recoveryOptions.fallback) {
        await trackEngagementEvent({
          type: 'error_recovery',
          data: {
            action: 'fallback_used',
            operation: operationId,
            error_id: errorId,
            timestamp: new Date().toISOString()
          }
        }).catch(console.error)
        
        return recoveryOptions.fallback()
      }
      
      // Try redirect option
      if (recoveryOptions.redirect) {
        await trackEngagementEvent({
          type: 'error_recovery',
          data: {
            action: 'redirect',
            operation: operationId,
            error_id: errorId,
            redirect_url: recoveryOptions.redirect,
            timestamp: new Date().toISOString()
          }
        }).catch(console.error)
        
        window.location.href = recoveryOptions.redirect
      }
      
    } catch (recoveryError) {
      console.error('Recovery attempt failed:', recoveryError)
      await handleError(
        recoveryError as Error,
        `${operationId}_recovery`,
        { original_error: error.message, error_id: errorId }
      )
    }
    
    return undefined
  }

  return {
    errorState,
    handleError,
    clearError,
    handleAsyncError,
    retryOperation
  }
}

// Enhanced global error handler setup
export const setupGlobalErrorHandling = () => {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', async (event) => {
    console.error('Unhandled promise rejection:', event.reason)
    
    try {
      const hasAuth = localStorage.getItem('auth_token')
      if (hasAuth) {
        await trackEngagementEvent({
          type: 'error',
          data: {
            error_type: 'unhandled_promise_rejection',
            error_message: event.reason?.message || String(event.reason),
            error_stack: event.reason?.stack,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            critical: true
          }
        })
      }
    } catch (trackingError) {
      // Silently fail
      if (process.env.NODE_ENV === 'development') {
        console.warn('Failed to track unhandled promise rejection:', trackingError)
      }
    }
  })

  // Handle global JavaScript errors
  window.addEventListener('error', async (event) => {
    console.error('Global JavaScript error:', event.error)
    
    try {
      const hasAuth = localStorage.getItem('auth_token')
      if (hasAuth) {
        await trackEngagementEvent({
          type: 'error',
          data: {
            error_type: 'global_javascript_error',
            error_message: event.message,
            error_filename: event.filename,
            error_lineno: event.lineno,
            error_colno: event.colno,
            error_stack: event.error?.stack,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            critical: true
          }
        })
      }
    } catch (trackingError) {
      // Silently fail
      if (process.env.NODE_ENV === 'development') {
        console.warn('Failed to track global JavaScript error:', trackingError)
      }
    }
  })

  // Handle resource loading errors
  window.addEventListener('error', async (event) => {
    if (event.target !== window) {
      const target = event.target as HTMLElement
      
      try {
        const hasAuth = localStorage.getItem('auth_token')
        if (hasAuth) {
          await trackEngagementEvent({
            type: 'error',
            data: {
              error_type: 'resource_load_error',
              resource_type: target.tagName?.toLowerCase(),
              resource_src: (target as any).src || (target as any).href,
              url: window.location.href,
              timestamp: new Date().toISOString()
            }
          })
        }
      } catch (trackingError) {
        // Silently fail
        if (process.env.NODE_ENV === 'development') {
          console.warn('Failed to track resource load error:', trackingError)
        }
      }
    }
  }, true)
}

// Helper functions
async function showErrorToast(message: string, errorId: string) {
  try {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Error Occurred', {
        body: message,
        icon: '/favicon.ico',
        tag: errorId
      })
    } else if ('Notification' in window && Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission()
      if (permission === 'granted') {
        new Notification('Error Occurred', {
          body: message,
          icon: '/favicon.ico',
          tag: errorId
        })
      }
    }
  } catch (notificationError) {
    console.warn('Failed to show notification:', notificationError)
  }
}

async function reportToExternalServices(
  error: Error,
  context: string,
  errorId: string,
  additionalData?: Record<string, any>
) {
  try {
    // Report to Sentry if available
    if (window.Sentry) {
      window.Sentry.captureException(error, {
        tags: {
          context,
          errorId
        },
        extra: additionalData
      })
    }

    // Report to other monitoring services
    // Add integrations for LogRocket, Bugsnag, etc. as needed
    
  } catch (reportingError) {
    console.error('Failed to report error to external services:', reportingError)
  }
}

export default useErrorHandler
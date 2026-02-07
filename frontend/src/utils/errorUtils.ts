/**
 * Error utilities for Customer Onboarding Agent
 * Provides error parsing, formatting, and user-friendly message generation
 */

export interface ApiError {
  code: string
  message: string
  user_message: string
  details?: Record<string, any>
  request_id?: string
  timestamp?: string
}

export interface ParsedError {
  title: string
  message: string
  details?: string
  isRetryable: boolean
  statusCode?: number
}

/**
 * Parse API error response into user-friendly format
 */
export const parseApiError = (error: any): ParsedError => {
  // Default error response
  const defaultError: ParsedError = {
    title: 'Error',
    message: 'An unexpected error occurred. Please try again.',
    isRetryable: true
  }

  try {
    // Handle fetch/axios errors
    if (error.response) {
      const { status, data } = error.response
      
      // Handle structured API error responses
      if (data?.error) {
        const apiError: ApiError = data.error
        return {
          title: getErrorTitle(apiError.code, status),
          message: apiError.user_message || apiError.message,
          details: formatErrorDetails(apiError),
          isRetryable: isRetryableError(status, apiError.code),
          statusCode: status
        }
      }
      
      // Handle plain error responses
      if (data?.detail) {
        return {
          title: getErrorTitle('', status),
          message: getUserFriendlyMessage(status, data.detail),
          isRetryable: isRetryableError(status),
          statusCode: status
        }
      }
      
      // Handle HTTP status codes without detailed error info
      return {
        title: getErrorTitle('', status),
        message: getUserFriendlyMessage(status),
        isRetryable: isRetryableError(status),
        statusCode: status
      }
    }
    
    // Handle network errors
    if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
      return {
        title: 'Connection Error',
        message: 'Unable to connect to the server. Please check your internet connection and try again.',
        isRetryable: true
      }
    }
    
    // Handle timeout errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return {
        title: 'Request Timeout',
        message: 'The request took too long to complete. Please try again.',
        isRetryable: true
      }
    }
    
    // Handle JavaScript errors
    if (error instanceof Error) {
      return {
        title: 'Application Error',
        message: 'An error occurred in the application. Please refresh the page and try again.',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined,
        isRetryable: true
      }
    }
    
    // Handle string errors
    if (typeof error === 'string') {
      return {
        title: 'Error',
        message: error,
        isRetryable: true
      }
    }
    
    return defaultError
    
  } catch (parseError) {
    console.error('Error parsing API error:', parseError)
    return defaultError
  }
}

/**
 * Get appropriate error title based on error code and status
 */
const getErrorTitle = (errorCode: string, statusCode?: number): string => {
  // Error code specific titles
  const codeToTitle: Record<string, string> = {
    'AUTHENTICATION_ERROR': 'Authentication Required',
    'AUTHORIZATION_ERROR': 'Access Denied',
    'VALIDATION_ERROR': 'Invalid Input',
    'DOCUMENT_PROCESSING_ERROR': 'Document Processing Failed',
    'DOCUMENT_VALIDATION_ERROR': 'Invalid Document',
    'EXTERNAL_API_ERROR': 'Service Unavailable',
    'ONBOARDING_ERROR': 'Onboarding Error',
    'ENGAGEMENT_TRACKING_ERROR': 'Tracking Error',
    'DATABASE_ERROR': 'Data Error',
    'RATE_LIMIT_ERROR': 'Rate Limit Exceeded',
    'SYSTEM_HEALTH_ERROR': 'System Unavailable'
  }
  
  if (errorCode && codeToTitle[errorCode]) {
    return codeToTitle[errorCode]
  }
  
  // Status code specific titles
  const statusToTitle: Record<number, string> = {
    400: 'Bad Request',
    401: 'Authentication Required',
    403: 'Access Denied',
    404: 'Not Found',
    405: 'Method Not Allowed',
    422: 'Invalid Input',
    429: 'Rate Limit Exceeded',
    500: 'Server Error',
    502: 'Service Unavailable',
    503: 'Service Unavailable',
    504: 'Request Timeout'
  }
  
  if (statusCode && statusToTitle[statusCode]) {
    return statusToTitle[statusCode]
  }
  
  return 'Error'
}

/**
 * Get user-friendly error message based on status code
 */
const getUserFriendlyMessage = (statusCode: number, detail?: string): string => {
  const statusMessages: Record<number, string> = {
    400: 'The request was invalid. Please check your input and try again.',
    401: 'Please log in to access this feature.',
    403: 'You don\'t have permission to perform this action.',
    404: 'The requested resource was not found.',
    405: 'This action is not allowed.',
    422: 'The provided data is invalid. Please check your input.',
    429: 'Too many requests. Please wait a moment and try again.',
    500: 'A server error occurred. Please try again later.',
    502: 'The service is temporarily unavailable. Please try again later.',
    503: 'The service is temporarily unavailable. Please try again later.',
    504: 'The request timed out. Please try again.'
  }
  
  // Use detail if it's user-friendly, otherwise use generic message
  if (detail && isUserFriendlyMessage(detail)) {
    return detail
  }
  
  return statusMessages[statusCode] || 'An unexpected error occurred. Please try again.'
}

/**
 * Check if an error message is user-friendly (not technical)
 */
const isUserFriendlyMessage = (message: string): boolean => {
  const technicalTerms = [
    'exception', 'traceback', 'stack trace', 'null pointer',
    'undefined', 'syntax error', 'type error', 'reference error',
    'internal server error', 'database', 'sql', 'connection',
    'timeout', 'http', 'api', 'json', 'xml'
  ]
  
  const lowerMessage = message.toLowerCase()
  return !technicalTerms.some(term => lowerMessage.includes(term))
}

/**
 * Determine if an error is retryable
 */
const isRetryableError = (statusCode?: number, errorCode?: string): boolean => {
  // Non-retryable status codes
  const nonRetryableStatuses = [400, 401, 403, 404, 405, 422]
  if (statusCode && nonRetryableStatuses.includes(statusCode)) {
    return false
  }
  
  // Non-retryable error codes
  const nonRetryableErrorCodes = [
    'AUTHENTICATION_ERROR',
    'AUTHORIZATION_ERROR',
    'VALIDATION_ERROR',
    'DOCUMENT_VALIDATION_ERROR'
  ]
  if (errorCode && nonRetryableErrorCodes.includes(errorCode)) {
    return false
  }
  
  return true
}

/**
 * Format error details for display
 */
const formatErrorDetails = (apiError: ApiError): string | undefined => {
  if (!apiError.details) {
    return undefined
  }
  
  try {
    // Format validation errors
    if (apiError.code === 'VALIDATION_ERROR' && apiError.details.validation_errors) {
      const validationErrors = apiError.details.validation_errors
      return validationErrors
        .map((err: any) => `${err.field}: ${err.message}`)
        .join('\n')
    }
    
    // Format other details
    return JSON.stringify(apiError.details, null, 2)
  } catch (error) {
    return undefined
  }
}

/**
 * Create error message for display components
 */
export const createErrorMessage = (error: any) => {
  const parsed = parseApiError(error)
  return {
    title: parsed.title,
    message: parsed.message,
    details: parsed.details,
    canRetry: parsed.isRetryable
  }
}

/**
 * Log error for debugging (development only)
 */
export const logError = (error: any, context?: string) => {
  if (process.env.NODE_ENV === 'development') {
    console.group(`🚨 Error ${context ? `in ${context}` : ''}`)
    console.error('Original error:', error)
    console.error('Parsed error:', parseApiError(error))
    console.groupEnd()
  }
}

/**
 * Check if error indicates authentication failure
 */
export const isAuthError = (error: any): boolean => {
  const parsed = parseApiError(error)
  return parsed.statusCode === 401 || 
         (error.response?.data?.error?.code === 'AUTHENTICATION_ERROR')
}

/**
 * Check if error indicates authorization failure
 */
export const isAuthorizationError = (error: any): boolean => {
  const parsed = parseApiError(error)
  return parsed.statusCode === 403 || 
         (error.response?.data?.error?.code === 'AUTHORIZATION_ERROR')
}

/**
 * Extract request ID from error for support purposes
 */
export const getRequestId = (error: any): string | undefined => {
  return error.response?.data?.error?.request_id ||
         error.response?.headers?.['x-request-id']
}
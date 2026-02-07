/**
 * Test suite for error handling utilities
 */

import { parseApiError, createErrorMessage, isAuthError, isAuthorizationError } from '../utils/errorUtils'

describe('Error Handling Utils', () => {
  describe('parseApiError', () => {
    it('should parse structured API error responses', () => {
      const apiError = {
        response: {
          status: 422,
          data: {
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Request validation failed',
              user_message: 'Please check your input',
              details: { field: 'email', issue: 'invalid format' }
            }
          }
        }
      }

      const parsed = parseApiError(apiError)
      
      expect(parsed.title).toBe('Invalid Input')
      expect(parsed.message).toBe('Please check your input')
      expect(parsed.statusCode).toBe(422)
      expect(parsed.isRetryable).toBe(false)
    })

    it('should handle network errors', () => {
      const networkError = {
        code: 'NETWORK_ERROR',
        message: 'Network Error'
      }

      const parsed = parseApiError(networkError)
      
      expect(parsed.title).toBe('Connection Error')
      expect(parsed.message).toContain('Unable to connect')
      expect(parsed.isRetryable).toBe(true)
    })

    it('should handle timeout errors', () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      }

      const parsed = parseApiError(timeoutError)
      
      expect(parsed.title).toBe('Request Timeout')
      expect(parsed.message).toContain('took too long')
      expect(parsed.isRetryable).toBe(true)
    })

    it('should handle JavaScript errors', () => {
      const jsError = new Error('Something went wrong')

      const parsed = parseApiError(jsError)
      
      expect(parsed.title).toBe('Application Error')
      expect(parsed.message).toContain('error occurred in the application')
      expect(parsed.isRetryable).toBe(true)
    })

    it('should handle HTTP status codes without detailed error info', () => {
      const httpError = {
        response: {
          status: 500,
          data: {
            detail: 'Internal server error'
          }
        }
      }

      const parsed = parseApiError(httpError)
      
      expect(parsed.title).toBe('Server Error')
      expect(parsed.statusCode).toBe(500)
      expect(parsed.isRetryable).toBe(true)
    })
  })

  describe('createErrorMessage', () => {
    it('should create error message from API error', () => {
      const apiError = {
        response: {
          status: 401,
          data: {
            error: {
              code: 'AUTHENTICATION_ERROR',
              message: 'Token expired',
              user_message: 'Please log in again'
            }
          }
        }
      }

      const errorMessage = createErrorMessage(apiError)
      
      expect(errorMessage.title).toBe('Authentication Required')
      expect(errorMessage.message).toBe('Please log in again')
      expect(errorMessage.canRetry).toBe(false)
    })
  })

  describe('isAuthError', () => {
    it('should identify authentication errors', () => {
      const authError = {
        response: {
          status: 401,
          data: {
            error: {
              code: 'AUTHENTICATION_ERROR'
            }
          }
        }
      }

      expect(isAuthError(authError)).toBe(true)
    })

    it('should not identify non-auth errors as auth errors', () => {
      const validationError = {
        response: {
          status: 422,
          data: {
            error: {
              code: 'VALIDATION_ERROR'
            }
          }
        }
      }

      expect(isAuthError(validationError)).toBe(false)
    })
  })

  describe('isAuthorizationError', () => {
    it('should identify authorization errors', () => {
      const authzError = {
        response: {
          status: 403,
          data: {
            error: {
              code: 'AUTHORIZATION_ERROR'
            }
          }
        }
      }

      expect(isAuthorizationError(authzError)).toBe(true)
    })

    it('should not identify non-authz errors as authz errors', () => {
      const authError = {
        response: {
          status: 401,
          data: {
            error: {
              code: 'AUTHENTICATION_ERROR'
            }
          }
        }
      }

      expect(isAuthorizationError(authError)).toBe(false)
    })
  })

  describe('Error categorization', () => {
    it('should correctly identify retryable errors', () => {
      const retryableErrors = [
        { response: { status: 500 } }, // Server error
        { response: { status: 502 } }, // Bad gateway
        { response: { status: 503 } }, // Service unavailable
        { response: { status: 429 } }, // Rate limit
        { code: 'NETWORK_ERROR' },     // Network error
        { code: 'ECONNABORTED' }       // Timeout
      ]

      retryableErrors.forEach(error => {
        const parsed = parseApiError(error)
        expect(parsed.isRetryable).toBe(true)
      })
    })

    it('should correctly identify non-retryable errors', () => {
      const nonRetryableErrors = [
        { response: { status: 400 } }, // Bad request
        { response: { status: 401 } }, // Unauthorized
        { response: { status: 403 } }, // Forbidden
        { response: { status: 404 } }, // Not found
        { response: { status: 422 } }  // Validation error
      ]

      nonRetryableErrors.forEach(error => {
        const parsed = parseApiError(error)
        expect(parsed.isRetryable).toBe(false)
      })
    })
  })
})
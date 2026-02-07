import React, { Component, ErrorInfo, ReactNode } from 'react'
import { trackEngagementEvent } from '../services/engagementService'
import './ErrorBoundary.css'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  level?: 'page' | 'component' | 'critical'
  componentName?: string
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
  errorId?: string
  retryCount: number
  lastErrorTime?: number
}

class ErrorBoundary extends Component<Props, State> {
  private maxRetries = 3
  private retryDelay = 1000 // 1 second

  constructor(props: Props) {
    super(props)
    this.state = { 
      hasError: false,
      retryCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      lastErrorTime: Date.now()
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to engagement tracking and monitoring
    this.logError(error, errorInfo)
    
    // Update state with error info
    this.setState({
      error,
      errorInfo
    })

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Report to external error tracking service if available
    this.reportToExternalService(error, errorInfo)
  }

  private logError = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      const errorLevel = this.props.level || 'component'
      const componentName = this.props.componentName || 'Unknown'

      // Only track if user is authenticated to avoid initialization errors
      const hasAuth = localStorage.getItem('auth_token')
      if (hasAuth) {
        // Track error as engagement event
        await trackEngagementEvent({
          type: 'error',
          data: {
            error_message: error.message,
            error_stack: error.stack,
            component_stack: errorInfo.componentStack,
            error_boundary: true,
            error_level: errorLevel,
            component_name: componentName,
            retry_count: this.state.retryCount,
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent,
            url: window.location.href
          }
        })
      }

      // Also log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.group('🚨 Error Boundary caught an error')
        console.error('Error:', error)
        console.error('Error Info:', errorInfo)
        console.error('Component:', componentName)
        console.error('Level:', errorLevel)
        console.groupEnd()
      }
    } catch (trackingError) {
      // Silently fail to avoid error loops
      if (process.env.NODE_ENV === 'development') {
        console.warn('Failed to track error:', trackingError)
      }
    }
  }

  private reportToExternalService = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      // Report to external monitoring service (e.g., Sentry, LogRocket, etc.)
      if (window.Sentry) {
        window.Sentry.captureException(error, {
          contexts: {
            react: {
              componentStack: errorInfo.componentStack
            }
          },
          tags: {
            errorBoundary: true,
            level: this.props.level || 'component',
            component: this.props.componentName || 'Unknown'
          }
        })
      }
    } catch (reportingError) {
      console.error('Failed to report error to external service:', reportingError)
    }
  }

  private handleRetry = () => {
    const now = Date.now()
    const timeSinceLastError = now - (this.state.lastErrorTime || 0)
    
    // Reset retry count if enough time has passed
    if (timeSinceLastError > 30000) { // 30 seconds
      this.setState({ 
        hasError: false, 
        error: undefined, 
        errorInfo: undefined,
        retryCount: 0
      })
      return
    }

    // Check if we've exceeded max retries
    if (this.state.retryCount >= this.maxRetries) {
      this.handleReload()
      return
    }

    // Increment retry count and try again
    this.setState(prevState => ({ 
      hasError: false, 
      error: undefined, 
      errorInfo: undefined,
      retryCount: prevState.retryCount + 1
    }))
  }

  private handleReload = () => {
    // Track reload action only if authenticated
    const hasAuth = localStorage.getItem('auth_token')
    if (hasAuth) {
      trackEngagementEvent({
        type: 'error_recovery',
        data: {
          action: 'page_reload',
          error_id: this.state.errorId,
          retry_count: this.state.retryCount,
          timestamp: new Date().toISOString()
        }
      }).catch(() => {
        // Silently fail
      })
    }

    // Reload the page
    window.location.reload()
  }

  private handleReportIssue = () => {
    // Track issue reporting only if authenticated
    const hasAuth = localStorage.getItem('auth_token')
    if (hasAuth) {
      trackEngagementEvent({
        type: 'error_recovery',
        data: {
          action: 'report_issue',
          error_id: this.state.errorId,
          timestamp: new Date().toISOString()
        }
      }).catch(() => {
        // Silently fail
      })
    }

    // Open support/feedback form or email
    const subject = encodeURIComponent(`Error Report: ${this.state.error?.message || 'Unknown Error'}`)
    const body = encodeURIComponent(`
Error ID: ${this.state.errorId}
Component: ${this.props.componentName || 'Unknown'}
Level: ${this.props.level || 'component'}
Time: ${new Date().toISOString()}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}

Error Details:
${this.state.error?.message || 'No error message'}

Please describe what you were doing when this error occurred:
[Your description here]
    `)
    
    window.open(`mailto:support@example.com?subject=${subject}&body=${body}`)
  }

  private getErrorSeverityInfo = () => {
    const level = this.props.level || 'component'
    
    switch (level) {
      case 'critical':
        return {
          icon: '🔥',
          title: 'Critical Error',
          description: 'A critical error has occurred that affects core functionality.',
          priority: 'high'
        }
      case 'page':
        return {
          icon: '⚠️',
          title: 'Page Error',
          description: 'This page encountered an error and cannot be displayed properly.',
          priority: 'medium'
        }
      case 'component':
      default:
        return {
          icon: '⚠️',
          title: 'Component Error',
          description: 'A component on this page encountered an error.',
          priority: 'low'
        }
    }
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      const severityInfo = this.getErrorSeverityInfo()
      const canRetry = this.state.retryCount < this.maxRetries

      // Default error UI with enhanced information
      return (
        <div className={`error-boundary error-boundary--${this.props.level || 'component'}`}>
          <div className="error-boundary-content">
            <div className="error-icon">{severityInfo.icon}</div>
            <h2>{severityInfo.title}</h2>
            <p className="error-description">
              {severityInfo.description}
            </p>
            
            {this.state.retryCount > 0 && (
              <p className="retry-info">
                Retry attempt {this.state.retryCount} of {this.maxRetries}
              </p>
            )}
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-details">
                <summary>Error Details (Development Only)</summary>
                <div className="error-info">
                  <h4>Component:</h4>
                  <pre>{this.props.componentName || 'Unknown'}</pre>
                  
                  <h4>Error Message:</h4>
                  <pre>{this.state.error.message}</pre>
                  
                  {this.state.error.stack && (
                    <>
                      <h4>Stack Trace:</h4>
                      <pre>{this.state.error.stack}</pre>
                    </>
                  )}
                  
                  {this.state.errorInfo?.componentStack && (
                    <>
                      <h4>Component Stack:</h4>
                      <pre>{this.state.errorInfo.componentStack}</pre>
                    </>
                  )}
                </div>
              </details>
            )}
            
            <div className="error-actions">
              {canRetry && (
                <button 
                  onClick={this.handleRetry}
                  className="btn btn-primary"
                >
                  Try Again {this.state.retryCount > 0 && `(${this.maxRetries - this.state.retryCount} left)`}
                </button>
              )}
              
              <button 
                onClick={this.handleReload}
                className="btn btn-secondary"
              >
                Reload Page
              </button>
              
              <button 
                onClick={this.handleReportIssue}
                className="btn btn-outline"
              >
                Report Issue
              </button>
            </div>
            
            {this.state.errorId && (
              <div className="error-metadata">
                <p className="error-id">Error ID: {this.state.errorId}</p>
                <p className="error-time">
                  Time: {new Date().toLocaleString()}
                </p>
              </div>
            )}
            
            {!canRetry && (
              <div className="error-help">
                <p>If this problem persists:</p>
                <ul>
                  <li>Try clearing your browser cache</li>
                  <li>Disable browser extensions temporarily</li>
                  <li>Contact support with the Error ID above</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
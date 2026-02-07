import React from 'react'

interface ErrorMessageProps {
  title?: string
  message: string
  details?: string
  onRetry?: () => void
  onDismiss?: () => void
  type?: 'error' | 'warning' | 'info'
  className?: string
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'Error',
  message,
  details,
  onRetry,
  onDismiss,
  type = 'error',
  className = ''
}) => {
  const getIcon = () => {
    switch (type) {
      case 'warning':
        return '⚠️'
      case 'info':
        return 'ℹ️'
      default:
        return '❌'
    }
  }

  const getTypeClass = () => {
    switch (type) {
      case 'warning':
        return 'error-message-warning'
      case 'info':
        return 'error-message-info'
      default:
        return 'error-message-error'
    }
  }

  return (
    <div className={`error-message ${getTypeClass()} ${className}`}>
      <div className="error-message-content">
        <div className="error-message-header">
          <span className="error-message-icon">{getIcon()}</span>
          <h4 className="error-message-title">{title}</h4>
          {onDismiss && (
            <button 
              onClick={onDismiss}
              className="error-message-close"
              aria-label="Dismiss"
            >
              ×
            </button>
          )}
        </div>
        
        <p className="error-message-text">{message}</p>
        
        {details && (
          <details className="error-message-details">
            <summary>More details</summary>
            <pre className="error-message-details-text">{details}</pre>
          </details>
        )}
        
        {onRetry && (
          <div className="error-message-actions">
            <button 
              onClick={onRetry}
              className="btn btn-sm btn-primary"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ErrorMessage
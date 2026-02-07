/**
 * Test for Enhanced Error Boundary Component
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import ErrorBoundary from '../components/ErrorBoundary'

// Mock the engagement service
jest.mock('../services/engagementService', () => ({
  trackEngagementEvent: jest.fn().mockResolvedValue(undefined)
}))

// Component that throws an error for testing
const ThrowError: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow = false }) => {
  if (shouldThrow) {
    throw new Error('Test error for ErrorBoundary')
  }
  return <div>No error</div>
}

describe('Enhanced ErrorBoundary', () => {
  // Suppress console.error for these tests
  const originalError = console.error
  beforeAll(() => {
    console.error = jest.fn()
  })
  
  afterAll(() => {
    console.error = originalError
  })

  test('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('No error')).toBeInTheDocument()
  })

  test('renders error UI when there is an error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Component Error')).toBeInTheDocument()
    expect(screen.getByText(/A component on this page encountered an error/)).toBeInTheDocument()
  })

  test('renders custom fallback when provided', () => {
    const customFallback = <div>Custom error message</div>
    
    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Custom error message')).toBeInTheDocument()
  })

  test('shows different error levels correctly', () => {
    render(
      <ErrorBoundary level="critical" componentName="TestComponent">
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Critical Error')).toBeInTheDocument()
    expect(screen.getByText(/A critical error has occurred/)).toBeInTheDocument()
  })

  test('shows retry button and handles retry', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    const retryButton = screen.getByText(/Try Again/)
    expect(retryButton).toBeInTheDocument()
    
    // Click retry button
    fireEvent.click(retryButton)
    
    // After retry, should show the component again (without error this time)
    expect(screen.getByText('No error')).toBeInTheDocument()
  })

  test('shows error metadata in development mode', () => {
    // Mock development environment
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'development'
    
    render(
      <ErrorBoundary componentName="TestComponent">
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Error Details (Development Only)')).toBeInTheDocument()
    
    // Restore environment
    process.env.NODE_ENV = originalEnv
  })

  test('shows report issue button', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText('Report Issue')).toBeInTheDocument()
  })

  test('shows error ID and timestamp', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(screen.getByText(/Error ID:/)).toBeInTheDocument()
    expect(screen.getByText(/Time:/)).toBeInTheDocument()
  })

  test('handles retry limit correctly', () => {
    const TestComponent = () => {
      const [shouldThrow, setShouldThrow] = React.useState(true)
      
      return (
        <ErrorBoundary>
          <div>
            <button onClick={() => setShouldThrow(!shouldThrow)}>
              Toggle Error
            </button>
            <ThrowError shouldThrow={shouldThrow} />
          </div>
        </ErrorBoundary>
      )
    }
    
    render(<TestComponent />)
    
    // Should show error initially
    expect(screen.getByText('Component Error')).toBeInTheDocument()
    
    // Try multiple retries
    for (let i = 0; i < 4; i++) {
      const retryButton = screen.queryByText(/Try Again/)
      if (retryButton) {
        fireEvent.click(retryButton)
      }
    }
    
    // After max retries, should show reload button instead
    expect(screen.getByText('Reload Page')).toBeInTheDocument()
  })

  test('calls custom error handler when provided', () => {
    const mockErrorHandler = jest.fn()
    
    render(
      <ErrorBoundary onError={mockErrorHandler}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )
    
    expect(mockErrorHandler).toHaveBeenCalled()
    expect(mockErrorHandler).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String)
      })
    )
  })
})

// Test the enhanced error handler hook
describe('Enhanced Error Handler Hook', () => {
  test('error handler hook is available', () => {
    // This is a basic test to ensure the hook can be imported
    const useErrorHandler = require('../hooks/useErrorHandler').default
    expect(typeof useErrorHandler).toBe('function')
  })
})
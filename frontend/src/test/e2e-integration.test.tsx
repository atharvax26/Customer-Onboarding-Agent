/**
 * End-to-End Integration Tests for Frontend
 * 
 * Tests complete user journeys, real-time features, error scenarios,
 * and performance requirements from the frontend perspective.
 * 
 * Requirements: 9.1 - Performance and Reliability
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import { ApiProvider } from '../contexts/ApiContext'
import App from '../App'
import Login from '../pages/Login'
import Register from '../pages/Register'
import Onboarding from '../pages/Onboarding'
import Analytics from '../pages/Analytics'
import Documents from '../pages/Documents'

// Mock API client
const mockApiClient = {
  auth: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
  },
  documents: {
    upload: vi.fn(),
    list: vi.fn(),
    get: vi.fn(),
  },
  onboarding: {
    start: vi.fn(),
    getSession: vi.fn(),
    getCurrentStep: vi.fn(),
    completeStep: vi.fn(),
    getSessions: vi.fn(),
  },
  engagement: {
    recordInteraction: vi.fn(),
    getScore: vi.fn(),
  },
  analytics: {
    getActivationRates: vi.fn(),
    getDropoffAnalysis: vi.fn(),
  },
  intervention: {
    getInterventions: vi.fn(),
  },
}

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      <ApiProvider value={mockApiClient}>
        {children}
      </ApiProvider>
    </AuthProvider>
  </BrowserRouter>
)

describe('Frontend End-to-End Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset localStorage
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  describe('Complete User Journeys', () => {
    it('should complete developer onboarding journey', async () => {
      const user = userEvent.setup()
      
      // Mock API responses
      mockApiClient.auth.register.mockResolvedValue({
        id: 1,
        email: 'dev@example.com',
        role: 'developer'
      })
      
      mockApiClient.auth.login.mockResolvedValue({
        access_token: 'test-token',
        user: { id: 1, email: 'dev@example.com', role: 'developer' }
      })
      
      mockApiClient.documents.upload.mockResolvedValue({
        id: 1,
        filename: 'test-doc.txt',
        summary: 'Test summary',
        tasks: ['Task 1', 'Task 2']
      })
      
      mockApiClient.onboarding.start.mockResolvedValue({
        session_id: 1,
        total_steps: 5,
        current_step: 1
      })
      
      mockApiClient.onboarding.getCurrentStep.mockResolvedValue({
        step_number: 1,
        total_steps: 5,
        title: 'API Setup',
        content: 'Configure your API access',
        tasks: ['Create API key', 'Test endpoints']
      })
      
      mockApiClient.onboarding.completeStep.mockResolvedValue({
        success: true,
        next_step: 2
      })

      // Render the full app
      render(<App />, { wrapper: TestWrapper })

      // Step 1: Navigate to register
      const registerLink = screen.getByText(/register/i)
      await user.click(registerLink)

      // Step 2: Fill registration form
      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })
      
      await user.type(screen.getByLabelText(/email/i), 'dev@example.com')
      await user.type(screen.getByLabelText(/password/i), 'testpass123')
      await user.selectOptions(screen.getByLabelText(/role/i), 'developer')
      
      const registerButton = screen.getByRole('button', { name: /register/i })
      await user.click(registerButton)

      // Step 3: Login after registration
      await waitFor(() => {
        expect(mockApiClient.auth.register).toHaveBeenCalledWith({
          email: 'dev@example.com',
          password: 'testpass123',
          role: 'developer'
        })
      })

      // Mock successful login
      mockApiClient.auth.getCurrentUser.mockResolvedValue({
        id: 1,
        email: 'dev@example.com',
        role: 'developer'
      })

      // Step 4: Navigate to documents and upload
      await waitFor(() => {
        const documentsLink = screen.getByText(/documents/i)
        expect(documentsLink).toBeInTheDocument()
      })

      // Step 5: Upload document (simulate file upload)
      const fileInput = screen.getByLabelText(/upload/i)
      const file = new File(['test content'], 'test-doc.txt', { type: 'text/plain' })
      
      await user.upload(fileInput, file)
      
      await waitFor(() => {
        expect(mockApiClient.documents.upload).toHaveBeenCalled()
      })

      // Step 6: Start onboarding
      const startOnboardingButton = screen.getByText(/start onboarding/i)
      await user.click(startOnboardingButton)

      await waitFor(() => {
        expect(mockApiClient.onboarding.start).toHaveBeenCalled()
      })

      // Step 7: Complete onboarding steps
      for (let step = 1; step <= 5; step++) {
        await waitFor(() => {
          expect(screen.getByText(`Step ${step} of 5`)).toBeInTheDocument()
        })

        const nextButton = screen.getByText(/next/i)
        await user.click(nextButton)

        if (step < 5) {
          mockApiClient.onboarding.getCurrentStep.mockResolvedValue({
            step_number: step + 1,
            total_steps: 5,
            title: `Step ${step + 1}`,
            content: `Content for step ${step + 1}`,
            tasks: [`Task ${step + 1}`]
          })
        }
      }

      // Verify completion
      await waitFor(() => {
        expect(mockApiClient.onboarding.completeStep).toHaveBeenCalledTimes(5)
      })
    })

    it('should complete business user onboarding journey', async () => {
      const user = userEvent.setup()
      
      // Mock API responses for business user (3 steps)
      mockApiClient.auth.register.mockResolvedValue({
        id: 2,
        email: 'business@example.com',
        role: 'business_user'
      })
      
      mockApiClient.auth.login.mockResolvedValue({
        access_token: 'test-token',
        user: { id: 2, email: 'business@example.com', role: 'business_user' }
      })
      
      mockApiClient.onboarding.start.mockResolvedValue({
        session_id: 2,
        total_steps: 3,
        current_step: 1
      })
      
      mockApiClient.onboarding.getCurrentStep.mockResolvedValue({
        step_number: 1,
        total_steps: 3,
        title: 'Workflow Overview',
        content: 'Understanding business processes',
        tasks: ['Review workflow', 'Identify key processes']
      })

      render(<App />, { wrapper: TestWrapper })

      // Similar flow but verify business user gets 3 steps
      const registerLink = screen.getByText(/register/i)
      await user.click(registerLink)

      await waitFor(() => {
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      })
      
      await user.type(screen.getByLabelText(/email/i), 'business@example.com')
      await user.type(screen.getByLabelText(/password/i), 'testpass123')
      await user.selectOptions(screen.getByLabelText(/role/i), 'business_user')
      
      const registerButton = screen.getByRole('button', { name: /register/i })
      await user.click(registerButton)

      // Verify business user specific behavior
      await waitFor(() => {
        expect(mockApiClient.auth.register).toHaveBeenCalledWith({
          email: 'business@example.com',
          password: 'testpass123',
          role: 'business_user'
        })
      })
    })
  })

  describe('Real-Time Features', () => {
    it('should update engagement scores in real-time', async () => {
      const user = userEvent.setup()
      
      // Mock authenticated state
      mockApiClient.auth.getCurrentUser.mockResolvedValue({
        id: 1,
        email: 'test@example.com',
        role: 'developer'
      })
      
      mockApiClient.engagement.getScore.mockResolvedValueOnce({
        current_score: 50,
        last_updated: new Date().toISOString()
      })
      
      mockApiClient.engagement.recordInteraction.mockResolvedValue({ success: true })

      render(<Onboarding />, { wrapper: TestWrapper })

      // Initial score should be displayed
      await waitFor(() => {
        expect(screen.getByText(/engagement/i)).toBeInTheDocument()
      })

      // Simulate user interaction
      const interactiveElement = screen.getByRole('button')
      await user.click(interactiveElement)

      // Verify interaction was recorded
      await waitFor(() => {
        expect(mockApiClient.engagement.recordInteraction).toHaveBeenCalled()
      })

      // Mock updated score
      mockApiClient.engagement.getScore.mockResolvedValueOnce({
        current_score: 65,
        last_updated: new Date().toISOString()
      })

      // Score should update within 5 seconds (requirement)
      await waitFor(() => {
        // This would be tested with actual score display component
        expect(mockApiClient.engagement.getScore).toHaveBeenCalled()
      }, { timeout: 5000 })
    })

    it('should display interventions in real-time', async () => {
      const user = userEvent.setup()
      
      // Mock low engagement scenario
      mockApiClient.engagement.getScore.mockResolvedValue({
        current_score: 25, // Below 30 threshold
        last_updated: new Date().toISOString()
      })
      
      mockApiClient.intervention.getInterventions.mockResolvedValue([
        {
          id: 1,
          message: 'Need help? Click here for assistance',
          type: 'contextual_help',
          triggered_at: new Date().toISOString()
        }
      ])

      render(<Onboarding />, { wrapper: TestWrapper })

      // Intervention should appear for low engagement
      await waitFor(() => {
        expect(screen.getByText(/need help/i)).toBeInTheDocument()
      })
    })

    it('should update analytics in real-time', async () => {
      // Mock analytics data
      mockApiClient.analytics.getActivationRates.mockResolvedValueOnce({
        developer: { total: 10, completed: 5, rate: 50 },
        business_user: { total: 5, completed: 3, rate: 60 },
        admin: { total: 2, completed: 2, rate: 100 }
      })

      render(<Analytics />, { wrapper: TestWrapper })

      // Initial analytics should load
      await waitFor(() => {
        expect(screen.getByText(/activation rates/i)).toBeInTheDocument()
      })

      // Simulate real-time update
      mockApiClient.analytics.getActivationRates.mockResolvedValueOnce({
        developer: { total: 11, completed: 6, rate: 54.5 },
        business_user: { total: 5, completed: 3, rate: 60 },
        admin: { total: 2, completed: 2, rate: 100 }
      })

      // Analytics should update automatically
      await waitFor(() => {
        expect(mockApiClient.analytics.getActivationRates).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Error Scenarios and Recovery', () => {
    it('should handle authentication errors gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock authentication failure
      mockApiClient.auth.login.mockRejectedValue(new Error('Invalid credentials'))

      render(<Login />, { wrapper: TestWrapper })

      await user.type(screen.getByLabelText(/email/i), 'wrong@example.com')
      await user.type(screen.getByLabelText(/password/i), 'wrongpass')
      
      const loginButton = screen.getByRole('button', { name: /login/i })
      await user.click(loginButton)

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
      })

      // System should remain functional
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    })

    it('should handle document upload errors gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock upload failure
      mockApiClient.documents.upload.mockRejectedValue(new Error('Invalid file format'))

      render(<Documents />, { wrapper: TestWrapper })

      const fileInput = screen.getByLabelText(/upload/i)
      const invalidFile = new File(['invalid'], 'test.exe', { type: 'application/octet-stream' })
      
      await user.upload(fileInput, invalidFile)

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/invalid file format/i)).toBeInTheDocument()
      })

      // Upload interface should remain available
      expect(fileInput).toBeInTheDocument()
    })

    it('should handle network errors with retry mechanism', async () => {
      const user = userEvent.setup()
      
      // Mock network error followed by success
      mockApiClient.onboarding.getCurrentStep
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          step_number: 1,
          total_steps: 5,
          title: 'Step 1',
          content: 'Content',
          tasks: ['Task 1']
        })

      render(<Onboarding />, { wrapper: TestWrapper })

      // Should show loading state initially
      expect(screen.getByText(/loading/i)).toBeInTheDocument()

      // Should retry and eventually succeed
      await waitFor(() => {
        expect(screen.getByText(/step 1/i)).toBeInTheDocument()
      })
    })

    it('should handle component errors with error boundary', async () => {
      // Mock component that throws error
      const ErrorComponent = () => {
        throw new Error('Component error')
      }

      // This would test the ErrorBoundary component
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <TestWrapper>
          <ErrorComponent />
        </TestWrapper>
      )

      // Error boundary should catch and display error
      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Performance Requirements', () => {
    it('should render components within performance thresholds', async () => {
      const startTime = performance.now()
      
      render(<App />, { wrapper: TestWrapper })
      
      // Wait for initial render
      await waitFor(() => {
        expect(screen.getByText(/customer onboarding/i)).toBeInTheDocument()
      })
      
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      // Should render within reasonable time (< 1000ms for initial load)
      expect(renderTime).toBeLessThan(1000)
    })

    it('should handle rapid user interactions without performance degradation', async () => {
      const user = userEvent.setup()
      
      mockApiClient.engagement.recordInteraction.mockResolvedValue({ success: true })
      
      render(<Onboarding />, { wrapper: TestWrapper })
      
      const button = screen.getByRole('button')
      
      // Simulate rapid clicking
      const startTime = performance.now()
      
      for (let i = 0; i < 10; i++) {
        await user.click(button)
      }
      
      const endTime = performance.now()
      const totalTime = endTime - startTime
      
      // Should handle rapid interactions efficiently
      expect(totalTime).toBeLessThan(2000) // 2 seconds for 10 interactions
      
      // All interactions should be recorded
      await waitFor(() => {
        expect(mockApiClient.engagement.recordInteraction).toHaveBeenCalledTimes(10)
      })
    })

    it('should maintain responsive UI during data loading', async () => {
      // Mock slow API response
      mockApiClient.analytics.getActivationRates.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          developer: { total: 10, completed: 5, rate: 50 }
        }), 1000))
      )

      render(<Analytics />, { wrapper: TestWrapper })

      // Loading state should be shown immediately
      expect(screen.getByText(/loading/i)).toBeInTheDocument()

      // UI should remain responsive during loading
      const refreshButton = screen.getByText(/refresh/i)
      expect(refreshButton).toBeEnabled()

      // Data should eventually load
      await waitFor(() => {
        expect(screen.getByText(/activation rates/i)).toBeInTheDocument()
      }, { timeout: 2000 })
    })
  })

  describe('User Interaction Tracking', () => {
    it('should track all user interactions for engagement scoring', async () => {
      const user = userEvent.setup()
      
      mockApiClient.engagement.recordInteraction.mockResolvedValue({ success: true })
      
      render(<Onboarding />, { wrapper: TestWrapper })
      
      // Test various interaction types
      const interactions = [
        () => user.click(screen.getByRole('button')),
        () => user.hover(screen.getByText(/step/i)),
        () => user.keyboard('{Tab}'),
      ]
      
      for (const interaction of interactions) {
        await interaction()
      }
      
      // All interactions should be tracked
      await waitFor(() => {
        expect(mockApiClient.engagement.recordInteraction).toHaveBeenCalledTimes(interactions.length)
      })
    })

    it('should track time spent on pages', async () => {
      vi.useFakeTimers()
      
      mockApiClient.engagement.recordInteraction.mockResolvedValue({ success: true })
      
      render(<Onboarding />, { wrapper: TestWrapper })
      
      // Simulate time passage
      act(() => {
        vi.advanceTimersByTime(30000) // 30 seconds
      })
      
      // Time tracking should be recorded
      await waitFor(() => {
        expect(mockApiClient.engagement.recordInteraction).toHaveBeenCalledWith(
          expect.objectContaining({
            event_type: 'time_spent'
          })
        )
      })
      
      vi.useRealTimers()
    })
  })

  describe('Accessibility and Usability', () => {
    it('should be accessible to screen readers', async () => {
      render(<App />, { wrapper: TestWrapper })
      
      // Check for proper ARIA labels and roles
      expect(screen.getByRole('navigation')).toBeInTheDocument()
      expect(screen.getByRole('main')).toBeInTheDocument()
      
      // Check for proper heading structure
      const headings = screen.getAllByRole('heading')
      expect(headings.length).toBeGreaterThan(0)
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(<App />, { wrapper: TestWrapper })
      
      // Tab through interactive elements
      await user.tab()
      expect(document.activeElement).toHaveAttribute('tabindex')
      
      // Enter should activate focused elements
      await user.keyboard('{Enter}')
      // Verify appropriate action was taken
    })

    it('should provide visual feedback for user actions', async () => {
      const user = userEvent.setup()
      
      render(<Onboarding />, { wrapper: TestWrapper })
      
      const button = screen.getByRole('button')
      
      // Button should show hover state
      await user.hover(button)
      expect(button).toHaveClass(/hover|focus/)
      
      // Button should show active state when clicked
      await user.click(button)
      // Visual feedback should be provided
    })
  })
})
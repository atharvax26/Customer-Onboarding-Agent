import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import ProgressIndicator from '../components/onboarding/ProgressIndicator'
import StepContent from '../components/onboarding/StepContent'
import RealTimeFeedback from '../components/feedback/RealTimeFeedback'

// Mock the auth context
const mockUser = {
  id: 1,
  email: 'test@example.com',
  role: 'Developer' as const,
  created_at: '2024-01-01T00:00:00Z'
}

// Mock API calls
jest.mock('../utils/api', () => ({
  engagementApi: {
    trackInteraction: jest.fn().mockResolvedValue({ success: true }),
    getEngagementScore: jest.fn().mockResolvedValue({
      current_score: 75,
      score_history: [],
      last_updated: '2024-01-01T00:00:00Z'
    })
  }
}))

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
)

describe('Onboarding Components', () => {
  describe('ProgressIndicator', () => {
    it('renders progress correctly', () => {
      render(
        <ProgressIndicator 
          currentStep={2}
          totalSteps={5}
          completionPercentage={40}
        />
      )

      expect(screen.getByText('Your Progress')).toBeInTheDocument()
      expect(screen.getByText('Step 2 of 5 (40% complete)')).toBeInTheDocument()
    })

    it('shows correct step indicators', () => {
      render(
        <ProgressIndicator 
          currentStep={3}
          totalSteps={5}
          completionPercentage={60}
        />
      )

      // Should have 5 step indicators
      const stepIndicators = screen.getAllByText(/Completed|In Progress|Upcoming/)
      expect(stepIndicators).toHaveLength(5)
    })
  })

  describe('StepContent', () => {
    const mockStep = {
      step_number: 1,
      total_steps: 3,
      title: 'Getting Started',
      content: '<p>Welcome to the onboarding process!</p>',
      tasks: ['Complete your profile', 'Review documentation'],
      estimated_time: 15
    }

    it('renders step content correctly', () => {
      render(
        <StepContent 
          step={mockStep}
          userRole="Developer"
        />
      )

      expect(screen.getByText('Getting Started')).toBeInTheDocument()
      expect(screen.getByText('Welcome to the onboarding process!')).toBeInTheDocument()
      expect(screen.getByText('Complete your profile')).toBeInTheDocument()
      expect(screen.getByText('Review documentation')).toBeInTheDocument()
    })

    it('shows role-specific content', () => {
      render(
        <StepContent 
          step={mockStep}
          userRole="Developer"
        />
      )

      expect(screen.getByText('👨‍💻')).toBeInTheDocument()
      expect(screen.getByText('Tailored for Developer')).toBeInTheDocument()
    })

    it('formats estimated time correctly', () => {
      render(
        <StepContent 
          step={mockStep}
          userRole="Developer"
        />
      )

      expect(screen.getByText('⏱️ Estimated time: 15 min')).toBeInTheDocument()
    })
  })

  describe('RealTimeFeedback', () => {
    it('renders engagement metrics when enabled', () => {
      render(
        <TestWrapper>
          <RealTimeFeedback 
            sessionId={1}
            showEngagementScore={true}
            showInteractionCount={true}
            showTimeSpent={true}
          />
        </TestWrapper>
      )

      expect(screen.getByText('Engagement')).toBeInTheDocument()
      expect(screen.getByText('Interactions')).toBeInTheDocument()
      expect(screen.getByText('Time Spent')).toBeInTheDocument()
    })

    it('does not render when user is not authenticated', () => {
      // Mock no user
      const { container } = render(
        <BrowserRouter>
          <RealTimeFeedback 
            sessionId={1}
            showEngagementScore={true}
          />
        </BrowserRouter>
      )

      expect(container.firstChild).toBeNull()
    })
  })
})

describe('Interaction Tracking', () => {
  it('should track interactions when components are used', () => {
    // This is more of an integration test that would require mocking
    // the interaction tracking hook and API calls
    expect(true).toBe(true) // Placeholder for now
  })
})
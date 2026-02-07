import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import HelpMessage from '../components/intervention/HelpMessage'
import InterventionSystem from '../components/intervention/InterventionSystem'
import { HelpMessage as HelpMessageType, InterventionFeedback } from '../types/intervention'

// Mock the hooks and API
vi.mock('../hooks/useInteractionTracking', () => ({
  useInteractionTracking: () => ({
    trackButtonClick: vi.fn(),
    trackCustomEvent: vi.fn()
  })
}))

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 1, role: 'Developer' }
  })
}))

vi.mock('../utils/api', () => ({
  interventionApi: {
    checkForIntervention: vi.fn(),
    triggerManualHelp: vi.fn(),
    submitFeedback: vi.fn(),
    getInterventionHistory: vi.fn()
  },
  engagementApi: {
    getEngagementScore: vi.fn()
  }
}))

describe('HelpMessage Component', () => {
  const mockHelpMessage: HelpMessageType = {
    message_id: 'test-message-1',
    content: 'This is a test help message to assist you with the current step.',
    message_type: 'contextual_help',
    context: {
      step_number: 2,
      step_title: 'Making Your First API Call',
      user_role: 'Developer',
      engagement_score: 25
    },
    dismissible: true
  }

  const mockOnDismiss = vi.fn()
  const mockOnFeedback = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders help message with correct content', () => {
    render(
      <HelpMessage
        helpMessage={mockHelpMessage}
        onDismiss={mockOnDismiss}
        sessionId={123}
      />
    )

    expect(screen.getByText('Need a hand?')).toBeInTheDocument()
    expect(screen.getByText(mockHelpMessage.content)).toBeInTheDocument()
    expect(screen.getByText('Step 2: Making Your First API Call')).toBeInTheDocument()
  })

  it('shows correct icon for contextual help', () => {
    render(
      <HelpMessage
        helpMessage={mockHelpMessage}
        onDismiss={mockOnDismiss}
        sessionId={123}
      />
    )

    expect(screen.getByText('💡')).toBeInTheDocument()
  })

  it('calls onDismiss when dismiss button is clicked', () => {
    render(
      <HelpMessage
        helpMessage={mockHelpMessage}
        onDismiss={mockOnDismiss}
        sessionId={123}
      />
    )

    const dismissButton = screen.getByLabelText('Dismiss help message')
    fireEvent.click(dismissButton)

    expect(mockOnDismiss).toHaveBeenCalledWith(mockHelpMessage.message_id)
  })

  it('shows feedback options when intervention ID is provided', () => {
    render(
      <HelpMessage
        helpMessage={mockHelpMessage}
        onDismiss={mockOnDismiss}
        onFeedback={mockOnFeedback}
        interventionId={456}
        sessionId={123}
      />
    )

    const feedbackToggle = screen.getByText('Was this helpful?')
    fireEvent.click(feedbackToggle)

    expect(screen.getByText('👍 Yes')).toBeInTheDocument()
    expect(screen.getByText('👎 No')).toBeInTheDocument()
  })

  it('submits positive feedback correctly', async () => {
    render(
      <HelpMessage
        helpMessage={mockHelpMessage}
        onDismiss={mockOnDismiss}
        onFeedback={mockOnFeedback}
        interventionId={456}
        sessionId={123}
      />
    )

    // Open feedback options
    const feedbackToggle = screen.getByText('Was this helpful?')
    fireEvent.click(feedbackToggle)

    // Click yes
    const yesButton = screen.getByText('👍 Yes')
    fireEvent.click(yesButton)

    expect(mockOnFeedback).toHaveBeenCalledWith({
      intervention_id: 456,
      was_helpful: true
    })

    await waitFor(() => {
      expect(screen.getByText('✓ Thank you for your feedback!')).toBeInTheDocument()
    })
  })

  it('submits negative feedback correctly', async () => {
    render(
      <HelpMessage
        helpMessage={mockHelpMessage}
        onDismiss={mockOnDismiss}
        onFeedback={mockOnFeedback}
        interventionId={456}
        sessionId={123}
      />
    )

    // Open feedback options
    const feedbackToggle = screen.getByText('Was this helpful?')
    fireEvent.click(feedbackToggle)

    // Click no
    const noButton = screen.getByText('👎 No')
    fireEvent.click(noButton)

    expect(mockOnFeedback).toHaveBeenCalledWith({
      intervention_id: 456,
      was_helpful: false
    })

    await waitFor(() => {
      expect(screen.getByText('✓ Thank you for your feedback!')).toBeInTheDocument()
    })
  })

  it('handles different message types with appropriate styling', () => {
    const lowEngagementMessage: HelpMessageType = {
      ...mockHelpMessage,
      message_type: 'low_engagement_help'
    }

    const { container } = render(
      <HelpMessage
        helpMessage={lowEngagementMessage}
        onDismiss={mockOnDismiss}
        sessionId={123}
      />
    )

    expect(container.querySelector('.help-message--low-engagement-help')).toBeInTheDocument()
    expect(screen.getByText('🤝')).toBeInTheDocument()
  })

  it('does not show dismiss button when not dismissible', () => {
    const nonDismissibleMessage: HelpMessageType = {
      ...mockHelpMessage,
      dismissible: false
    }

    render(
      <HelpMessage
        helpMessage={nonDismissibleMessage}
        onDismiss={mockOnDismiss}
        sessionId={123}
      />
    )

    expect(screen.queryByLabelText('Dismiss help message')).not.toBeInTheDocument()
  })
})

describe('InterventionSystem Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing when enabled', () => {
    render(
      <InterventionSystem
        sessionId={123}
        currentStep={2}
        engagementScore={25}
        enabled={true}
      />
    )

    // Component should render but be empty initially
    expect(document.querySelector('.intervention-system')).toBeInTheDocument()
  })

  it('does not render when disabled', () => {
    render(
      <InterventionSystem
        sessionId={123}
        currentStep={2}
        engagementScore={25}
        enabled={false}
      />
    )

    expect(document.querySelector('.intervention-system')).not.toBeInTheDocument()
  })

  it('does not render when no session ID provided', () => {
    render(
      <InterventionSystem
        currentStep={2}
        engagementScore={25}
        enabled={true}
      />
    )

    expect(document.querySelector('.intervention-system')).not.toBeInTheDocument()
  })
})
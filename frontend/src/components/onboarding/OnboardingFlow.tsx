import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useInteractionTracking } from '../../hooks/useInteractionTracking'
import ProgressIndicator from './ProgressIndicator'
import StepContent from './StepContent'
import StepNavigation from './StepNavigation'
import RealTimeFeedback from '../feedback/RealTimeFeedback'
import InteractionTracker from '../tracking/InteractionTracker'
import { OnboardingSession, OnboardingStep, OnboardingProgress } from '../../types/onboarding'
import { onboardingApi } from '../../utils/api'
import './OnboardingFlow.css'

interface OnboardingFlowProps {
  documentId: number
}

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ documentId }) => {
  const { user } = useAuth()
  const [session, setSession] = useState<OnboardingSession | null>(null)
  const [currentStep, setCurrentStep] = useState<OnboardingStep | null>(null)
  const [progress, setProgress] = useState<OnboardingProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const stepStartTime = useRef<number>(Date.now())

  // Initialize interaction tracking for this onboarding session
  const { 
    trackCustomEvent, 
    trackButtonClick, 
    trackStepAdvance, 
    trackStepComplete 
  } = useInteractionTracking({ 
    sessionId: session?.id,
    enableClickTracking: true,
    enableScrollTracking: true,
    enableTimeTracking: true,
    enableFocusTracking: true
  })

  // Initialize onboarding session
  useEffect(() => {
    const initializeOnboarding = async () => {
      if (!user) return

      try {
        setLoading(true)
        setError(null)

        // Start new onboarding session
        const newSession = await onboardingApi.startOnboarding(documentId)
        setSession(newSession)

        // Track onboarding start
        trackCustomEvent('onboarding_started', {
          document_id: documentId,
          user_role: user.role,
          session_id: newSession.id
        })

        // Get current step
        const step = await onboardingApi.getCurrentStep(newSession.id)
        setCurrentStep(step)
        stepStartTime.current = Date.now()

        // Track step start
        trackCustomEvent('step_started', {
          step_number: step.step_number,
          step_title: step.title,
          session_id: newSession.id
        })

        // Get progress
        const progressData = await onboardingApi.getProgress(newSession.id)
        setProgress(progressData)

      } catch (err) {
        console.error('Failed to initialize onboarding:', err)
        setError('Failed to start onboarding session. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    initializeOnboarding()
  }, [documentId, user])

  const handleStepComplete = async () => {
    if (!session || !currentStep) return

    try {
      setLoading(true)
      
      // Calculate time spent on current step
      const timeSpent = Date.now() - stepStartTime.current
      
      // Track step completion
      trackStepComplete(currentStep.step_number, timeSpent)
      
      // Advance to next step
      await onboardingApi.advanceStep(session.id)
      
      // Track step advance
      if (currentStep.step_number < currentStep.total_steps) {
        trackStepAdvance(currentStep.step_number, currentStep.step_number + 1)
      }
      
      // Get updated step and progress
      const [updatedStep, updatedProgress] = await Promise.all([
        onboardingApi.getCurrentStep(session.id),
        onboardingApi.getProgress(session.id)
      ])
      
      setCurrentStep(updatedStep)
      setProgress(updatedProgress)
      
      // Reset step timer for new step
      stepStartTime.current = Date.now()
      
      // Track new step start if not completed
      if (updatedProgress.completion_percentage < 100) {
        trackCustomEvent('step_started', {
          step_number: updatedStep.step_number,
          step_title: updatedStep.title,
          session_id: session.id
        })
      }

      // Check if onboarding is complete
      if (updatedProgress.completion_percentage >= 100) {
        trackCustomEvent('onboarding_completed', {
          session_id: session.id,
          total_time: Date.now() - stepStartTime.current,
          user_role: user?.role
        })
        console.log('Onboarding completed!')
      }

    } catch (err) {
      console.error('Failed to advance step:', err)
      setError('Failed to advance to next step. Please try again.')
      
      // Track error
      trackCustomEvent('step_advance_error', {
        step_number: currentStep.step_number,
        error: err instanceof Error ? err.message : 'Unknown error',
        session_id: session.id
      })
    } finally {
      setLoading(false)
    }
  }

  const handleStepBack = async () => {
    // Note: Backend doesn't support going back, but we can track the attempt
    trackButtonClick('back-button', 'Back')
    trackCustomEvent('back_button_clicked', {
      step_number: currentStep?.step_number,
      session_id: session?.id
    })
    
    // Show a message
    alert('Going back is not supported in this onboarding flow.')
  }

  if (loading && !currentStep) {
    return (
      <div className="onboarding-flow loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading your personalized onboarding...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="onboarding-flow error">
        <div className="error-message">
          <h3>Oops! Something went wrong</h3>
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="retry-button"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!session || !currentStep || !progress) {
    return (
      <div className="onboarding-flow error">
        <div className="error-message">
          <h3>Unable to load onboarding</h3>
          <p>Please refresh the page and try again.</p>
        </div>
      </div>
    )
  }

  const isLastStep = currentStep.step_number === currentStep.total_steps
  const isFirstStep = currentStep.step_number === 1

  return (
    <div className="onboarding-flow">
      {/* Real-time feedback component */}
      <RealTimeFeedback 
        sessionId={session?.id}
        showEngagementScore={true}
        showInteractionCount={true}
        showTimeSpent={true}
      />

      <div className="onboarding-header">
        <InteractionTracker 
          trackClicks={true}
          eventPrefix="header"
          sessionId={session?.id}
          additionalData={{ step_number: currentStep?.step_number }}
        >
          <h1>Welcome to Your Onboarding Journey</h1>
        </InteractionTracker>
        <p className="role-indicator">
          Customized for: <span className="role-badge">{user?.role}</span>
        </p>
      </div>

      <ProgressIndicator 
        currentStep={currentStep.step_number}
        totalSteps={currentStep.total_steps}
        completionPercentage={progress.completion_percentage}
      />

      <div className="onboarding-content">
        <StepContent 
          step={currentStep}
          userRole={user?.role || 'Developer'}
        />
      </div>

      <StepNavigation
        isFirstStep={isFirstStep}
        isLastStep={isLastStep}
        loading={loading}
        onBack={handleStepBack}
        onNext={handleStepComplete}
        onComplete={handleStepComplete}
        sessionId={session?.id}
      />

      {progress.completion_percentage >= 100 && (
        <div className="completion-celebration">
          <div className="celebration-content">
            <h2>🎉 Congratulations!</h2>
            <p>You've successfully completed your onboarding!</p>
            <InteractionTracker 
              trackClicks={true}
              eventPrefix="completion"
              sessionId={session?.id}
            >
              <button 
                onClick={() => {
                  trackButtonClick('continue-to-dashboard', 'Continue to Dashboard')
                  window.location.href = '/'
                }}
                className="continue-button"
              >
                Continue to Dashboard
              </button>
            </InteractionTracker>
          </div>
        </div>
      )}
    </div>
  )
}

export default OnboardingFlow
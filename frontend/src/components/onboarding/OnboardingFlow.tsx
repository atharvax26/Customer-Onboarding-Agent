import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useInteractionTracking } from '../../hooks/useInteractionTracking'
import { useOnboarding, useEngagement } from '../../hooks/useApiClient'
import ProgressIndicator from './ProgressIndicator'
import StepContent from './StepContent'
import StepNavigation from './StepNavigation'
import RealTimeFeedback from '../feedback/RealTimeFeedback'
import InteractionTracker from '../tracking/InteractionTracker'
import InterventionSystem from '../intervention/InterventionSystem'
import { OnboardingSession, OnboardingStep, OnboardingProgress } from '../../types/onboarding'
import './OnboardingFlow.css'

interface OnboardingFlowProps {
  documentId: number
}

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ documentId }) => {
  const { user } = useAuth()
  const { start, getCurrentStep, advanceStep, getProgress, getUserSessions, handleError } = useOnboarding()
  const { getScore } = useEngagement()
  const [session, setSession] = useState<OnboardingSession | null>(null)
  const [currentStep, setCurrentStep] = useState<OnboardingStep | null>(null)
  const [progress, setProgress] = useState<OnboardingProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [engagementScore, setEngagementScore] = useState<number | undefined>(undefined)
  const [stepHistory, setStepHistory] = useState<OnboardingStep[]>([])
  const [viewingHistoryIndex, setViewingHistoryIndex] = useState<number | null>(null)
  const [isStepComplete, setIsStepComplete] = useState(false)
  const stepStartTime = useRef<number>(Date.now())

  // Reset completion state when step changes
  useEffect(() => {
    setIsStepComplete(false)
  }, [currentStep?.step_number])

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

  // Fetch engagement score periodically
  useEffect(() => {
    if (!user || !session) return

    const fetchEngagementScore = async () => {
      try {
        const scoreData = await getScore()
        setEngagementScore(scoreData.current_score)
      } catch (error) {
        console.error('Error fetching engagement score:', error)
      }
    }

    // Initial fetch
    fetchEngagementScore()

    // Set up periodic fetching every 10 seconds
    const intervalId = setInterval(fetchEngagementScore, 10000)

    return () => clearInterval(intervalId)
  }, [user, session, getScore])

  // Initialize onboarding session
  useEffect(() => {
    const initializeOnboarding = async () => {
      if (!user) return

      try {
        setLoading(true)
        setError(null)

        // Check if user already has an active session for this document
        const existingSessions = await getUserSessions()
        const activeSession = existingSessions.find(
          (s: any) => s.document_id === documentId && s.status === 'active'
        )

        let sessionToUse
        if (activeSession) {
          // Reuse existing active session
          console.log('Reusing existing session:', activeSession.id)
          sessionToUse = activeSession
        } else {
          // Start new onboarding session only if no active session exists
          console.log('Creating new session for document:', documentId)
          sessionToUse = await start(documentId)
        }
        
        setSession(sessionToUse)

        // Track onboarding start only for new sessions
        if (!activeSession) {
          trackCustomEvent('onboarding_started', {
            document_id: documentId,
            user_role: user.role,
            session_id: sessionToUse.id
          })
        }

        // Get current step
        const step = await getCurrentStep(sessionToUse.id)
        setCurrentStep(step)
        setStepHistory([step]) // Initialize history with first step
        setViewingHistoryIndex(null) // Not viewing history
        stepStartTime.current = Date.now()

        // Track step start only for new sessions
        if (!activeSession) {
          trackCustomEvent('step_started', {
            step_number: step.step_number,
            step_title: step.title,
            session_id: sessionToUse.id
          })
        }

        // Get progress
        const progressData = await getProgress(sessionToUse.id)
        setProgress(progressData)

      } catch (err) {
        console.error('Failed to initialize onboarding:', err)
        setError(handleError(err))
      } finally {
        setLoading(false)
      }
    }

    initializeOnboarding()
  }, [documentId, user, start, getCurrentStep, getProgress, getUserSessions, handleError, trackCustomEvent])

  const handleStepComplete = async () => {
    if (!session || !currentStep) return

    // If viewing history, just move forward in history
    if (viewingHistoryIndex !== null && viewingHistoryIndex < stepHistory.length - 1) {
      const nextStep = stepHistory[viewingHistoryIndex + 1]
      setCurrentStep(nextStep)
      setViewingHistoryIndex(viewingHistoryIndex + 1)
      return
    }

    // If at current step, advance to next step
    try {
      setLoading(true)
      
      // Calculate time spent on current step
      const timeSpent = Date.now() - stepStartTime.current
      
      // Track step completion
      trackStepComplete(currentStep.step_number, timeSpent)
      
      // Advance to next step
      await advanceStep(session.id)
      
      // Track step advance
      if (currentStep.step_number < currentStep.total_steps) {
        trackStepAdvance(currentStep.step_number, currentStep.step_number + 1)
      }
      
      // Get updated step and progress
      const [updatedStep, updatedProgress] = await Promise.all([
        getCurrentStep(session.id),
        getProgress(session.id)
      ])
      
      setCurrentStep(updatedStep)
      setProgress(updatedProgress)
      
      // Add new step to history if not already there
      setStepHistory(prev => {
        const exists = prev.some(s => s.step_number === updatedStep.step_number)
        if (!exists) {
          return [...prev, updatedStep]
        }
        return prev
      })
      setViewingHistoryIndex(null) // Reset to current view
      
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
      setError(handleError(err))
      
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
    if (!session || !currentStep) return
    
    // Check if we can go back
    if (currentStep.step_number <= 1) {
      // Already at first step
      trackCustomEvent('back_button_clicked', {
        step_number: currentStep.step_number,
        session_id: session.id,
        result: 'already_at_first_step'
      })
      return
    }

    // Track back button click
    trackButtonClick('back-button', 'Back')
    trackCustomEvent('back_button_clicked', {
      step_number: currentStep.step_number,
      session_id: session.id,
      result: 'viewing_previous_step'
    })
    
    // Find the previous step in history
    const currentIndex = viewingHistoryIndex !== null 
      ? viewingHistoryIndex 
      : stepHistory.findIndex(s => s.step_number === currentStep.step_number)
    
    if (currentIndex > 0) {
      // Show previous step from history
      const previousStep = stepHistory[currentIndex - 1]
      setCurrentStep(previousStep)
      setViewingHistoryIndex(currentIndex - 1)
    }
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
  const isViewingHistory = viewingHistoryIndex !== null
  const isAtCurrentStep = !isViewingHistory || viewingHistoryIndex === stepHistory.length - 1

  return (
    <div className="onboarding-flow">
      {/* Intervention System - monitors engagement and shows help messages */}
      <InterventionSystem
        sessionId={session?.id}
        currentStep={currentStep?.step_number}
        engagementScore={engagementScore}
        enabled={true}
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

      {isViewingHistory && !isAtCurrentStep && (
        <div className="history-banner">
          <span className="history-icon">👁️</span>
          <span className="history-text">
            You're viewing a previous step. Click "Next" to return to your current progress.
          </span>
        </div>
      )}

      <ProgressIndicator 
        currentStep={currentStep.step_number}
        totalSteps={currentStep.total_steps}
        completionPercentage={progress.completion_percentage}
      />

      <div className="onboarding-content">
        <StepContent 
          step={currentStep}
          userRole={user?.role || 'Developer'}
          onCompletionChange={setIsStepComplete}
        />
      </div>

      <StepNavigation
        isFirstStep={isFirstStep}
        isLastStep={isLastStep}
        loading={loading}
        isStepComplete={isStepComplete}
        onBack={handleStepBack}
        onNext={handleStepComplete}
        onComplete={handleStepComplete}
        sessionId={session?.id}
        currentStep={currentStep?.step_number}
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
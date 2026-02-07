import React from 'react'
import { useNavigate } from 'react-router-dom'
import InteractionTracker from '../tracking/InteractionTracker'
import './StepNavigation.css'

interface StepNavigationProps {
  isFirstStep: boolean
  isLastStep: boolean
  loading: boolean
  isStepComplete: boolean
  onBack: () => void
  onNext: () => void
  onComplete: () => void
  sessionId?: number
  currentStep?: number // Used for tracking
}

const StepNavigation: React.FC<StepNavigationProps> = ({
  isFirstStep,
  isLastStep,
  loading,
  isStepComplete,
  onBack,
  onNext,
  onComplete,
  sessionId,
  currentStep
}) => {
  const navigate = useNavigate()

  const handleContactUs = () => {
    navigate('/contact')
  }

  return (
    <div className="step-navigation">
      <div className="nav-buttons">
        <InteractionTracker 
          trackClicks={true}
          trackHovers={true}
          eventPrefix="navigation"
          sessionId={sessionId}
          additionalData={{ button_type: 'back', disabled: isFirstStep || loading }}
        >
          <button
            className="nav-button back-button"
            onClick={onBack}
            disabled={isFirstStep || loading}
          >
            <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Back
          </button>
        </InteractionTracker>

        {loading && (
          <div className="nav-center">
            <div className="nav-loading">
              <div className="nav-spinner"></div>
              <span>Processing...</span>
            </div>
          </div>
        )}

        {isLastStep ? (
          <InteractionTracker 
            trackClicks={true}
            trackHovers={true}
            eventPrefix="navigation"
            sessionId={sessionId}
            additionalData={{ button_type: 'complete', disabled: loading || !isStepComplete }}
          >
            <button
              className="nav-button complete-button"
              onClick={onComplete}
              disabled={loading || !isStepComplete}
              title={!isStepComplete ? 'Complete all tasks to finish onboarding' : 'Complete onboarding'}
            >
              {loading ? (
                <>
                  <div className="button-spinner"></div>
                  Completing...
                </>
              ) : (
                <>
                  Complete Onboarding
                  <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </>
              )}
            </button>
          </InteractionTracker>
        ) : (
          <InteractionTracker 
            trackClicks={true}
            trackHovers={true}
            eventPrefix="navigation"
            sessionId={sessionId}
            additionalData={{ button_type: 'next', disabled: loading || !isStepComplete }}
          >
            <button
              className="nav-button next-button"
              onClick={onNext}
              disabled={loading || !isStepComplete}
              title={!isStepComplete ? 'Complete all tasks to continue' : 'Continue to next step'}
            >
              {loading ? (
                <>
                  <div className="button-spinner"></div>
                  Processing...
                </>
              ) : (
                <>
                  Continue
                  <svg className="nav-icon" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </>
              )}
            </button>
          </InteractionTracker>
        )}
      </div>

      <div className="nav-help">
        {!isStepComplete && (
          <div className="completion-reminder">
            <span className="reminder-icon">✓</span>
            <span className="reminder-text">Complete all tasks above to continue</span>
          </div>
        )}
        <div className="help-actions">
          <InteractionTracker 
            trackClicks={true}
            eventPrefix="help"
            sessionId={sessionId}
          >
            <button 
              className="help-link contact-support-btn"
              onClick={handleContactUs}
            >
              <svg className="contact-icon" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
              </svg>
              Contact Us
            </button>
          </InteractionTracker>
        </div>
      </div>
    </div>
  )
}

export default StepNavigation
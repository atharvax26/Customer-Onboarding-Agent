import React from 'react'
import InteractionTracker from '../tracking/InteractionTracker'
import './StepNavigation.css'

interface StepNavigationProps {
  isFirstStep: boolean
  isLastStep: boolean
  loading: boolean
  onBack: () => void
  onNext: () => void
  onComplete: () => void
  sessionId?: number
}

const StepNavigation: React.FC<StepNavigationProps> = ({
  isFirstStep,
  isLastStep,
  loading,
  onBack,
  onNext,
  onComplete,
  sessionId
}) => {
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

        <div className="nav-center">
          {loading && (
            <div className="nav-loading">
              <div className="nav-spinner"></div>
              <span>Processing...</span>
            </div>
          )}
        </div>

        {isLastStep ? (
          <InteractionTracker 
            trackClicks={true}
            trackHovers={true}
            eventPrefix="navigation"
            sessionId={sessionId}
            additionalData={{ button_type: 'complete', disabled: loading }}
          >
            <button
              className="nav-button complete-button"
              onClick={onComplete}
              disabled={loading}
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
            additionalData={{ button_type: 'next', disabled: loading }}
          >
            <button
              className="nav-button next-button"
              onClick={onNext}
              disabled={loading}
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
        <p className="help-text">
          Need help? 
          <InteractionTracker 
            trackClicks={true}
            eventPrefix="help"
            sessionId={sessionId}
          >
            <button className="help-link">Contact Support</button>
          </InteractionTracker>
        </p>
      </div>
    </div>
  )
}

export default StepNavigation
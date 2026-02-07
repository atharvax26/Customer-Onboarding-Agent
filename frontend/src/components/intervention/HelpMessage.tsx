import React, { useState } from 'react'
import { HelpMessage as HelpMessageType, InterventionFeedback } from '../../types/intervention'
import { useInteractionTracking } from '../../hooks/useInteractionTracking'
import './HelpMessage.css'

interface HelpMessageProps {
  helpMessage: HelpMessageType
  onDismiss: (messageId: string) => void
  onFeedback?: (feedback: InterventionFeedback) => void
  interventionId?: number
  sessionId?: number
}

const HelpMessage: React.FC<HelpMessageProps> = ({
  helpMessage,
  onDismiss,
  onFeedback,
  interventionId,
  sessionId
}) => {
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  const { trackButtonClick, trackCustomEvent } = useInteractionTracking({
    sessionId,
    enableClickTracking: true
  })

  const handleDismiss = () => {
    trackButtonClick('help-dismiss', 'Dismiss Help Message')
    trackCustomEvent('help_message_dismissed', {
      message_id: helpMessage.message_id,
      message_type: helpMessage.message_type,
      context: helpMessage.context
    })
    onDismiss(helpMessage.message_id)
  }

  const handleFeedback = (wasHelpful: boolean) => {
    if (!interventionId || !onFeedback) return

    const feedback: InterventionFeedback = {
      intervention_id: interventionId,
      was_helpful: wasHelpful
    }

    onFeedback(feedback)
    setFeedbackSubmitted(true)

    trackButtonClick(
      wasHelpful ? 'help-feedback-yes' : 'help-feedback-no',
      wasHelpful ? 'Help was useful' : 'Help was not useful'
    )
    
    trackCustomEvent('help_feedback_submitted', {
      message_id: helpMessage.message_id,
      was_helpful: wasHelpful,
      intervention_id: interventionId
    })

    // Auto-dismiss after feedback
    setTimeout(() => {
      handleDismiss()
    }, 2000)
  }

  const getMessageIcon = () => {
    switch (helpMessage.message_type) {
      case 'contextual_help':
        return '💡'
      case 'low_engagement_help':
        return '🤝'
      case 'generic_help':
        return 'ℹ️'
      default:
        return '❓'
    }
  }

  const getMessageClass = () => {
    const baseClass = 'help-message'
    const typeClass = `help-message--${helpMessage.message_type.replace('_', '-')}`
    return `${baseClass} ${typeClass}`
  }

  return (
    <div className={getMessageClass()}>
      <div className="help-message__header">
        <div className="help-message__icon">
          {getMessageIcon()}
        </div>
        <div className="help-message__title">
          Need a hand?
        </div>
        {helpMessage.dismissible && (
          <button
            className="help-message__close"
            onClick={handleDismiss}
            aria-label="Dismiss help message"
          >
            ×
          </button>
        )}
      </div>

      <div className="help-message__content">
        <p>{helpMessage.content}</p>
        
        {helpMessage.context.step_title && (
          <div className="help-message__context">
            <small>
              Step {helpMessage.context.step_number}: {helpMessage.context.step_title}
            </small>
          </div>
        )}
      </div>

      {!feedbackSubmitted && interventionId && onFeedback && (
        <div className="help-message__actions">
          {!showFeedback ? (
            <button
              className="help-message__feedback-toggle"
              onClick={() => {
                setShowFeedback(true)
                trackCustomEvent('help_feedback_opened', {
                  message_id: helpMessage.message_id
                })
              }}
            >
              Was this helpful?
            </button>
          ) : (
            <div className="help-message__feedback">
              <span className="help-message__feedback-label">Was this helpful?</span>
              <div className="help-message__feedback-buttons">
                <button
                  className="help-message__feedback-button help-message__feedback-button--yes"
                  onClick={() => handleFeedback(true)}
                >
                  👍 Yes
                </button>
                <button
                  className="help-message__feedback-button help-message__feedback-button--no"
                  onClick={() => handleFeedback(false)}
                >
                  👎 No
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {feedbackSubmitted && (
        <div className="help-message__feedback-success">
          <span>✓ Thank you for your feedback!</span>
        </div>
      )}
    </div>
  )
}

export default HelpMessage
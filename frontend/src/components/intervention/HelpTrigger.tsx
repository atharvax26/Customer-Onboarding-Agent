import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { useInteractionTracking } from '../../hooks/useInteractionTracking'
import { interventionApi } from '../../utils/api'
import './HelpTrigger.css'

interface HelpTriggerProps {
  sessionId?: number
  currentStep?: number
  className?: string
}

const HelpTrigger: React.FC<HelpTriggerProps> = ({
  sessionId,
  currentStep,
  className = ''
}) => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const { trackButtonClick, trackCustomEvent } = useInteractionTracking({
    sessionId,
    enableClickTracking: true
  })

  const handleTriggerHelp = async () => {
    if (!sessionId || !currentStep) {
      setMessage('No active onboarding session found')
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      await interventionApi.triggerManualHelp(sessionId, currentStep)
      
      trackButtonClick('manual-help-trigger', 'Request Help')
      trackCustomEvent('manual_help_requested', {
        session_id: sessionId,
        step_number: currentStep,
        user_role: user?.role
      })

      setMessage('Help message triggered! Check for assistance above.')
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000)
      
    } catch (error) {
      console.error('Error triggering help:', error)
      setMessage('Failed to request help. Please try again.')
      
      // Clear error message after 5 seconds
      setTimeout(() => setMessage(null), 5000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`help-trigger ${className}`}>
      <button
        onClick={handleTriggerHelp}
        disabled={loading || !sessionId}
        className="help-trigger__button"
        title="Request contextual help for the current step"
      >
        {loading ? (
          <>
            <span className="help-trigger__spinner">⏳</span>
            Requesting help...
          </>
        ) : (
          <>
            <span className="help-trigger__icon">🆘</span>
            Need Help?
          </>
        )}
      </button>
      
      {message && (
        <div className={`help-trigger__message ${message.includes('Failed') ? 'help-trigger__message--error' : 'help-trigger__message--success'}`}>
          {message}
        </div>
      )}
    </div>
  )
}

export default HelpTrigger
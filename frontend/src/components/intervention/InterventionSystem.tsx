import React, { useState, useEffect, useCallback } from 'react'
import { HelpMessage as HelpMessageType, HelpMessageResponse, InterventionFeedback } from '../../types/intervention'
import { useAuth } from '../../contexts/AuthContext'
import { useInteractionTracking } from '../../hooks/useInteractionTracking'
import HelpMessage from './HelpMessage'
import { interventionApi } from '../../utils/api'
import './InterventionSystem.css'

interface InterventionSystemProps {
  sessionId?: number
  currentStep?: number
  engagementScore?: number
  enabled?: boolean
}

const InterventionSystem: React.FC<InterventionSystemProps> = ({
  sessionId,
  currentStep,
  engagementScore,
  enabled = true
}) => {
  const { user } = useAuth()
  const [activeHelpMessages, setActiveHelpMessages] = useState<Map<string, HelpMessageResponse>>(new Map())
  const [isMonitoring, setIsMonitoring] = useState(false)
  const [lastInterventionCheck, setLastInterventionCheck] = useState<number>(0)

  const { trackCustomEvent } = useInteractionTracking({
    sessionId,
    enableClickTracking: true
  })

  // Check for interventions periodically
  const checkForInterventions = useCallback(async () => {
    if (!enabled || !user || !sessionId) return

    try {
      // Only check every 30 seconds to avoid spam
      const now = Date.now()
      if (now - lastInterventionCheck < 30000) return

      setLastInterventionCheck(now)

      // Check if user needs intervention
      const response = await interventionApi.checkForIntervention(sessionId)
      
      if (response.help_message) {
        const messageId = response.help_message.message_id
        
        // Only show if we don't already have this message
        if (!activeHelpMessages.has(messageId)) {
          setActiveHelpMessages(prev => new Map(prev.set(messageId, response)))
          
          trackCustomEvent('intervention_triggered', {
            message_id: messageId,
            message_type: response.help_message.message_type,
            engagement_score: engagementScore,
            step_number: currentStep,
            triggered_at: response.triggered_at
          })
        }
      }
    } catch (error) {
      console.error('Error checking for interventions:', error)
    }
  }, [enabled, user, sessionId, lastInterventionCheck, activeHelpMessages, engagementScore, currentStep, trackCustomEvent])

  // Start monitoring when component mounts and conditions are met
  useEffect(() => {
    if (!enabled || !sessionId || isMonitoring) return

    setIsMonitoring(true)
    
    // Initial check
    checkForInterventions()
    
    // Set up periodic checking
    const intervalId = setInterval(checkForInterventions, 30000) // Check every 30 seconds
    
    return () => {
      clearInterval(intervalId)
      setIsMonitoring(false)
    }
  }, [enabled, sessionId, checkForInterventions, isMonitoring])

  // Check for interventions when engagement score changes significantly
  useEffect(() => {
    if (engagementScore !== undefined && engagementScore < 30) {
      // Trigger immediate check for low engagement
      setTimeout(checkForInterventions, 1000)
    }
  }, [engagementScore, checkForInterventions])

  const handleDismissMessage = useCallback(async (messageId: string) => {
    setActiveHelpMessages(prev => {
      const newMap = new Map(prev)
      newMap.delete(messageId)
      return newMap
    })

    trackCustomEvent('help_message_dismissed', {
      message_id: messageId,
      session_id: sessionId
    })
  }, [sessionId, trackCustomEvent])

  const handleFeedback = useCallback(async (feedback: InterventionFeedback) => {
    try {
      await interventionApi.submitFeedback(feedback)
      
      trackCustomEvent('intervention_feedback_submitted', {
        intervention_id: feedback.intervention_id,
        was_helpful: feedback.was_helpful,
        session_id: sessionId
      })
    } catch (error) {
      console.error('Error submitting intervention feedback:', error)
    }
  }, [sessionId, trackCustomEvent])

  // Manual trigger for testing or explicit help requests
  const triggerHelp = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await interventionApi.triggerManualHelp(sessionId, currentStep || 1)
      
      if (response.help_message) {
        const messageId = response.help_message.message_id
        setActiveHelpMessages(prev => new Map(prev.set(messageId, response)))
        
        trackCustomEvent('manual_help_triggered', {
          message_id: messageId,
          step_number: currentStep,
          session_id: sessionId
        })
      }
    } catch (error) {
      console.error('Error triggering manual help:', error)
    }
  }, [sessionId, currentStep, trackCustomEvent])

  if (!enabled || activeHelpMessages.size === 0) {
    return null
  }

  return (
    <div className="intervention-system">
      {Array.from(activeHelpMessages.values()).map((helpResponse) => (
        <HelpMessage
          key={helpResponse.help_message.message_id}
          helpMessage={helpResponse.help_message}
          onDismiss={handleDismissMessage}
          onFeedback={handleFeedback}
          interventionId={parseInt(helpResponse.help_message.context.intervention_id || '0')}
          sessionId={sessionId}
        />
      ))}
    </div>
  )
}

export default InterventionSystem
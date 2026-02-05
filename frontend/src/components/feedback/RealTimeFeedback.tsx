import React, { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { engagementApi } from '../../utils/api'
import './RealTimeFeedback.css'

interface RealTimeFeedbackProps {
  sessionId?: number
  showEngagementScore?: boolean
  showInteractionCount?: boolean
  showTimeSpent?: boolean
}

interface EngagementData {
  current_score: number
  score_history: Array<{
    timestamp: string
    score: number
  }>
  last_updated: string
}

const RealTimeFeedback: React.FC<RealTimeFeedbackProps> = ({
  sessionId,
  showEngagementScore = true,
  showInteractionCount = true,
  showTimeSpent = true
}) => {
  const { user } = useAuth()
  const [engagementData, setEngagementData] = useState<EngagementData | null>(null)
  const [interactionCount, setInteractionCount] = useState(0)
  const [timeSpent, setTimeSpent] = useState(0)
  const [isVisible, setIsVisible] = useState(false)
  const [lastFeedbackMessage, setLastFeedbackMessage] = useState<string>('')

  // Update engagement score periodically
  useEffect(() => {
    if (!user || !showEngagementScore) return

    const fetchEngagementScore = async () => {
      try {
        const data = await engagementApi.getEngagementScore()
        setEngagementData(data)
      } catch (error) {
        console.error('Failed to fetch engagement score:', error)
      }
    }

    // Initial fetch
    fetchEngagementScore()

    // Set up periodic updates every 10 seconds
    const interval = setInterval(fetchEngagementScore, 10000)

    return () => clearInterval(interval)
  }, [user, showEngagementScore])

  // Track time spent
  useEffect(() => {
    if (!showTimeSpent) return

    const startTime = Date.now()
    const interval = setInterval(() => {
      setTimeSpent(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)

    return () => clearInterval(interval)
  }, [showTimeSpent])

  // Listen for interaction events to update count
  useEffect(() => {
    if (!showInteractionCount) return

    const handleInteraction = () => {
      setInteractionCount(prev => prev + 1)
    }

    // Listen for various interaction types
    document.addEventListener('click', handleInteraction)
    document.addEventListener('keydown', handleInteraction)
    window.addEventListener('scroll', handleInteraction)

    return () => {
      document.removeEventListener('click', handleInteraction)
      document.removeEventListener('keydown', handleInteraction)
      window.removeEventListener('scroll', handleInteraction)
    }
  }, [showInteractionCount])

  // Show/hide feedback based on engagement score
  useEffect(() => {
    if (!engagementData) return

    const score = engagementData.current_score
    
    // Show feedback for low engagement
    if (score < 30) {
      setIsVisible(true)
      setLastFeedbackMessage('Your engagement is low. Try interacting more with the content!')
    } else if (score < 50) {
      setIsVisible(true)
      setLastFeedbackMessage('Good progress! Keep engaging with the material.')
    } else if (score >= 80) {
      setIsVisible(true)
      setLastFeedbackMessage('Excellent engagement! You\'re doing great!')
      // Auto-hide positive feedback after 3 seconds
      setTimeout(() => setIsVisible(false), 3000)
    } else {
      setIsVisible(false)
    }
  }, [engagementData])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#38a169' // Green
    if (score >= 60) return '#d69e2e' // Yellow
    if (score >= 40) return '#ed8936' // Orange
    return '#e53e3e' // Red
  }

  const getScoreLabel = (score: number): string => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Fair'
    return 'Needs Improvement'
  }

  if (!user) return null

  return (
    <div className="real-time-feedback">
      {/* Engagement Score Display */}
      {showEngagementScore && engagementData && (
        <div className="feedback-metric engagement-score">
          <div className="metric-header">
            <span className="metric-label">Engagement</span>
            <span 
              className="metric-value"
              style={{ color: getScoreColor(engagementData.current_score) }}
            >
              {Math.round(engagementData.current_score)}%
            </span>
          </div>
          <div className="score-bar">
            <div 
              className="score-fill"
              style={{ 
                width: `${engagementData.current_score}%`,
                backgroundColor: getScoreColor(engagementData.current_score)
              }}
            />
          </div>
          <div className="score-label">
            {getScoreLabel(engagementData.current_score)}
          </div>
        </div>
      )}

      {/* Interaction Count */}
      {showInteractionCount && (
        <div className="feedback-metric interaction-count">
          <div className="metric-header">
            <span className="metric-label">Interactions</span>
            <span className="metric-value">{interactionCount}</span>
          </div>
          <div className="metric-description">
            Clicks, scrolls, and key presses
          </div>
        </div>
      )}

      {/* Time Spent */}
      {showTimeSpent && (
        <div className="feedback-metric time-spent">
          <div className="metric-header">
            <span className="metric-label">Time Spent</span>
            <span className="metric-value">{formatTime(timeSpent)}</span>
          </div>
          <div className="metric-description">
            Active time on this page
          </div>
        </div>
      )}

      {/* Feedback Messages */}
      {isVisible && lastFeedbackMessage && (
        <div className={`feedback-message ${engagementData && engagementData.current_score >= 80 ? 'positive' : 'warning'}`}>
          <div className="message-content">
            <span className="message-icon">
              {engagementData && engagementData.current_score >= 80 ? '🎉' : '💡'}
            </span>
            <span className="message-text">{lastFeedbackMessage}</span>
          </div>
          <button 
            className="message-close"
            onClick={() => setIsVisible(false)}
            aria-label="Close feedback message"
          >
            ×
          </button>
        </div>
      )}
    </div>
  )
}

export default RealTimeFeedback
import React from 'react'
import { OnboardingStep } from '../../types/onboarding'
import './StepContent.css'

interface StepContentProps {
  step: OnboardingStep
  userRole: string
}

const StepContent: React.FC<StepContentProps> = ({ step, userRole }) => {
  const getRoleSpecificIcon = (role: string) => {
    switch (role) {
      case 'Developer':
        return '👨‍💻'
      case 'Business_User':
        return '👔'
      case 'Admin':
        return '⚙️'
      default:
        return '📚'
    }
  }

  const formatEstimatedTime = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} min`
    }
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
  }

  return (
    <div className="step-content">
      <div className="step-header">
        <div className="step-icon">
          {getRoleSpecificIcon(userRole)}
        </div>
        <div className="step-info">
          <h2 className="step-title">{step.title}</h2>
          <div className="step-meta">
            <span className="step-time">
              ⏱️ Estimated time: {formatEstimatedTime(step.estimated_time)}
            </span>
            <span className="step-role">
              🎯 Tailored for {userRole.replace('_', ' ')}
            </span>
          </div>
        </div>
      </div>

      <div className="step-body">
        <div className="step-description">
          <div 
            className="content-text"
            dangerouslySetInnerHTML={{ __html: step.content }}
          />
        </div>

        {step.tasks && step.tasks.length > 0 && (
          <div className="step-tasks">
            <h3>Key Tasks for This Step:</h3>
            <ul className="task-list">
              {step.tasks.map((task, index) => (
                <li key={index} className="task-item">
                  <span className="task-bullet">✓</span>
                  <span className="task-text">{task}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="step-tips">
          <div className="tip-box">
            <h4>💡 Pro Tip</h4>
            <p>
              {userRole === 'Developer' && 
                "Focus on the technical implementation details and API examples provided."
              }
              {userRole === 'Business_User' && 
                "Pay attention to the workflow benefits and business impact of each feature."
              }
              {userRole === 'Admin' && 
                "Consider the administrative implications and user management aspects."
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StepContent
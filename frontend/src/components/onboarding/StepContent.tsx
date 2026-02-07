import React, { useState } from 'react'
import { OnboardingStep } from '../../types/onboarding'
import './StepContent.css'

interface StepContentProps {
  step: OnboardingStep
  userRole: string
  onCompletionChange?: (isComplete: boolean) => void
}

const StepContent: React.FC<StepContentProps> = ({ step, userRole, onCompletionChange }) => {
  const [completedSubSteps, setCompletedSubSteps] = useState<Set<number>>(new Set())

  // Reset checkboxes when step changes
  React.useEffect(() => {
    setCompletedSubSteps(new Set())
    // Notify parent that step is not complete on mount
    if (onCompletionChange) {
      const subtasksToCheck = step.subtasks && step.subtasks.length > 0 ? step.subtasks : step.tasks
      if (subtasksToCheck.length === 0) {
        onCompletionChange(true) // Auto-complete if no tasks
      } else {
        onCompletionChange(false) // Reset to incomplete
      }
    }
  }, [step.step_number, onCompletionChange])

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

  const toggleSubStep = (subStepIndex: number) => {
    const newCompleted = new Set(completedSubSteps)
    if (newCompleted.has(subStepIndex)) {
      newCompleted.delete(subStepIndex)
    } else {
      newCompleted.add(subStepIndex)
    }
    setCompletedSubSteps(newCompleted)
    
    // Notify parent of completion status
    if (onCompletionChange) {
      const allComplete = newCompleted.size === subtasks.length
      onCompletionChange(allComplete)
    }
  }

  // Use Gemini-generated subtasks if available, otherwise fall back to tasks
  const subtasks = step.subtasks && step.subtasks.length > 0 ? step.subtasks : step.tasks
  const completedCount = Array.from(completedSubSteps).length
  const progress = subtasks.length > 0 ? (completedCount / subtasks.length) * 100 : 0

  // Debug logging
  console.log('StepContent render:', {
    stepNumber: step.step_number,
    completedSubSteps: Array.from(completedSubSteps),
    completedCount,
    progress
  })

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
            dangerouslySetInnerHTML={{ __html: step.description || step.content }}
          />
        </div>

        {subtasks.length > 0 && (
          <div className="step-tasks-detailed">
            <h3>📋 Step-by-Step Instructions:</h3>
            <p className="tasks-intro">Complete these {subtasks.length} tasks to finish this onboarding step. Check off each task as you complete it.</p>
            
            {progress > 0 && (
              <div className="overall-progress">
                <div className="progress-label">
                  <span>Progress: {completedCount}/{subtasks.length} completed</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
            
            <ol className="substep-list">
              {subtasks.map((substep, index) => {
                const isCompleted = completedSubSteps.has(index)
                return (
                  <li 
                    key={index} 
                    className={`substep-item ${isCompleted ? 'completed' : ''}`}
                  >
                    <div className="substep-content">
                      <label className="substep-checkbox">
                        <input
                          type="checkbox"
                          checked={isCompleted}
                          onChange={() => toggleSubStep(index)}
                        />
                        <span className="checkmark"></span>
                      </label>
                      <span className="substep-text">{substep}</span>
                    </div>
                  </li>
                )
              })}
            </ol>
          </div>
        )}

        <div className="step-tips">
          <div className="tip-box">
            <h4>💡 Pro Tip</h4>
            <p>
              {step.tip || (
                <>
                  {userRole === 'Developer' && 
                    "Focus on the technical implementation details and API examples provided. Use the code examples as a starting point for your integration."
                  }
                  {userRole === 'Business_User' && 
                    "Pay attention to the workflow benefits and business impact of each feature. Consider how these steps will improve your daily operations."
                  }
                  {userRole === 'Admin' && 
                    "Consider the administrative implications and user management aspects. Think about how to scale these processes across your organization."
                  }
                </>
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StepContent
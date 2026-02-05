import React from 'react'
import './ProgressIndicator.css'

interface ProgressIndicatorProps {
  currentStep: number
  totalSteps: number
  completionPercentage: number
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentStep,
  totalSteps,
  completionPercentage
}) => {
  const steps = Array.from({ length: totalSteps }, (_, index) => index + 1)

  return (
    <div className="progress-indicator">
      <div className="progress-header">
        <h3>Your Progress</h3>
        <span className="progress-text">
          Step {currentStep} of {totalSteps} ({Math.round(completionPercentage)}% complete)
        </span>
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
        <span className="progress-percentage">
          {Math.round(completionPercentage)}%
        </span>
      </div>

      <div className="step-indicators">
        {steps.map((stepNumber) => {
          const isCompleted = stepNumber < currentStep
          const isCurrent = stepNumber === currentStep
          const isUpcoming = stepNumber > currentStep

          return (
            <div
              key={stepNumber}
              className={`step-indicator ${
                isCompleted ? 'completed' : 
                isCurrent ? 'current' : 
                'upcoming'
              }`}
            >
              <div className="step-circle">
                {isCompleted ? (
                  <svg className="check-icon" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <span className="step-number">{stepNumber}</span>
                )}
              </div>
              <span className="step-label">
                {isCompleted ? 'Completed' : 
                 isCurrent ? 'In Progress' : 
                 'Upcoming'}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ProgressIndicator
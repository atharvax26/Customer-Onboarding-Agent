import React from 'react'
import { DropoffAnalysisResponse } from '../../types/analytics'
import BarChart from './BarChart'
import MetricCard from './MetricCard'
import './DropoffAnalysis.css'

interface DropoffAnalysisProps {
  data: DropoffAnalysisResponse
  isLoading?: boolean
}

const DropoffAnalysis: React.FC<DropoffAnalysisProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="dropoff-loading">
        <div className="loading-spinner"></div>
        <p>Loading drop-off analysis...</p>
      </div>
    )
  }

  // Safety check for data
  if (!data || !data.steps || data.steps.length === 0) {
    return (
      <div className="dropoff-error">
        <p>No drop-off data available</p>
      </div>
    )
  }

  // Prepare data for completion rate chart
  const completionData = data.steps.map((step, index) => ({
    label: `Step ${step.step_number}`,
    value: step.completion_rate,
    color: getCompletionColor(step.completion_rate)
  }))

  // Prepare data for user count chart
  const userCountData = data.steps.map((step, index) => ({
    label: `Step ${step.step_number}`,
    value: step.started_count,
    color: '#3b82f6'
  }))

  // Find the step with highest drop-off
  const highestDropoff = data.steps.reduce((prev, current) => 
    (100 - current.completion_rate) > (100 - prev.completion_rate) ? current : prev
  )

  // Calculate average time spent
  const avgTimeSpent = data.steps.reduce((sum, step) => 
    sum + (step.average_time_spent || 0), 0
  ) / data.steps.length

  return (
    <div className="dropoff-analysis-section">
      <div className="metrics-grid">
        <MetricCard
          title="Overall Completion"
          value={`${data.overall_completion_rate.toFixed(1)}%`}
          trend={getCompletionTrend(data.overall_completion_rate)}
          trendValue={getCompletionDescription(data.overall_completion_rate)}
          color="blue"
          icon="🎯"
        />
        <MetricCard
          title="Highest Drop-off"
          value={`Step ${highestDropoff.step_number}`}
          subtitle={`${(100 - highestDropoff.completion_rate).toFixed(1)}% drop-off`}
          color="red"
          icon="⚠️"
        />
        <MetricCard
          title="Average Time"
          value={`${Math.round(avgTimeSpent)}s`}
          subtitle="Per step completion"
          color="green"
          icon="⏱️"
        />
      </div>

      <div className="charts-grid">
        <BarChart
          data={completionData}
          title="Completion Rate by Step"
          height={300}
          showValues={true}
          maxValue={100}
        />
        
        <BarChart
          data={userCountData}
          title="Users Started by Step"
          height={300}
          showValues={true}
        />
      </div>

      <div className="step-details-table">
        <h3>Step-by-Step Analysis</h3>
        <div className="table-container">
          <table className="details-table">
            <thead>
              <tr>
                <th>Step</th>
                <th>Title</th>
                <th>Started</th>
                <th>Completed</th>
                <th>Completion Rate</th>
                <th>Avg Time</th>
                <th>Drop-off</th>
              </tr>
            </thead>
            <tbody>
              {data.steps.map((step) => {
                const dropoffRate = 100 - step.completion_rate
                return (
                  <tr key={step.step_number} className={getRowClass(step.completion_rate)}>
                    <td className="step-number">{step.step_number}</td>
                    <td className="step-title">{step.step_title}</td>
                    <td>{step.started_count}</td>
                    <td>{step.completed_count}</td>
                    <td>
                      <div className="completion-bar">
                        <div 
                          className="completion-fill"
                          style={{ 
                            width: `${step.completion_rate}%`,
                            backgroundColor: getCompletionColor(step.completion_rate)
                          }}
                        ></div>
                        <span className="completion-text">
                          {step.completion_rate.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td>
                      {step.average_time_spent 
                        ? `${Math.round(step.average_time_spent)}s`
                        : 'N/A'
                      }
                    </td>
                    <td>
                      <span className={`dropoff-badge ${getDropoffClass(dropoffRate)}`}>
                        {dropoffRate.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="insights-section">
        <h3>Key Insights</h3>
        <div className="insights-grid">
          <div className="insight-card">
            <h4>🔍 Critical Drop-off Point</h4>
            <p>
              Step {highestDropoff.step_number} has the highest drop-off rate at{' '}
              {(100 - highestDropoff.completion_rate).toFixed(1)}%. 
              Consider reviewing the content or adding additional support.
            </p>
          </div>
          
          <div className="insight-card">
            <h4>📊 Completion Trend</h4>
            <p>
              {data.overall_completion_rate >= 70 
                ? 'Strong overall completion rate indicates effective onboarding flow.'
                : data.overall_completion_rate >= 50
                ? 'Moderate completion rate - there\'s room for improvement.'
                : 'Low completion rate suggests significant onboarding challenges.'
              }
            </p>
          </div>
          
          <div className="insight-card">
            <h4>⏰ Time Analysis</h4>
            <p>
              Average time per step is {Math.round(avgTimeSpent)} seconds.
              {avgTimeSpent > 300 
                ? ' Consider breaking down complex steps.'
                : avgTimeSpent < 60
                ? ' Steps might be too simple or rushed.'
                : ' Time spent appears appropriate.'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function getCompletionColor(rate: number): string {
  if (rate >= 80) return '#10b981'
  if (rate >= 60) return '#3b82f6'
  if (rate >= 40) return '#f59e0b'
  return '#ef4444'
}

function getCompletionTrend(rate: number): 'up' | 'down' | 'stable' {
  if (rate >= 70) return 'up'
  if (rate <= 40) return 'down'
  return 'stable'
}

function getCompletionDescription(rate: number): string {
  if (rate >= 80) return 'Excellent'
  if (rate >= 60) return 'Good'
  if (rate >= 40) return 'Fair'
  return 'Poor'
}

function getRowClass(completionRate: number): string {
  if (completionRate >= 80) return 'row-excellent'
  if (completionRate >= 60) return 'row-good'
  if (completionRate >= 40) return 'row-fair'
  return 'row-poor'
}

function getDropoffClass(dropoffRate: number): string {
  if (dropoffRate >= 40) return 'dropoff-high'
  if (dropoffRate >= 20) return 'dropoff-medium'
  return 'dropoff-low'
}

export default DropoffAnalysis
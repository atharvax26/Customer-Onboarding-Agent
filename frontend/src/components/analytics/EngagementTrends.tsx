import React from 'react'
import { TrendData } from '../../types/analytics'
import LineChart from './LineChart'
import MetricCard from './MetricCard'
import './EngagementTrends.css'

interface EngagementTrendsProps {
  data: TrendData[]
  isLoading?: boolean
}

const EngagementTrends: React.FC<EngagementTrendsProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="engagement-loading">
        <div className="loading-spinner"></div>
        <p>Loading engagement trends...</p>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="engagement-empty">
        <p>No engagement data available</p>
      </div>
    )
  }

  // Process the first trend data (assuming engagement scores)
  const engagementTrend = data[0]
  const chartData = engagementTrend.data_points.map(point => ({
    label: formatDate(point.date),
    value: point.value,
    date: point.date
  }))

  // Calculate metrics
  const currentScore = chartData.length > 0 ? chartData[chartData.length - 1].value : 0
  const previousScore = chartData.length > 1 ? chartData[chartData.length - 2].value : currentScore
  const scoreChange = currentScore - previousScore
  const averageScore = chartData.reduce((sum, point) => sum + point.value, 0) / chartData.length

  // Calculate trend statistics
  const maxScore = Math.max(...chartData.map(d => d.value))
  const minScore = Math.min(...chartData.map(d => d.value))
  const totalDataPoints = chartData.reduce((sum, point) => sum + (point as any).count || 1, 0)

  return (
    <div className="engagement-trends-section">
      <div className="metrics-grid">
        <MetricCard
          title="Current Score"
          value={currentScore.toFixed(1)}
          trend={scoreChange > 0 ? 'up' : scoreChange < 0 ? 'down' : 'stable'}
          trendValue={`${scoreChange >= 0 ? '+' : ''}${scoreChange.toFixed(1)}`}
          color="blue"
          icon="📊"
        />
        <MetricCard
          title="Average Score"
          value={averageScore.toFixed(1)}
          subtitle="Over selected period"
          color="green"
          icon="📈"
        />
        <MetricCard
          title="Score Range"
          value={`${minScore.toFixed(1)} - ${maxScore.toFixed(1)}`}
          subtitle="Min - Max values"
          color="purple"
          icon="📏"
        />
        <MetricCard
          title="Trend Direction"
          value={getTrendEmoji(engagementTrend.trend_direction)}
          subtitle={engagementTrend.trend_direction.toUpperCase()}
          color={getTrendColor(engagementTrend.trend_direction)}
          icon="🎯"
        />
      </div>

      <LineChart
        data={chartData}
        title="Engagement Score Over Time"
        height={400}
        color="#3b82f6"
        showDots={true}
        maxValue={100}
      />

      <div className="trend-analysis">
        <h3>Trend Analysis</h3>
        <div className="analysis-grid">
          <div className="analysis-card">
            <h4>📈 Score Performance</h4>
            <p>
              {currentScore >= 80 
                ? 'Excellent engagement levels! Users are highly engaged with the onboarding process.'
                : currentScore >= 60
                ? 'Good engagement levels. There\'s room for improvement in user interaction.'
                : currentScore >= 40
                ? 'Moderate engagement. Consider reviewing content and user experience.'
                : 'Low engagement detected. Immediate attention needed to improve user experience.'
              }
            </p>
          </div>

          <div className="analysis-card">
            <h4>📊 Trend Direction</h4>
            <p>
              {engagementTrend.trend_direction === 'up' 
                ? 'Positive trend! Engagement scores are improving over time.'
                : engagementTrend.trend_direction === 'down'
                ? 'Declining trend. Consider investigating factors causing decreased engagement.'
                : 'Stable trend. Engagement levels are consistent but may benefit from optimization.'
              }
            </p>
          </div>

          <div className="analysis-card">
            <h4>🎯 Recommendations</h4>
            <p>
              {getRecommendations(currentScore, engagementTrend.trend_direction, scoreChange)}
            </p>
          </div>
        </div>
      </div>

      {chartData.length > 0 && (
        <div className="data-summary">
          <h3>Data Summary</h3>
          <div className="summary-stats">
            <div className="stat-item">
              <span className="stat-label">Data Points:</span>
              <span className="stat-value">{chartData.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Date Range:</span>
              <span className="stat-value">
                {formatDate(chartData[0].date)} - {formatDate(chartData[chartData.length - 1].date)}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Score Variance:</span>
              <span className="stat-value">{(maxScore - minScore).toFixed(1)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  })
}

function getTrendEmoji(direction: string): string {
  switch (direction) {
    case 'up': return '📈'
    case 'down': return '📉'
    case 'stable': return '➡️'
    default: return '📊'
  }
}

function getTrendColor(direction: string): 'blue' | 'green' | 'red' | 'yellow' | 'purple' {
  switch (direction) {
    case 'up': return 'green'
    case 'down': return 'red'
    case 'stable': return 'blue'
    default: return 'purple'
  }
}

function getRecommendations(currentScore: number, trend: string, change: number): string {
  if (currentScore >= 80 && trend === 'up') {
    return 'Maintain current strategies. Consider documenting successful practices for replication.'
  } else if (currentScore >= 60 && trend === 'stable') {
    return 'Look for opportunities to boost engagement through interactive elements or personalization.'
  } else if (trend === 'down') {
    return 'Investigate recent changes that may have impacted engagement. Consider user feedback collection.'
  } else if (currentScore < 40) {
    return 'Urgent: Review onboarding flow, simplify complex steps, and add more guidance or support.'
  } else {
    return 'Focus on identifying and addressing common user pain points in the onboarding process.'
  }
}

export default EngagementTrends
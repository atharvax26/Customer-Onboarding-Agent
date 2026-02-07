import React, { useState, useEffect } from 'react'
import { RealTimeMetrics as RealTimeMetricsType } from '../../types/analytics'
import { useAnalytics } from '../../hooks/useApiClient'
import MetricCard from './MetricCard'
import './RealTimeMetrics.css'

interface RealTimeMetricsProps {
  refreshInterval?: number // in milliseconds
  autoRefresh?: boolean
}

const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({ 
  refreshInterval = 30000, // 30 seconds default
  autoRefresh = true 
}) => {
  const { getRealTimeMetrics, handleError } = useAnalytics()
  const [metrics, setMetrics] = useState<RealTimeMetricsType | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchMetrics = async () => {
    try {
      setError(null)
      const data = await getRealTimeMetrics()
      setMetrics(data)
      setLastUpdated(new Date())
    } catch (err) {
      setError(handleError(err))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()

    if (autoRefresh) {
      const interval = setInterval(fetchMetrics, refreshInterval)
      return () => clearInterval(interval)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshInterval, autoRefresh])

  const handleManualRefresh = () => {
    setIsLoading(true)
    fetchMetrics()
  }

  if (error) {
    return (
      <div className="real-time-error">
        <div className="error-content">
          <h3>⚠️ Unable to Load Real-Time Metrics</h3>
          <p>{error}</p>
          <button onClick={handleManualRefresh} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (isLoading && !metrics) {
    return (
      <div className="real-time-loading">
        <div className="loading-spinner"></div>
        <p>Loading real-time metrics...</p>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="real-time-empty">
        <p>No real-time metrics available</p>
      </div>
    )
  }

  const formatLastUpdated = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getEngagementTrend = (score: number): 'up' | 'down' | 'stable' => {
    if (score >= 70) return 'up'
    if (score <= 40) return 'down'
    return 'stable'
  }

  const getEngagementDescription = (score: number): string => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Fair'
    return 'Needs Attention'
  }

  return (
    <div className="real-time-metrics-section">
      <div className="metrics-header">
        <h3>Real-Time Metrics</h3>
        <div className="metrics-controls">
          <div className="last-updated">
            {lastUpdated && (
              <span>Last updated: {formatLastUpdated(lastUpdated)}</span>
            )}
          </div>
          <button 
            onClick={handleManualRefresh} 
            className={`refresh-button ${isLoading ? 'refreshing' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? '🔄' : '↻'} Refresh
          </button>
        </div>
      </div>

      <div className="real-time-grid">
        <MetricCard
          title="Active Sessions"
          value={metrics.active_sessions}
          subtitle="Currently online"
          color="blue"
          icon="👥"
        />
        
        <MetricCard
          title="24h Avg Engagement"
          value={`${metrics.average_engagement_24h.toFixed(1)}%`}
          trend={getEngagementTrend(metrics.average_engagement_24h)}
          trendValue={getEngagementDescription(metrics.average_engagement_24h)}
          color="green"
          icon="📊"
        />
        
        <MetricCard
          title="Interventions Today"
          value={metrics.total_interventions_today}
          subtitle="Help messages sent"
          color="yellow"
          icon="🆘"
        />
      </div>

      <div className="metrics-details">
        <div className="detail-card">
          <h4>📈 Session Activity</h4>
          <p>
            {metrics.active_sessions === 0 
              ? 'No active sessions currently. This is normal during off-peak hours.'
              : metrics.active_sessions === 1
              ? '1 user is currently going through onboarding.'
              : `${metrics.active_sessions} users are currently active in onboarding sessions.`
            }
          </p>
        </div>

        <div className="detail-card">
          <h4>🎯 Engagement Health</h4>
          <p>
            {metrics.average_engagement_24h >= 70 
              ? 'Engagement levels are healthy. Users are actively participating in the onboarding process.'
              : metrics.average_engagement_24h >= 50
              ? 'Engagement is moderate. Consider reviewing user feedback for improvement opportunities.'
              : 'Low engagement detected. Review onboarding content and user experience immediately.'
            }
          </p>
        </div>

        <div className="detail-card">
          <h4>🆘 Intervention Analysis</h4>
          <p>
            {metrics.total_interventions_today === 0 
              ? 'No interventions triggered today. Users are progressing smoothly through onboarding.'
              : metrics.total_interventions_today <= 5
              ? `${metrics.total_interventions_today} intervention(s) today. This indicates some users needed help.`
              : `High intervention count (${metrics.total_interventions_today}) suggests onboarding challenges that need attention.`
            }
          </p>
        </div>
      </div>

      <div className="auto-refresh-indicator">
        {autoRefresh && (
          <div className="refresh-indicator">
            <span className="refresh-dot"></span>
            Auto-refreshing every {refreshInterval / 1000} seconds
          </div>
        )}
      </div>
    </div>
  )
}

export default RealTimeMetrics
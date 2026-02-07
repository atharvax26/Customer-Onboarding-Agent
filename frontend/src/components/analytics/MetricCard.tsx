import React from 'react'
import './MetricCard.css'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple'
  icon?: React.ReactNode
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  color = 'blue',
  icon
}) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return '↗'
      case 'down':
        return '↘'
      case 'stable':
        return '→'
      default:
        return null
    }
  }

  const getTrendClass = () => {
    switch (trend) {
      case 'up':
        return 'trend-up'
      case 'down':
        return 'trend-down'
      case 'stable':
        return 'trend-stable'
      default:
        return ''
    }
  }

  return (
    <div className={`metric-card metric-card-${color}`}>
      <div className="metric-header">
        <div className="metric-title">{title}</div>
        {icon && <div className="metric-icon">{icon}</div>}
      </div>
      
      <div className="metric-value">{value}</div>
      
      {subtitle && (
        <div className="metric-subtitle">{subtitle}</div>
      )}
      
      {trend && trendValue && (
        <div className={`metric-trend ${getTrendClass()}`}>
          <span className="trend-icon">{getTrendIcon()}</span>
          <span className="trend-value">{trendValue}</span>
        </div>
      )}
    </div>
  )
}

export default MetricCard
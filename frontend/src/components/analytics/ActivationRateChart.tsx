import React from 'react'
import { ActivationMetrics } from '../../types/analytics'
import BarChart from './BarChart'
import MetricCard from './MetricCard'
import './ActivationRateChart.css'

interface ActivationRateChartProps {
  data: ActivationMetrics
  isLoading?: boolean
}

const ActivationRateChart: React.FC<ActivationRateChartProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="activation-rate-loading">
        <div className="loading-spinner"></div>
        <p>Loading activation rates...</p>
      </div>
    )
  }

  // Safety check for data
  if (!data || !data.role_breakdown) {
    return (
      <div className="activation-rate-error">
        <p>No activation data available</p>
      </div>
    )
  }

  // Prepare data for role breakdown chart
  const roleData = Object.entries(data.role_breakdown).map(([role, stats]) => ({
    label: role.replace('_', ' '),
    value: stats.activated || 0,
    color: getRoleColor(role)
  }))

  // Calculate activation rate percentage
  const activationPercentage = data.total_users > 0 
    ? Math.round((data.activated_users / data.total_users) * 100)
    : 0

  return (
    <div className="activation-rate-section">
      <div className="metrics-grid">
        <MetricCard
          title="Total Users"
          value={data.total_users}
          color="blue"
          icon="👥"
        />
        <MetricCard
          title="Activated Users"
          value={data.activated_users}
          subtitle={`${activationPercentage}% of total users`}
          color="green"
          icon="✅"
        />
        <MetricCard
          title="Activation Rate"
          value={`${data.activation_rate.toFixed(1)}%`}
          trend={getActivationTrend(data.activation_rate)}
          trendValue={getTrendDescription(data.activation_rate)}
          color="purple"
          icon="📈"
        />
      </div>

      {roleData.length > 0 && (
        <BarChart
          data={roleData}
          title="Activated Users by Role"
          height={300}
          showValues={true}
        />
      )}

      <div className="role-breakdown-table">
        <h3>Detailed Role Breakdown</h3>
        <div className="table-container">
          <table className="breakdown-table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Total Users</th>
                <th>Activated</th>
                <th>Rate</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.role_breakdown).map(([role, stats]) => {
                const rate = stats.total > 0 ? (stats.activated / stats.total) * 100 : 0
                return (
                  <tr key={role}>
                    <td className="role-cell">
                      <span 
                        className="role-indicator" 
                        style={{ backgroundColor: getRoleColor(role) }}
                      ></span>
                      {role.replace('_', ' ')}
                    </td>
                    <td>{stats.total}</td>
                    <td>{stats.activated}</td>
                    <td className="rate-cell">
                      <span className={`rate-badge ${getRateClass(rate)}`}>
                        {rate.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    'Developer': '#3b82f6',
    'Business_User': '#10b981',
    'Admin': '#f59e0b'
  }
  return colors[role] || '#6b7280'
}

function getActivationTrend(rate: number): 'up' | 'down' | 'stable' {
  if (rate >= 80) return 'up'
  if (rate <= 40) return 'down'
  return 'stable'
}

function getTrendDescription(rate: number): string {
  if (rate >= 80) return 'Excellent'
  if (rate >= 60) return 'Good'
  if (rate >= 40) return 'Fair'
  return 'Needs Improvement'
}

function getRateClass(rate: number): string {
  if (rate >= 80) return 'rate-excellent'
  if (rate >= 60) return 'rate-good'
  if (rate >= 40) return 'rate-fair'
  return 'rate-poor'
}

export default ActivationRateChart
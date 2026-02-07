import React, { useState, useEffect } from 'react'
import {
  FilterControls,
  ActivationRateChart,
  DropoffAnalysis,
  EngagementTrends,
  RealTimeMetrics
} from '../components/analytics'
import { useAnalytics } from '../hooks/useApiClient'
import {
  AnalyticsFilters,
  ActivationMetrics,
  DropoffAnalysisResponse,
  TrendData
} from '../types/analytics'
import './Analytics.css'

const Analytics: React.FC = () => {
  const { getActivationRates, getDropoffAnalysis, getEngagementTrends, handleError } = useAnalytics()
  const [filters, setFilters] = useState<AnalyticsFilters>({})
  const [activationData, setActivationData] = useState<ActivationMetrics | null>(null)
  const [dropoffData, setDropoffData] = useState<DropoffAnalysisResponse | null>(null)
  const [engagementData, setEngagementData] = useState<TrendData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAnalyticsData = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Fetch data with proper error handling for each request
      const activationPromise = getActivationRates(filters).catch(err => {
        console.error('Activation rates error:', err)
        return null
      })
      
      const dropoffPromise = getDropoffAnalysis(filters).catch(err => {
        console.error('Dropoff analysis error:', err)
        return null
      })
      
      const engagementPromise = getEngagementTrends(filters.user_id, 30).catch(err => {
        console.error('Engagement trends error:', err)
        return null
      })

      const [activation, dropoff, engagement] = await Promise.all([
        activationPromise,
        dropoffPromise,
        engagementPromise
      ])

      setActivationData(activation)
      setDropoffData(dropoff)
      setEngagementData(engagement ? [engagement] : [])
    } catch (err) {
      console.error('Analytics fetch error:', err)
      setError(handleError(err))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalyticsData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)])

  const handleFiltersChange = (newFilters: AnalyticsFilters) => {
    setFilters(newFilters)
  }

  const handleRefresh = () => {
    fetchAnalyticsData()
  }

  if (error) {
    return (
      <div className="analytics-error">
        <div className="error-content">
          <h2>⚠️ Unable to Load Analytics</h2>
          <p>{error}</p>
          <button onClick={handleRefresh} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <p>Comprehensive insights into user onboarding performance and engagement</p>
      </div>

      <FilterControls
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onRefresh={handleRefresh}
        isLoading={isLoading}
      />

      <RealTimeMetrics
        refreshInterval={30000}
        autoRefresh={true}
      />

      {activationData && (
        <ActivationRateChart
          data={activationData}
          isLoading={isLoading}
        />
      )}

      {dropoffData && (
        <DropoffAnalysis
          data={dropoffData}
          isLoading={isLoading}
        />
      )}

      {engagementData.length > 0 && (
        <EngagementTrends
          data={engagementData}
          isLoading={isLoading}
        />
      )}

      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Loading analytics data...</p>
        </div>
      )}
    </div>
  )
}

export default Analytics
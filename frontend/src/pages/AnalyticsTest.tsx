import React, { useState, useEffect } from 'react'
import { useAnalytics } from '../hooks/useApiClient'

const AnalyticsTest: React.FC = () => {
  const { getRealTimeMetrics, handleError } = useAnalytics()
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching real-time metrics...')
        const metrics = await getRealTimeMetrics()
        console.log('Received metrics:', metrics)
        setData(metrics)
      } catch (err) {
        console.error('Error fetching metrics:', err)
        setError(handleError(err))
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return <div style={{ padding: '2rem' }}>Loading...</div>
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', color: 'red' }}>
        <h2>Error</h2>
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Analytics Test Page</h1>
      <h2>Real-Time Metrics:</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}

export default AnalyticsTest

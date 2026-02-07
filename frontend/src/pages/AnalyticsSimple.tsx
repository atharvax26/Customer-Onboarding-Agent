import React from 'react'
import './Analytics.css'

const AnalyticsSimple: React.FC = () => {
  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h1>Analytics Dashboard (Simple Test)</h1>
        <p>Testing if the page renders at all</p>
      </div>
      
      <div style={{ padding: '2rem', background: 'white', borderRadius: '8px', margin: '1rem 0' }}>
        <h2>✅ Page Loaded Successfully!</h2>
        <p>If you see this, the routing and basic page structure works.</p>
        <p>The error is likely in one of the analytics components.</p>
      </div>
    </div>
  )
}

export default AnalyticsSimple

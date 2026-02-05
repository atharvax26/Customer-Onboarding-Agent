import React from 'react'

const Home: React.FC = () => {
  return (
    <div>
      <h1>Welcome to Customer Onboarding Agent</h1>
      <p>
        Transform your product documentation into personalized, role-based onboarding experiences 
        with AI-powered document processing and real-time engagement analytics.
      </p>
      <div style={{ marginTop: '2rem' }}>
        <h2>Features</h2>
        <ul>
          <li>AI-powered document processing with Claude API</li>
          <li>Role-based onboarding flows (Developer, Business User, Admin)</li>
          <li>Real-time engagement scoring and interventions</li>
          <li>Comprehensive analytics dashboard</li>
        </ul>
      </div>
    </div>
  )
}

export default Home
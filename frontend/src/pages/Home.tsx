import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Home: React.FC = () => {
  const { isAuthenticated } = useAuth()

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

      {isAuthenticated && (
        <div style={{ marginTop: '2rem', padding: '1.5rem', background: '#f8f9fa', borderRadius: '8px' }}>
          <h3>Get Started</h3>
          <p>Ready to create your first onboarding experience?</p>
          <Link 
            to="/documents" 
            style={{
              display: 'inline-block',
              background: '#007bff',
              color: 'white',
              padding: '0.75rem 1.5rem',
              textDecoration: 'none',
              borderRadius: '6px',
              fontWeight: '500'
            }}
          >
            📄 Upload Your First Document
          </Link>
        </div>
      )}
    </div>
  )
}

export default Home
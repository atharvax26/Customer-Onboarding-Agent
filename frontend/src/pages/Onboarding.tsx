import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import OnboardingFlow from '../components/onboarding/OnboardingFlow'

const Onboarding: React.FC = () => {
  const { user } = useAuth()
  // Use document ID 1 directly since we know it exists
  const [selectedDocumentId] = useState<number>(1)
  const [loading] = useState(false)
  const [error] = useState<string | null>(null)

  // Skip document fetching - use existing document
  // This avoids rate limit issues

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '60vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid #e2e8f0',
          borderTop: '4px solid #667eea',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p>Loading documents...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '2rem',
        maxWidth: '500px',
        margin: '0 auto'
      }}>
        <h2 style={{ color: '#e53e3e', marginBottom: '1rem' }}>Error</h2>
        <p style={{ marginBottom: '1.5rem' }}>{error}</p>
        <button 
          onClick={() => window.location.reload()}
          style={{
            background: '#667eea',
            color: 'white',
            border: 'none',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    )
  }

  return <OnboardingFlow documentId={selectedDocumentId} />
}

export default Onboarding
import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import OnboardingFlow from '../components/onboarding/OnboardingFlow'
import { documentApi } from '../utils/api'

interface Document {
  id: number
  filename: string
  uploaded_at: string
}

const Onboarding: React.FC = () => {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true)
        const docs = await documentApi.getDocuments()
        setDocuments(docs)
        
        // Auto-select the first document if available
        if (docs.length > 0) {
          setSelectedDocumentId(docs[0].id)
        }
      } catch (err) {
        console.error('Failed to fetch documents:', err)
        setError('Failed to load documents. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchDocuments()
  }, [])

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

  if (documents.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '2rem',
        maxWidth: '600px',
        margin: '0 auto'
      }}>
        <h2>No Documents Available</h2>
        <p style={{ marginBottom: '1.5rem' }}>
          No documents have been uploaded yet. Please contact your administrator to upload 
          onboarding documents before starting your onboarding journey.
        </p>
        <p style={{ color: '#4a5568', fontSize: '0.9rem' }}>
          Your role: <strong>{user?.role}</strong>
        </p>
      </div>
    )
  }

  if (!selectedDocumentId) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '2rem',
        maxWidth: '600px',
        margin: '0 auto'
      }}>
        <h2>Select a Document</h2>
        <p style={{ marginBottom: '1.5rem' }}>
          Choose a document to start your onboarding:
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {documents.map((doc) => (
            <button
              key={doc.id}
              onClick={() => setSelectedDocumentId(doc.id)}
              style={{
                background: 'white',
                border: '2px solid #e2e8f0',
                padding: '1rem',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'border-color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#667eea'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#e2e8f0'
              }}
            >
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                {doc.filename}
              </div>
              <div style={{ fontSize: '0.9rem', color: '#4a5568' }}>
                Uploaded: {new Date(doc.uploaded_at).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      </div>
    )
  }

  return <OnboardingFlow documentId={selectedDocumentId} />
}

export default Onboarding
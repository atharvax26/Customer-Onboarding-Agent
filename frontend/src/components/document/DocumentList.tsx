import React, { useState, useEffect } from 'react'
import { useDocuments } from '../../hooks/useApiClient'
import { Document, ProcessedDocument } from '../../types/document'
import DocumentPreview from './DocumentPreview'
import './DocumentList.css'

interface DocumentListProps {
  refreshTrigger?: number
  onDocumentSelect?: (document: Document) => void
}

const DocumentList: React.FC<DocumentListProps> = ({
  refreshTrigger,
  onDocumentSelect
}) => {
  const { getAll, process, delete: deleteDoc, handleError } = useDocuments()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [processingDocuments, setProcessingDocuments] = useState<Set<number>>(new Set())

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      const docs = await getAll()
      setDocuments(docs)
    } catch (err: any) {
      setError(handleError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [refreshTrigger])

  const handleProcessDocument = async (documentId: number) => {
    try {
      setProcessingDocuments(prev => new Set(prev).add(documentId))
      const result = await process(documentId)
      
      // Update the document in the list
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId 
          ? { ...doc, processed_summary: result.summary, step_tasks: result.tasks }
          : doc
      ))
    } catch (err: any) {
      setError(handleError(err))
    } finally {
      setProcessingDocuments(prev => {
        const newSet = new Set(prev)
        newSet.delete(documentId)
        return newSet
      })
    }
  }

  const handleDeleteDocument = async (documentId: number) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return
    }

    try {
      await deleteDoc(documentId)
      setDocuments(prev => prev.filter(doc => doc.id !== documentId))
      if (selectedDocument?.id === documentId) {
        setSelectedDocument(null)
      }
    } catch (err: any) {
      setError(handleError(err))
    }
  }

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'Unknown size'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isProcessed = (doc: Document): boolean => {
    return !!(doc.processed_summary && doc.step_tasks)
  }

  if (loading) {
    return (
      <div className="document-list-loading">
        <div className="loading-spinner"></div>
        <p>Loading documents...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="document-list-error">
        <div className="error-icon">⚠️</div>
        <h3>Error Loading Documents</h3>
        <p>{error}</p>
        <button onClick={loadDocuments} className="retry-button">
          Try Again
        </button>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="document-list-empty">
        <div className="empty-icon">📄</div>
        <h3>No Documents Yet</h3>
        <p>Upload your first document to get started with onboarding flows.</p>
      </div>
    )
  }

  return (
    <div className="document-list">
      <div className="document-list-header">
        <h2>Your Documents</h2>
        <button onClick={loadDocuments} className="refresh-button" disabled={loading}>
          🔄 Refresh
        </button>
      </div>

      <div className="document-grid">
        {documents.map(doc => (
          <div key={doc.id} className={`document-card ${isProcessed(doc) ? 'processed' : 'unprocessed'}`}>
            <div className="document-header">
              <div className="document-icon">
                {doc.filename.endsWith('.pdf') ? '📄' : '📝'}
              </div>
              <div className="document-info">
                <h3 className="document-title">{doc.filename}</h3>
                <p className="document-meta">
                  {formatFileSize(doc.file_size)} • {formatDate(doc.uploaded_at)}
                </p>
              </div>
              <div className="document-status">
                {isProcessed(doc) ? (
                  <span className="status-badge processed">✅ Processed</span>
                ) : (
                  <span className="status-badge unprocessed">⏳ Uploaded</span>
                )}
              </div>
            </div>

            <div className="document-actions">
              <button
                onClick={() => {
                  setSelectedDocument(doc)
                  onDocumentSelect?.(doc)
                }}
                className="action-button view"
              >
                👁️ View
              </button>

              {!isProcessed(doc) && (
                <button
                  onClick={() => handleProcessDocument(doc.id)}
                  disabled={processingDocuments.has(doc.id)}
                  className="action-button process"
                >
                  {processingDocuments.has(doc.id) ? '⚙️ Processing...' : '⚙️ Process'}
                </button>
              )}

              {isProcessed(doc) && (
                <button
                  onClick={() => {
                    // Navigate to onboarding with this document
                    window.location.href = `/onboarding?document=${doc.id}`
                  }}
                  className="action-button start"
                >
                  🚀 Start Onboarding
                </button>
              )}

              <button
                onClick={() => handleDeleteDocument(doc.id)}
                className="action-button delete"
              >
                🗑️ Delete
              </button>
            </div>

            {isProcessed(doc) && (
              <div className="document-summary">
                <h4>Summary Preview</h4>
                <p>{doc.processed_summary?.summary || 'Summary available'}</p>
                {doc.step_tasks && doc.step_tasks.length > 0 && (
                  <p className="task-count">{doc.step_tasks.length} tasks generated</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedDocument && (
        <DocumentPreview
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)}
        />
      )}
    </div>
  )
}

export default DocumentList
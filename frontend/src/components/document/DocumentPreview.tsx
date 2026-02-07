import React, { useState, useEffect } from 'react'
import { Document } from '../../types/document'
import { documentApi } from '../../utils/api'
import './DocumentPreview.css'

interface DocumentPreviewProps {
  document: Document
  onClose: () => void
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({ document, onClose }) => {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadStats = async () => {
      try {
        const documentStats = await documentApi.getStats(document.id)
        setStats(documentStats)
      } catch (error) {
        console.error('Failed to load document stats:', error)
      } finally {
        setLoading(false)
      }
    }

    loadStats()
  }, [document.id])

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return 'Unknown size'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isProcessed = !!(document.processed_summary && document.step_tasks)

  return (
    <div className="document-preview-overlay" onClick={onClose}>
      <div className="document-preview" onClick={(e) => e.stopPropagation()}>
        <div className="preview-header">
          <div className="preview-title">
            <h2>{document.filename}</h2>
            <div className="preview-status">
              {isProcessed ? (
                <span className="status-badge processed">✅ Processed</span>
              ) : (
                <span className="status-badge unprocessed">⏳ Uploaded</span>
              )}
            </div>
          </div>
          <button onClick={onClose} className="close-button">
            ✕
          </button>
        </div>

        <div className="preview-content">
          <div className="preview-section">
            <h3>Document Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <label>File Size:</label>
                <span>{formatFileSize(document.file_size)}</span>
              </div>
              <div className="info-item">
                <label>Uploaded:</label>
                <span>{formatDate(document.uploaded_at)}</span>
              </div>
              <div className="info-item">
                <label>Content Hash:</label>
                <span className="hash">{document.content_hash.substring(0, 16)}...</span>
              </div>
              {stats && (
                <div className="info-item">
                  <label>Content Length:</label>
                  <span>{stats.content_length} characters</span>
                </div>
              )}
            </div>
          </div>

          {isProcessed && (
            <>
              <div className="preview-section">
                <h3>AI-Generated Summary</h3>
                <div className="summary-content">
                  {typeof document.processed_summary === 'string' 
                    ? document.processed_summary 
                    : document.processed_summary?.text || document.processed_summary?.summary || 'Summary not available'}
                </div>
              </div>

              {document.step_tasks && document.step_tasks.length > 0 && (
                <div className="preview-section">
                  <h3>Generated Onboarding Steps ({document.step_tasks.length})</h3>
                  <div className="tasks-list">
                    {document.step_tasks.map((task: any, index: number) => (
                      <div key={index} className="task-item">
                        <div className="task-header">
                          <span className="task-number">{task.step || index + 1}</span>
                          <span className="task-title">{task.title || `Step ${index + 1}`}</span>
                        </div>
                        {task.description && (
                          <p className="task-description">{task.description}</p>
                        )}
                        {task.estimated_time && (
                          <span className="task-time">⏱️ {task.estimated_time} min</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {!isProcessed && (
            <div className="preview-section">
              <div className="unprocessed-notice">
                <div className="notice-icon">⚙️</div>
                <h3>Document Not Yet Processed</h3>
                <p>
                  This document has been uploaded but hasn't been processed through our AI system yet. 
                  Process it to generate a summary and actionable tasks for onboarding.
                </p>
              </div>
            </div>
          )}

          {loading && (
            <div className="preview-section">
              <div className="loading-stats">
                <div className="loading-spinner"></div>
                <p>Loading document statistics...</p>
              </div>
            </div>
          )}
        </div>

        <div className="preview-actions">
          {isProcessed && (
            <button
              onClick={() => {
                window.location.href = `/onboarding?document=${document.id}`
              }}
              className="action-button primary"
            >
              🚀 Start Onboarding
            </button>
          )}
          <button onClick={onClose} className="action-button secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default DocumentPreview
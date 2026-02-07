import React, { useState } from 'react'
import DocumentUpload from '../components/document/DocumentUpload'
import DocumentList from '../components/document/DocumentList'
import { ProcessedDocument, Document } from '../types/document'
import './Documents.css'

const Documents: React.FC = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)

  const handleUploadSuccess = (document: ProcessedDocument) => {
    // Trigger refresh of document list
    setRefreshTrigger(prev => prev + 1)
  }

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error)
    // Could show a toast notification here
  }

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document)
  }

  return (
    <div className="documents-page">
      <div className="documents-header">
        <h1>Document Management</h1>
        <p>
          Upload your product documentation to create personalized onboarding experiences. 
          Our AI will process your documents to generate summaries and actionable tasks.
        </p>
      </div>

      <div className="documents-content">
        <section className="upload-section">
          <h2>Upload New Document</h2>
          <DocumentUpload
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
            autoProcess={true}
          />
        </section>

        <section className="documents-section">
          <DocumentList
            refreshTrigger={refreshTrigger}
            onDocumentSelect={handleDocumentSelect}
          />
        </section>
      </div>

      {selectedDocument && (
        <div className="selected-document-info">
          <h3>Selected Document</h3>
          <p>{selectedDocument.filename}</p>
          <button
            onClick={() => {
              if (selectedDocument.processed_summary && selectedDocument.step_tasks) {
                window.location.href = `/onboarding?document=${selectedDocument.id}`
              }
            }}
            disabled={!selectedDocument.processed_summary || !selectedDocument.step_tasks}
            className="start-onboarding-button"
          >
            Start Onboarding with This Document
          </button>
        </div>
      )}
    </div>
  )
}

export default Documents
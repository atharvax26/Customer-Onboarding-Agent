import React, { useState, useRef, useCallback } from 'react'
import { useDocuments } from '../../hooks/useApiClient'
import { DocumentUploadState, ProcessedDocument } from '../../types/document'
import './DocumentUpload.css'

interface DocumentUploadProps {
  onUploadSuccess?: (document: ProcessedDocument) => void
  onUploadError?: (error: string) => void
  autoProcess?: boolean
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({
  onUploadSuccess,
  onUploadError,
  autoProcess = true
}) => {
  const { uploadAndProcess, upload, handleError } = useDocuments()
  const [uploadState, setUploadState] = useState<DocumentUploadState>({
    isUploading: false,
    isProcessing: false,
    progress: { loaded: 0, total: 0, percentage: 0 },
    error: undefined,
    success: false
  })
  
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (file: File): string | null => {
    const maxSize = 10 * 1024 * 1024 // 10MB
    const allowedTypes = [
      'text/plain',
      'application/pdf',
      'text/markdown',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]

    if (file.size > maxSize) {
      return 'File size must be less than 10MB'
    }

    if (!allowedTypes.includes(file.type)) {
      return 'Only PDF, text, and Word documents are supported'
    }

    return null
  }

  const handleProgress = useCallback((percentage: number) => {
    setUploadState(prev => ({
      ...prev,
      progress: {
        ...prev.progress,
        percentage
      }
    }))
  }, [])

  const uploadFile = async (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setUploadState(prev => ({
        ...prev,
        error: validationError
      }))
      onUploadError?.(validationError)
      return
    }

    setUploadState({
      isUploading: true,
      isProcessing: autoProcess,
      progress: { loaded: 0, total: file.size, percentage: 0 },
      error: undefined,
      success: false
    })

    try {
      let result
      if (autoProcess) {
        result = await uploadAndProcess(file, handleProgress)
      } else {
        result = await upload(file, handleProgress)
      }

      // Ensure progress reaches 100%
      setUploadState(prev => ({
        ...prev,
        isUploading: false,
        isProcessing: false,
        success: true,
        progress: { ...prev.progress, percentage: 100 }
      }))

      onUploadSuccess?.(result)
      
      // Auto-reset after 3 seconds on success
      setTimeout(() => {
        resetUpload()
      }, 3000)
      
    } catch (error: any) {
      console.error('Upload error:', error)
      
      // Check if it's an authentication error
      if (error.status === 401) {
        const errorMessage = 'Authentication required. Please log in again.'
        setUploadState(prev => ({
          ...prev,
          isUploading: false,
          isProcessing: false,
          error: errorMessage
        }))
        onUploadError?.(errorMessage)
        return
      }
      
      // Check if it's a duplicate document error
      if (error.status === 409) {
        const errorMessage = 'This document has already been uploaded.'
        setUploadState(prev => ({
          ...prev,
          isUploading: false,
          isProcessing: false,
          error: errorMessage
        }))
        onUploadError?.(errorMessage)
        return
      }
      
      const errorMessage = handleError(error)
      setUploadState(prev => ({
        ...prev,
        isUploading: false,
        isProcessing: false,
        error: errorMessage,
        progress: { ...prev.progress, percentage: 0 } // Reset progress on error
      }))
      onUploadError?.(errorMessage)
    }
  }

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setDragActive(true)
    }
  }, [])

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0]
      uploadFile(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      uploadFile(file)
    }
  }

  const handleClick = () => {
    if (!uploadState.isUploading && !uploadState.isProcessing) {
      fileInputRef.current?.click()
    }
  }

  const resetUpload = () => {
    setUploadState({
      isUploading: false,
      isProcessing: false,
      progress: { loaded: 0, total: 0, percentage: 0 },
      error: undefined,
      success: false
    })
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const isActive = uploadState.isUploading || uploadState.isProcessing

  return (
    <div className="document-upload">
      <div
        className={`upload-area ${dragActive ? 'drag-active' : ''} ${isActive ? 'uploading' : ''} ${uploadState.success ? 'success' : ''} ${uploadState.error ? 'error' : ''}`}
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md,.doc,.docx"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          disabled={isActive}
        />

        {!isActive && !uploadState.success && !uploadState.error && (
          <div className="upload-prompt">
            <div className="upload-icon">📄</div>
            <h3>Upload Document</h3>
            <p>Drag and drop your document here, or click to browse</p>
            <p className="file-types">Supports PDF, TXT, MD, DOC, DOCX (max 10MB)</p>
          </div>
        )}

        {isActive && (
          <div className="upload-progress">
            <div className="progress-icon">
              {uploadState.isUploading ? '⬆️' : '⚙️'}
            </div>
            <h3>
              {uploadState.isUploading && uploadState.progress.percentage < 50 
                ? 'Uploading...' 
                : uploadState.progress.percentage >= 50 && uploadState.progress.percentage < 100
                ? 'Processing with AI...'
                : 'Almost done...'}
            </h3>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${uploadState.progress.percentage}%` }}
              />
            </div>
            <p>{Math.round(uploadState.progress.percentage)}% complete</p>
            {uploadState.progress.percentage >= 50 && uploadState.progress.percentage < 100 && (
              <p className="processing-note">
                {uploadState.progress.percentage < 70 
                  ? 'Analyzing document content...'
                  : uploadState.progress.percentage < 90
                  ? 'Generating onboarding steps...'
                  : 'Finalizing...'}
              </p>
            )}
          </div>
        )}

        {uploadState.success && (
          <div className="upload-success">
            <div className="success-icon">✅</div>
            <h3>Upload Successful!</h3>
            <p>Your document has been {autoProcess ? 'processed' : 'uploaded'} successfully</p>
            <button onClick={resetUpload} className="reset-button">
              Upload Another Document
            </button>
          </div>
        )}

        {uploadState.error && (
          <div className="upload-error">
            <div className="error-icon">❌</div>
            <h3>Upload Failed</h3>
            <p>{uploadState.error}</p>
            <button onClick={resetUpload} className="retry-button">
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentUpload
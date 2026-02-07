import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import DocumentUpload from './DocumentUpload'

// Mock the API
jest.mock('../../utils/api', () => ({
  documentApi: {
    uploadAndProcessDocument: jest.fn(),
    uploadDocument: jest.fn()
  }
}))

describe('DocumentUpload', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders upload prompt initially', () => {
    render(<DocumentUpload />)
    
    expect(screen.getByText('Upload Document')).toBeInTheDocument()
    expect(screen.getByText('Drag and drop your document here, or click to browse')).toBeInTheDocument()
    expect(screen.getByText('Supports PDF, TXT, MD, DOC, DOCX (max 10MB)')).toBeInTheDocument()
  })

  test('shows error for invalid file type', async () => {
    const onUploadError = jest.fn()
    render(<DocumentUpload onUploadError={onUploadError} />)
    
    const file = new File(['test content'], 'test.jpg', { type: 'image/jpeg' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    fireEvent.change(input, { target: { files: [file] } })
    
    await waitFor(() => {
      expect(onUploadError).toHaveBeenCalledWith('Only PDF, text, and Word documents are supported')
    })
  })

  test('shows error for file too large', async () => {
    const onUploadError = jest.fn()
    render(<DocumentUpload onUploadError={onUploadError} />)
    
    // Create a file larger than 10MB
    const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.txt', { type: 'text/plain' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    fireEvent.change(input, { target: { files: [largeFile] } })
    
    await waitFor(() => {
      expect(onUploadError).toHaveBeenCalledWith('File size must be less than 10MB')
    })
  })

  test('handles drag and drop', () => {
    render(<DocumentUpload />)
    
    const uploadArea = screen.getByText('Upload Document').closest('.upload-area')
    
    // Test drag enter
    fireEvent.dragEnter(uploadArea!, {
      dataTransfer: {
        items: [{ kind: 'file' }]
      }
    })
    
    expect(uploadArea).toHaveClass('drag-active')
    
    // Test drag leave
    fireEvent.dragLeave(uploadArea!)
    
    expect(uploadArea).not.toHaveClass('drag-active')
  })

  test('calls onUploadSuccess when upload completes', async () => {
    const mockResponse = {
      id: 1,
      filename: 'test.txt',
      summary: 'Test summary',
      tasks: ['Task 1', 'Task 2'],
      processing_time: 1.5
    }
    
    const { documentApi } = require('../../utils/api')
    documentApi.uploadAndProcessDocument.mockResolvedValue(mockResponse)
    
    const onUploadSuccess = jest.fn()
    render(<DocumentUpload onUploadSuccess={onUploadSuccess} />)
    
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    fireEvent.change(input, { target: { files: [file] } })
    
    await waitFor(() => {
      expect(onUploadSuccess).toHaveBeenCalledWith(mockResponse)
    })
  })
})
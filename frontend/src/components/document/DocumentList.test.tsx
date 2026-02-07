import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import DocumentList from './DocumentList'

// Mock the API
jest.mock('../../utils/api', () => ({
  documentApi: {
    getDocuments: jest.fn(),
    processDocument: jest.fn(),
    deleteDocument: jest.fn()
  }
}))

const mockDocuments = [
  {
    id: 1,
    filename: 'test1.pdf',
    file_size: 1024,
    processed_summary: { summary: 'Test summary 1' },
    step_tasks: ['Task 1', 'Task 2'],
    uploaded_at: '2024-01-01T10:00:00Z',
    content_hash: 'hash1'
  },
  {
    id: 2,
    filename: 'test2.txt',
    file_size: 2048,
    processed_summary: null,
    step_tasks: null,
    uploaded_at: '2024-01-02T10:00:00Z',
    content_hash: 'hash2'
  }
]

describe('DocumentList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders loading state initially', () => {
    const { documentApi } = require('../../utils/api')
    documentApi.getDocuments.mockImplementation(() => new Promise(() => {})) // Never resolves
    
    render(<DocumentList />)
    
    expect(screen.getByText('Loading documents...')).toBeInTheDocument()
  })

  test('renders documents when loaded', async () => {
    const { documentApi } = require('../../utils/api')
    documentApi.getDocuments.mockResolvedValue(mockDocuments)
    
    render(<DocumentList />)
    
    await waitFor(() => {
      expect(screen.getByText('test1.pdf')).toBeInTheDocument()
      expect(screen.getByText('test2.txt')).toBeInTheDocument()
    })
    
    // Check processed status
    expect(screen.getByText('✅ Processed')).toBeInTheDocument()
    expect(screen.getByText('⏳ Uploaded')).toBeInTheDocument()
  })

  test('renders empty state when no documents', async () => {
    const { documentApi } = require('../../utils/api')
    documentApi.getDocuments.mockResolvedValue([])
    
    render(<DocumentList />)
    
    await waitFor(() => {
      expect(screen.getByText('No Documents Yet')).toBeInTheDocument()
      expect(screen.getByText('Upload your first document to get started with onboarding flows.')).toBeInTheDocument()
    })
  })

  test('handles error state', async () => {
    const { documentApi } = require('../../utils/api')
    documentApi.getDocuments.mockRejectedValue(new Error('Failed to load'))
    
    render(<DocumentList />)
    
    await waitFor(() => {
      expect(screen.getByText('Error Loading Documents')).toBeInTheDocument()
      expect(screen.getByText('Failed to load')).toBeInTheDocument()
    })
  })

  test('processes unprocessed document', async () => {
    const { documentApi } = require('../../utils/api')
    documentApi.getDocuments.mockResolvedValue(mockDocuments)
    documentApi.processDocument.mockResolvedValue({
      id: 2,
      filename: 'test2.txt',
      summary: 'Processed summary',
      tasks: ['New task'],
      processing_time: 2.0
    })
    
    render(<DocumentList />)
    
    await waitFor(() => {
      expect(screen.getByText('test2.txt')).toBeInTheDocument()
    })
    
    const processButton = screen.getByText('⚙️ Process')
    fireEvent.click(processButton)
    
    await waitFor(() => {
      expect(documentApi.processDocument).toHaveBeenCalledWith(2)
    })
  })

  test('deletes document with confirmation', async () => {
    const { documentApi } = require('../../utils/api')
    documentApi.getDocuments.mockResolvedValue(mockDocuments)
    documentApi.deleteDocument.mockResolvedValue({})
    
    // Mock window.confirm
    const originalConfirm = window.confirm
    window.confirm = jest.fn(() => true)
    
    render(<DocumentList />)
    
    await waitFor(() => {
      expect(screen.getByText('test1.pdf')).toBeInTheDocument()
    })
    
    const deleteButtons = screen.getAllByText('🗑️ Delete')
    fireEvent.click(deleteButtons[0])
    
    await waitFor(() => {
      expect(documentApi.deleteDocument).toHaveBeenCalledWith(1)
    })
    
    // Restore window.confirm
    window.confirm = originalConfirm
  })

  test('calls onDocumentSelect when view button is clicked', async () => {
    const { documentApi } = require('../../utils/api')
    documentApi.getDocuments.mockResolvedValue(mockDocuments)
    
    const onDocumentSelect = jest.fn()
    render(<DocumentList onDocumentSelect={onDocumentSelect} />)
    
    await waitFor(() => {
      expect(screen.getByText('test1.pdf')).toBeInTheDocument()
    })
    
    const viewButtons = screen.getAllByText('👁️ View')
    fireEvent.click(viewButtons[0])
    
    expect(onDocumentSelect).toHaveBeenCalledWith(mockDocuments[0])
  })
})
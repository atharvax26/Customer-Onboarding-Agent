export interface Document {
  id: number
  filename: string
  file_size?: number
  processed_summary?: Record<string, any>
  step_tasks?: string[]
  uploaded_at: string
  content_hash: string
}

export interface ProcessedDocument {
  id: number
  filename: string
  summary: string
  tasks: string[]
  processing_time: number
}

export interface DocumentUploadResponse {
  message: string
  document_id: number
  processing_status: string
}

export interface DocumentStats {
  file_size: number
  content_length: number
  processing_status: string
  upload_date: string
  last_processed?: string
}

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface DocumentUploadState {
  isUploading: boolean
  isProcessing: boolean
  progress: UploadProgress
  error?: string
  success?: boolean
}
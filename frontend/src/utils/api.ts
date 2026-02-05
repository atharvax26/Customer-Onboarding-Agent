import { OnboardingSession, OnboardingStep, OnboardingProgress, InteractionEvent, InteractionTrackingResponse } from '../types/onboarding'
import { getStoredToken } from './auth'

const API_BASE_URL = '/api'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

const createAuthHeaders = () => {
  const token = getStoredToken()
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}

const handleApiResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(response.status, errorData.detail || 'Request failed')
  }
  return response.json()
}

// Onboarding API functions
export const onboardingApi = {
  async startOnboarding(documentId: number): Promise<OnboardingSession> {
    const response = await fetch(`${API_BASE_URL}/onboarding/start`, {
      method: 'POST',
      headers: createAuthHeaders(),
      body: JSON.stringify({ document_id: documentId })
    })
    return handleApiResponse(response)
  },

  async getCurrentStep(sessionId: number): Promise<OnboardingStep> {
    const response = await fetch(`${API_BASE_URL}/onboarding/current-step/${sessionId}`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async advanceStep(sessionId: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/onboarding/advance-step/${sessionId}`, {
      method: 'POST',
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getProgress(sessionId: number): Promise<OnboardingProgress> {
    const response = await fetch(`${API_BASE_URL}/onboarding/progress/${sessionId}`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getUserSessions(): Promise<OnboardingSession[]> {
    const response = await fetch(`${API_BASE_URL}/onboarding/sessions`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getSessionDetails(sessionId: number): Promise<OnboardingSession> {
    const response = await fetch(`${API_BASE_URL}/onboarding/session/${sessionId}`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  }
}

// Engagement tracking API functions
export const engagementApi = {
  async trackInteraction(event: InteractionEvent): Promise<InteractionTrackingResponse> {
    const response = await fetch(`${API_BASE_URL}/engagement/track-interaction`, {
      method: 'POST',
      headers: createAuthHeaders(),
      body: JSON.stringify(event)
    })
    return handleApiResponse(response)
  },

  async getEngagementScore(userId?: number): Promise<any> {
    const url = userId 
      ? `${API_BASE_URL}/engagement/score/${userId}`
      : `${API_BASE_URL}/engagement/score`
    
    const response = await fetch(url, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  }
}

// Document API functions
export const documentApi = {
  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    const token = getStoredToken()
    const response = await fetch(`${API_BASE_URL}/scaledown/upload`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: formData
    })
    return handleApiResponse(response)
  },

  async getDocuments(): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/scaledown/documents`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  }
}

export { ApiError }
export interface OnboardingSession {
  id: number
  user_id: number
  document_id: number
  status: 'active' | 'completed' | 'abandoned'
  current_step: number
  total_steps: number
  started_at: string
  completed_at?: string
  session_metadata?: Record<string, any>
}

export interface OnboardingStep {
  step_number: number
  total_steps: number
  title: string
  content: string
  description?: string
  tasks: string[]
  subtasks?: string[]
  estimated_time: number
  tip?: string
}

export interface StepCompletion {
  id: number
  session_id: number
  step_number: number
  started_at: string
  completed_at?: string
  time_spent_seconds?: number
  step_data?: Record<string, any>
}

export interface OnboardingProgress {
  session_id: number
  current_step: number
  total_steps: number
  completion_percentage: number
  steps_completed: StepCompletion[]
}

export interface InteractionEvent {
  event_type: string
  element_id?: string
  element_type?: string
  page_url: string
  timestamp: string
  additional_data?: Record<string, any>
}

export interface InteractionTrackingResponse {
  success: boolean
  message: string
}
export interface HelpMessage {
  message_id: string
  content: string
  message_type: string
  context: Record<string, any>
  dismissible: boolean
}

export interface HelpMessageResponse {
  help_message: HelpMessage
  triggered_at: string
}

export interface InterventionLog {
  id: number
  user_id: number
  session_id?: number
  intervention_type: string
  message_content?: string
  triggered_at: string
  was_helpful?: boolean
}

export interface InterventionFeedback {
  intervention_id: number
  was_helpful: boolean
}
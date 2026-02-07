export interface ActivationMetrics {
  total_users: number
  activated_users: number
  activation_rate: number
  role_breakdown: Record<string, Record<string, number>>
}

export interface DropoffData {
  step_number: number
  step_title: string
  started_count: number
  completed_count: number
  completion_rate: number
  average_time_spent?: number
}

export interface DropoffAnalysisResponse {
  overall_completion_rate: number
  steps: DropoffData[]
}

export interface TrendDataPoint {
  date: string
  value: number
  count: number
}

export interface TrendData {
  metric_name: string
  data_points: TrendDataPoint[]
  trend_direction: 'up' | 'down' | 'stable'
}

export interface AnalyticsFilters {
  role?: 'Developer' | 'Business_User' | 'Admin'
  start_date?: string
  end_date?: string
  user_id?: number
}

export interface DashboardData {
  activation_metrics: ActivationMetrics
  recent_dropoff_analysis: DropoffAnalysisResponse
  engagement_trends: TrendData[]
  total_sessions: number
  active_sessions: number
  recent_interventions: number
}

export interface RealTimeMetrics {
  active_sessions: number
  average_engagement_24h: number
  total_interventions_today: number
  last_updated: string
}

export interface MetricsSummary {
  activation_rate: number
  total_users: number
  overall_completion_rate: number
  active_sessions: number
  average_engagement: number
  role_filter?: string
  generated_at: string
}
import { 
  ActivationMetrics, 
  DropoffAnalysisResponse, 
  TrendData, 
  DashboardData, 
  RealTimeMetrics,
  MetricsSummary,
  AnalyticsFilters 
} from '../types/analytics'
import { getStoredToken } from './auth'
import { ApiError } from '../services/apiClient'

const API_BASE_URL = '/api'

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

const buildQueryParams = (filters: AnalyticsFilters): string => {
  const params = new URLSearchParams()
  
  if (filters.role) params.append('role', filters.role)
  if (filters.start_date) params.append('start_date', filters.start_date)
  if (filters.end_date) params.append('end_date', filters.end_date)
  if (filters.user_id) params.append('user_id', filters.user_id.toString())
  
  return params.toString()
}

export const analyticsApi = {
  async getActivationRates(filters: AnalyticsFilters = {}): Promise<ActivationMetrics> {
    const queryParams = buildQueryParams(filters)
    const url = `${API_BASE_URL}/analytics/activation-rates${queryParams ? `?${queryParams}` : ''}`
    
    const response = await fetch(url, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getDropoffAnalysis(filters: AnalyticsFilters = {}): Promise<DropoffAnalysisResponse> {
    const queryParams = buildQueryParams(filters)
    const url = `${API_BASE_URL}/analytics/dropoff-analysis${queryParams ? `?${queryParams}` : ''}`
    
    const response = await fetch(url, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getEngagementTrends(userId?: number, daysBack: number = 30): Promise<TrendData> {
    const params = new URLSearchParams()
    if (userId) params.append('user_id', userId.toString())
    params.append('days_back', daysBack.toString())
    
    const response = await fetch(`${API_BASE_URL}/analytics/engagement-trends?${params.toString()}`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getDashboardData(): Promise<DashboardData> {
    const response = await fetch(`${API_BASE_URL}/analytics/dashboard`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getRealTimeMetrics(): Promise<RealTimeMetrics> {
    const response = await fetch(`${API_BASE_URL}/analytics/real-time-metrics`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getMetricsSummary(role?: string): Promise<MetricsSummary> {
    const params = role ? `?role=${role}` : ''
    const response = await fetch(`${API_BASE_URL}/analytics/metrics/summary${params}`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async exportAnalyticsData(filters: AnalyticsFilters = {}, format: string = 'json'): Promise<any> {
    const queryParams = buildQueryParams(filters)
    const params = new URLSearchParams(queryParams)
    params.append('export_format', format)
    
    const response = await fetch(`${API_BASE_URL}/analytics/export?${params.toString()}`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async refreshMetricsCache(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/analytics/metrics/refresh`, {
      method: 'POST',
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getAvailableRoles(): Promise<{ available_roles: string[], user_role: string, access_level: string }> {
    const response = await fetch(`${API_BASE_URL}/analytics/filters/roles`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  },

  async getUserAnalytics(userId: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/analytics/user-analytics/${userId}`, {
      headers: createAuthHeaders()
    })
    return handleApiResponse(response)
  }
}
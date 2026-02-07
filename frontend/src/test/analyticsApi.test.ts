import { analyticsApi } from '../utils/analyticsApi'
import { AnalyticsFilters } from '../types/analytics'

// Mock fetch for testing
global.fetch = jest.fn()

const mockFetch = fetch as jest.MockedFunction<typeof fetch>

describe('Analytics API', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  test('getActivationRates makes correct API call', async () => {
    const mockResponse = {
      total_users: 100,
      activated_users: 75,
      activation_rate: 75.0,
      role_breakdown: {}
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response)

    const filters: AnalyticsFilters = { role: 'Developer' }
    const result = await analyticsApi.getActivationRates(filters)

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/analytics/activation-rates?role=Developer',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    )
    expect(result).toEqual(mockResponse)
  })

  test('getDropoffAnalysis makes correct API call', async () => {
    const mockResponse = {
      overall_completion_rate: 68.5,
      steps: []
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response)

    const filters: AnalyticsFilters = { start_date: '2024-01-01' }
    const result = await analyticsApi.getDropoffAnalysis(filters)

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/analytics/dropoff-analysis?start_date=2024-01-01',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    )
    expect(result).toEqual(mockResponse)
  })

  test('getEngagementTrends makes correct API call', async () => {
    const mockResponse = {
      metric_name: 'engagement_score',
      data_points: [],
      trend_direction: 'stable'
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response)

    const result = await analyticsApi.getEngagementTrends(123, 7)

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/analytics/engagement-trends?user_id=123&days_back=7',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    )
    expect(result).toEqual(mockResponse)
  })

  test('getDashboardData makes correct API call', async () => {
    const mockResponse = {
      activation_metrics: { total_users: 0, activated_users: 0, activation_rate: 0, role_breakdown: {} },
      recent_dropoff_analysis: { overall_completion_rate: 0, steps: [] },
      engagement_trends: [],
      total_sessions: 0,
      active_sessions: 0,
      recent_interventions: 0
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response)

    const result = await analyticsApi.getDashboardData()

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/analytics/dashboard',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    )
    expect(result).toEqual(mockResponse)
  })

  test('handles API errors correctly', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: 'Not found' }),
    } as Response)

    await expect(analyticsApi.getActivationRates()).rejects.toThrow('Not found')
  })

  test('buildQueryParams works correctly', async () => {
    const mockResponse = { total_users: 0, activated_users: 0, activation_rate: 0, role_breakdown: {} }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response)

    const filters: AnalyticsFilters = {
      role: 'Business_User',
      start_date: '2024-01-01',
      end_date: '2024-01-31'
    }

    await analyticsApi.getActivationRates(filters)

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/analytics/activation-rates?role=Business_User&start_date=2024-01-01&end_date=2024-01-31',
      expect.any(Object)
    )
  })
})
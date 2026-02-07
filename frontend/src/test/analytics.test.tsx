import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ActivationRateChart, DropoffAnalysis, EngagementTrends, MetricCard } from '../components/analytics'
import { ActivationMetrics, DropoffAnalysisResponse, TrendData } from '../types/analytics'

// Mock data for testing
const mockActivationData: ActivationMetrics = {
  total_users: 100,
  activated_users: 75,
  activation_rate: 75.0,
  role_breakdown: {
    'Developer': { total: 50, activated: 40 },
    'Business_User': { total: 30, activated: 25 },
    'Admin': { total: 20, activated: 10 }
  }
}

const mockDropoffData: DropoffAnalysisResponse = {
  overall_completion_rate: 68.5,
  steps: [
    {
      step_number: 1,
      step_title: 'Welcome',
      started_count: 100,
      completed_count: 95,
      completion_rate: 95.0,
      average_time_spent: 120
    },
    {
      step_number: 2,
      step_title: 'Setup',
      started_count: 95,
      completed_count: 80,
      completion_rate: 84.2,
      average_time_spent: 180
    }
  ]
}

const mockEngagementData: TrendData[] = [{
  metric_name: 'engagement_score',
  data_points: [
    { date: '2024-01-01', value: 65, count: 10 },
    { date: '2024-01-02', value: 70, count: 12 },
    { date: '2024-01-03', value: 68, count: 8 }
  ],
  trend_direction: 'up'
}]

describe('Analytics Components', () => {
  test('MetricCard renders correctly', () => {
    render(
      <MetricCard
        title="Test Metric"
        value="42"
        subtitle="Test subtitle"
        trend="up"
        trendValue="+5%"
        color="blue"
      />
    )
    
    expect(screen.getByText('Test Metric')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('Test subtitle')).toBeInTheDocument()
    expect(screen.getByText('+5%')).toBeInTheDocument()
  })

  test('ActivationRateChart renders with data', () => {
    render(<ActivationRateChart data={mockActivationData} />)
    
    expect(screen.getByText('Total Users')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
    expect(screen.getByText('Activated Users')).toBeInTheDocument()
    expect(screen.getByText('75')).toBeInTheDocument()
  })

  test('ActivationRateChart shows loading state', () => {
    render(<ActivationRateChart data={mockActivationData} isLoading={true} />)
    
    expect(screen.getByText('Loading activation rates...')).toBeInTheDocument()
  })

  test('DropoffAnalysis renders with data', () => {
    render(<DropoffAnalysis data={mockDropoffData} />)
    
    expect(screen.getByText('Overall Completion')).toBeInTheDocument()
    expect(screen.getByText('68.5%')).toBeInTheDocument()
    expect(screen.getByText('Step-by-Step Analysis')).toBeInTheDocument()
  })

  test('DropoffAnalysis shows loading state', () => {
    render(<DropoffAnalysis data={mockDropoffData} isLoading={true} />)
    
    expect(screen.getByText('Loading drop-off analysis...')).toBeInTheDocument()
  })

  test('EngagementTrends renders with data', () => {
    render(<EngagementTrends data={mockEngagementData} />)
    
    expect(screen.getByText('Current Score')).toBeInTheDocument()
    expect(screen.getByText('Average Score')).toBeInTheDocument()
    expect(screen.getByText('Engagement Score Over Time')).toBeInTheDocument()
  })

  test('EngagementTrends shows loading state', () => {
    render(<EngagementTrends data={mockEngagementData} isLoading={true} />)
    
    expect(screen.getByText('Loading engagement trends...')).toBeInTheDocument()
  })

  test('EngagementTrends shows empty state', () => {
    render(<EngagementTrends data={[]} />)
    
    expect(screen.getByText('No engagement data available')).toBeInTheDocument()
  })
})
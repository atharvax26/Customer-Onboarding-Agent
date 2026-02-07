# Analytics Dashboard Components

This directory contains all the visualization components for the Customer Onboarding Agent analytics dashboard.

## Components Overview

### Core Chart Components

#### `BarChart.tsx`
- **Purpose**: Renders horizontal bar charts for categorical data
- **Props**: 
  - `data`: Array of `{label, value, color?}` objects
  - `title`: Chart title
  - `height?`: Chart height in pixels (default: 300)
  - `showValues?`: Whether to display values on bars (default: true)
  - `maxValue?`: Override maximum value for scaling

#### `LineChart.tsx`
- **Purpose**: Renders line charts for time-series data
- **Props**:
  - `data`: Array of `{label, value, date?}` objects
  - `title`: Chart title
  - `height?`: Chart height in pixels (default: 300)
  - `color?`: Line color (default: '#3b82f6')
  - `showDots?`: Whether to show data points (default: true)
  - `maxValue?`: Override maximum value for scaling

#### `MetricCard.tsx`
- **Purpose**: Displays key metrics with optional trend indicators
- **Props**:
  - `title`: Metric title
  - `value`: Main metric value (string or number)
  - `subtitle?`: Additional description
  - `trend?`: 'up' | 'down' | 'stable'
  - `trendValue?`: Trend description text
  - `color?`: Card accent color
  - `icon?`: React node for icon display

### Analytics-Specific Components

#### `ActivationRateChart.tsx`
- **Purpose**: Displays user activation metrics and role breakdown
- **Features**:
  - Overall activation rate metrics
  - Role-based activation breakdown chart
  - Detailed role breakdown table
  - Loading and error states
- **Requirements**: Validates Requirements 5.1, 5.2

#### `DropoffAnalysis.tsx`
- **Purpose**: Shows step-by-step completion and drop-off analysis
- **Features**:
  - Overall completion rate metrics
  - Step completion rate charts
  - User count progression charts
  - Detailed step analysis table
  - Insights and recommendations
- **Requirements**: Validates Requirements 5.1, 5.2, 5.3

#### `EngagementTrends.tsx`
- **Purpose**: Visualizes engagement score trends over time
- **Features**:
  - Current and average engagement scores
  - Time-series line chart
  - Trend analysis and recommendations
  - Data summary statistics
- **Requirements**: Validates Requirements 5.4, 5.5

#### `RealTimeMetrics.tsx`
- **Purpose**: Displays live system metrics with auto-refresh
- **Features**:
  - Active sessions count
  - 24-hour average engagement
  - Daily intervention count
  - Auto-refresh functionality (30-second intervals)
  - Manual refresh capability
- **Requirements**: Validates Requirements 5.4, 5.5

#### `FilterControls.tsx`
- **Purpose**: Provides filtering controls for analytics data
- **Features**:
  - Role-based filtering
  - Date range selection
  - Active filter display
  - Clear filters functionality
  - Refresh data capability
- **Requirements**: Validates Requirements 5.5

## Usage Example

```tsx
import React, { useState, useEffect } from 'react'
import {
  FilterControls,
  ActivationRateChart,
  DropoffAnalysis,
  EngagementTrends,
  RealTimeMetrics
} from '../components/analytics'
import { analyticsApi } from '../utils/analyticsApi'

const AnalyticsDashboard: React.FC = () => {
  const [filters, setFilters] = useState({})
  const [data, setData] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      const dashboardData = await analyticsApi.getDashboardData()
      setData(dashboardData)
    }
    fetchData()
  }, [filters])

  return (
    <div>
      <FilterControls
        filters={filters}
        onFiltersChange={setFilters}
        onRefresh={() => window.location.reload()}
      />
      
      <RealTimeMetrics autoRefresh={true} />
      
      {data && (
        <>
          <ActivationRateChart data={data.activation_metrics} />
          <DropoffAnalysis data={data.recent_dropoff_analysis} />
          <EngagementTrends data={data.engagement_trends} />
        </>
      )}
    </div>
  )
}
```

## Styling

All components use CSS modules with responsive design:
- Mobile-first approach
- Grid layouts for responsive behavior
- Consistent color scheme and spacing
- Hover effects and transitions
- Loading states and error handling

## Data Flow

1. **FilterControls** → Updates filters → Triggers data refresh
2. **Analytics API** → Fetches filtered data → Updates component state
3. **Chart Components** → Render visualizations → Display insights
4. **RealTimeMetrics** → Auto-refreshes → Shows live data

## Testing

Components include comprehensive tests:
- Unit tests for individual components
- Integration tests for API interactions
- Mock data for consistent testing
- Loading and error state testing

## Performance Considerations

- Charts use CSS-based rendering for better performance
- Real-time components use efficient polling intervals
- Data is cached to minimize API calls
- Responsive design reduces mobile rendering overhead

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox support required
- ES6+ JavaScript features used
- No external chart library dependencies
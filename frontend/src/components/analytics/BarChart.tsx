import React from 'react'
import './BarChart.css'

interface BarChartData {
  label: string
  value: number
  color?: string
}

interface BarChartProps {
  data: BarChartData[]
  title: string
  height?: number
  showValues?: boolean
  maxValue?: number
}

const BarChart: React.FC<BarChartProps> = ({ 
  data, 
  title, 
  height = 300, 
  showValues = true,
  maxValue 
}) => {
  const max = maxValue || Math.max(...data.map(d => d.value))
  const chartHeight = height - 60 // Account for title and labels

  return (
    <div className="bar-chart">
      <h3 className="chart-title">{title}</h3>
      <div className="chart-container" style={{ height: chartHeight }}>
        <div className="y-axis">
          <div className="y-axis-label">{max}</div>
          <div className="y-axis-label">{Math.round(max * 0.75)}</div>
          <div className="y-axis-label">{Math.round(max * 0.5)}</div>
          <div className="y-axis-label">{Math.round(max * 0.25)}</div>
          <div className="y-axis-label">0</div>
        </div>
        <div className="bars-container">
          {data.map((item, index) => {
            const barHeight = max > 0 ? (item.value / max) * (chartHeight - 40) : 0
            return (
              <div key={index} className="bar-wrapper">
                <div 
                  className="bar" 
                  style={{ 
                    height: `${barHeight}px`,
                    backgroundColor: item.color || '#3b82f6'
                  }}
                >
                  {showValues && (
                    <div className="bar-value">{item.value}</div>
                  )}
                </div>
                <div className="bar-label">{item.label}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default BarChart
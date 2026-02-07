import React from 'react'
import './LineChart.css'

interface LineChartData {
  label: string
  value: number
  date?: string
}

interface LineChartProps {
  data: LineChartData[]
  title: string
  height?: number
  color?: string
  showDots?: boolean
  maxValue?: number
}

const LineChart: React.FC<LineChartProps> = ({ 
  data, 
  title, 
  height = 300, 
  color = '#3b82f6',
  showDots = true,
  maxValue 
}) => {
  const max = maxValue || Math.max(...data.map(d => d.value))
  const min = Math.min(...data.map(d => d.value))
  const chartHeight = height - 80 // Account for title and labels
  const chartWidth = 400 // Fixed width for SVG

  // Generate SVG path for the line
  const generatePath = () => {
    if (data.length === 0) return ''
    
    const points = data.map((item, index) => {
      const x = (index / (data.length - 1)) * chartWidth
      const y = max > min ? ((max - item.value) / (max - min)) * chartHeight : chartHeight / 2
      return `${x},${y}`
    })
    
    return `M ${points.join(' L ')}`
  }

  // Generate points for dots
  const generateDots = () => {
    return data.map((item, index) => {
      const x = (index / (data.length - 1)) * chartWidth
      const y = max > min ? ((max - item.value) / (max - min)) * chartHeight : chartHeight / 2
      return { x, y, value: item.value, label: item.label }
    })
  }

  const path = generatePath()
  const dots = generateDots()

  return (
    <div className="line-chart">
      <h3 className="chart-title">{title}</h3>
      <div className="chart-container">
        <div className="y-axis">
          <div className="y-axis-label">{max}</div>
          <div className="y-axis-label">{Math.round(max * 0.75)}</div>
          <div className="y-axis-label">{Math.round(max * 0.5)}</div>
          <div className="y-axis-label">{Math.round(max * 0.25)}</div>
          <div className="y-axis-label">{min}</div>
        </div>
        <div className="chart-area">
          <svg width={chartWidth} height={chartHeight} className="line-svg">
            {/* Grid lines */}
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Line */}
            {path && (
              <path
                d={path}
                fill="none"
                stroke={color}
                strokeWidth="2"
                className="line-path"
              />
            )}
            
            {/* Dots */}
            {showDots && dots.map((dot, index) => (
              <g key={index}>
                <circle
                  cx={dot.x}
                  cy={dot.y}
                  r="4"
                  fill={color}
                  className="line-dot"
                />
                <title>{`${dot.label}: ${dot.value}`}</title>
              </g>
            ))}
          </svg>
          
          {/* X-axis labels */}
          <div className="x-axis">
            {data.map((item, index) => (
              <div 
                key={index} 
                className="x-axis-label"
                style={{ left: `${(index / (data.length - 1)) * 100}%` }}
              >
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default LineChart
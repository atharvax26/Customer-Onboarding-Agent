import React, { useState, useEffect } from 'react'
import { AnalyticsFilters } from '../../types/analytics'
import { analyticsApi } from '../../utils/analyticsApi'
import './FilterControls.css'

interface FilterControlsProps {
  filters: AnalyticsFilters
  onFiltersChange: (filters: AnalyticsFilters) => void
  onRefresh?: () => void
  isLoading?: boolean
}

const FilterControls: React.FC<FilterControlsProps> = ({
  filters,
  onFiltersChange,
  onRefresh,
  isLoading = false
}) => {
  const [availableRoles, setAvailableRoles] = useState<string[]>([])
  const [userRole, setUserRole] = useState<string>('')

  useEffect(() => {
    loadAvailableRoles()
  }, [])

  const loadAvailableRoles = async () => {
    try {
      const response = await analyticsApi.getAvailableRoles()
      setAvailableRoles(response.available_roles)
      setUserRole(response.user_role)
    } catch (error) {
      console.error('Failed to load available roles:', error)
      // Set default roles if API fails
      setAvailableRoles(['Developer', 'Business_User', 'Admin'])
    }
  }

  const handleRoleChange = (role: string) => {
    onFiltersChange({
      ...filters,
      role: role === 'all' ? undefined : role as any
    })
  }

  const handleDateChange = (field: 'start_date' | 'end_date', value: string) => {
    onFiltersChange({
      ...filters,
      [field]: value || undefined
    })
  }

  const clearFilters = () => {
    onFiltersChange({})
  }

  const formatDateForInput = (dateString?: string) => {
    if (!dateString) return ''
    return new Date(dateString).toISOString().split('T')[0]
  }

  const hasActiveFilters = filters.role || filters.start_date || filters.end_date

  return (
    <div className="filter-controls">
      <div className="filter-section">
        <h3 className="filter-title">Filters</h3>
        
        <div className="filter-row">
          <div className="filter-group">
            <label htmlFor="role-filter" className="filter-label">
              User Role
            </label>
            <select
              id="role-filter"
              value={filters.role || 'all'}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Roles</option>
              {availableRoles.map(role => (
                <option key={role} value={role}>
                  {role.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="start-date" className="filter-label">
              Start Date
            </label>
            <input
              id="start-date"
              type="date"
              value={formatDateForInput(filters.start_date)}
              onChange={(e) => handleDateChange('start_date', e.target.value)}
              className="filter-input"
            />
          </div>

          <div className="filter-group">
            <label htmlFor="end-date" className="filter-label">
              End Date
            </label>
            <input
              id="end-date"
              type="date"
              value={formatDateForInput(filters.end_date)}
              onChange={(e) => handleDateChange('end_date', e.target.value)}
              className="filter-input"
            />
          </div>
        </div>

        <div className="filter-actions">
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="filter-button filter-button-secondary"
              disabled={isLoading}
            >
              Clear Filters
            </button>
          )}
          
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="filter-button filter-button-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Refreshing...' : 'Refresh Data'}
            </button>
          )}
        </div>

        {hasActiveFilters && (
          <div className="active-filters">
            <span className="active-filters-label">Active filters:</span>
            {filters.role && (
              <span className="filter-tag">
                Role: {filters.role.replace('_', ' ')}
              </span>
            )}
            {filters.start_date && (
              <span className="filter-tag">
                From: {new Date(filters.start_date).toLocaleDateString()}
              </span>
            )}
            {filters.end_date && (
              <span className="filter-tag">
                To: {new Date(filters.end_date).toLocaleDateString()}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default FilterControls
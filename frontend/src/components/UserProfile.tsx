import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

const UserProfile: React.FC = () => {
  const { user, logout } = useAuth()
  const [showDetails, setShowDetails] = useState(false)

  if (!user) {
    return null
  }

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout()
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getRoleBadgeClass = (role: string) => {
    switch (role) {
      case 'Admin':
        return 'role-badge role-admin'
      case 'Developer':
        return 'role-badge role-developer'
      case 'Business_User':
        return 'role-badge role-business'
      default:
        return 'role-badge'
    }
  }

  return (
    <div className="user-profile">
      <div className="profile-header">
        <div className="profile-info">
          <h3>{user.email}</h3>
          <span className={getRoleBadgeClass(user.role)}>
            {user.role.replace('_', ' ')}
          </span>
        </div>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="btn btn-outline"
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
      </div>

      {showDetails && (
        <div className="profile-details">
          <div className="detail-item">
            <label>User ID:</label>
            <span>{user.id}</span>
          </div>
          <div className="detail-item">
            <label>Account Created:</label>
            <span>{formatDate(user.created_at)}</span>
          </div>
          {user.last_login && (
            <div className="detail-item">
              <label>Last Login:</label>
              <span>{formatDate(user.last_login)}</span>
            </div>
          )}
          <div className="profile-actions">
            <button onClick={handleLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserProfile
import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import RoleBasedComponent from './RoleBasedComponent'

const Navigation: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
    setShowUserMenu(false)
  }

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <Link to="/" className="brand-link">
          Customer Onboarding Agent
        </Link>
      </div>
      
      <div className="nav-links">
        <Link to="/" className="nav-link">Home</Link>
        
        {isAuthenticated ? (
          <>
            <Link to="/onboarding" className="nav-link">Onboarding</Link>
            
            {/* Role-based navigation */}
            <RoleBasedComponent allowedRoles={['Admin']}>
              <Link to="/analytics" className="nav-link">Analytics</Link>
            </RoleBasedComponent>
            
            <div className="user-menu-container">
              <button
                className="user-menu-trigger"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                <span className="user-email">{user?.email}</span>
                <span className="user-role">({user?.role?.replace('_', ' ')})</span>
                <span className="dropdown-arrow">▼</span>
              </button>
              
              {showUserMenu && (
                <div className="user-dropdown">
                  <div className="user-info">
                    <div className="user-details">
                      <strong>{user?.email}</strong>
                      <small>{user?.role?.replace('_', ' ')}</small>
                    </div>
                  </div>
                  <hr />
                  <button onClick={handleLogout} className="dropdown-item">
                    Logout
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">Login</Link>
            <Link to="/register" className="btn btn-primary">Register</Link>
          </>
        )}
      </div>
    </nav>
  )
}

export default Navigation

export default Navigation
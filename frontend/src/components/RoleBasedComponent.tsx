import React from 'react'
import { useAuth, User } from '../contexts/AuthContext'

interface RoleBasedComponentProps {
  allowedRoles: User['role'][]
  children: React.ReactNode
  fallback?: React.ReactNode
}

const RoleBasedComponent: React.FC<RoleBasedComponentProps> = ({
  allowedRoles,
  children,
  fallback = null
}) => {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated || !user) {
    return <>{fallback}</>
  }

  if (!allowedRoles.includes(user.role)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

export default RoleBasedComponent
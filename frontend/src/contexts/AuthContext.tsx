import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { 
  isTokenExpired, 
  clearAuthStorage, 
  getStoredToken, 
  getStoredUser,
  TOKEN_STORAGE_KEY,
  USER_STORAGE_KEY
} from '../utils/auth'

export interface User {
  id: number
  email: string
  role: 'Developer' | 'Business_User' | 'Admin'
  created_at: string
  last_login?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, role: User['role']) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for stored token on app initialization
    const storedToken = getStoredToken()
    const storedUser = getStoredUser()
    
    if (storedToken && storedUser) {
      // Check if token is expired
      if (isTokenExpired(storedToken)) {
        clearAuthStorage()
      } else {
        setToken(storedToken)
        setUser(storedUser)
      }
    }
    
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string): Promise<void> => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      const data = await response.json()
      
      setToken(data.access_token)
      setUser(data.user)
      
      localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user))
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const register = async (email: string, password: string, role: User['role']): Promise<void> => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, role }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Registration failed')
      }

      const data = await response.json()
      
      setToken(data.access_token)
      setUser(data.user)
      
      localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token)
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user))
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    clearAuthStorage()
  }

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    isAuthenticated: !!user && !!token,
    isLoading,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
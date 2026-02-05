// JWT Token utilities
export interface DecodedToken {
  sub: string // user id
  email: string
  role: string
  exp: number // expiration timestamp
  iat: number // issued at timestamp
}

export const decodeToken = (token: string): DecodedToken | null => {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch (error) {
    console.error('Error decoding token:', error)
    return null
  }
}

export const isTokenExpired = (token: string): boolean => {
  const decoded = decodeToken(token)
  if (!decoded) return true
  
  const currentTime = Date.now() / 1000
  return decoded.exp < currentTime
}

export const getTokenExpirationTime = (token: string): Date | null => {
  const decoded = decodeToken(token)
  if (!decoded) return null
  
  return new Date(decoded.exp * 1000)
}

export const shouldRefreshToken = (token: string): boolean => {
  const decoded = decodeToken(token)
  if (!decoded) return false
  
  const currentTime = Date.now() / 1000
  const timeUntilExpiry = decoded.exp - currentTime
  
  // Refresh if token expires in less than 5 minutes
  return timeUntilExpiry < 300
}

// API request helper with token
export const createAuthenticatedRequest = (token: string) => {
  return {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  }
}

// Storage helpers
export const TOKEN_STORAGE_KEY = 'auth_token'
export const USER_STORAGE_KEY = 'auth_user'

export const clearAuthStorage = () => {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(USER_STORAGE_KEY)
}

export const getStoredToken = (): string | null => {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export const getStoredUser = () => {
  const userStr = localStorage.getItem(USER_STORAGE_KEY)
  if (!userStr) return null
  
  try {
    return JSON.parse(userStr)
  } catch (error) {
    console.error('Error parsing stored user:', error)
    return null
  }
}
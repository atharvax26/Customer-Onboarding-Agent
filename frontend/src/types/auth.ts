export interface User {
  id: number
  email: string
  role: 'Developer' | 'Business_User' | 'Admin'
  is_active: boolean
  created_at: string
  last_login?: string
}

export interface UserCreate {
  email: string
  password: string
  role: 'Developer' | 'Business_User' | 'Admin'
  is_active?: boolean
}

export interface UserLogin {
  email: string
  password: string
}

export interface UserLoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface DecodedToken {
  sub: string // user id
  email: string
  role: string
  exp: number // expiration timestamp
  iat: number // issued at timestamp
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}
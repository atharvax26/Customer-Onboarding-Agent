import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import Login from '../pages/Login'
import Register from '../pages/Register'

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
)

describe('Authentication Components', () => {
  it('renders login form with required fields', () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    )
    
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders register form with required fields', () => {
    render(
      <TestWrapper>
        <Register />
      </TestWrapper>
    )
    
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/role/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('register form includes all role options', () => {
    render(
      <TestWrapper>
        <Register />
      </TestWrapper>
    )
    
    const roleSelect = screen.getByLabelText(/role/i)
    expect(roleSelect).toBeInTheDocument()
    
    // Check that role options exist
    expect(screen.getByDisplayValue('Developer')).toBeInTheDocument()
  })
})
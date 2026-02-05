import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from '../App'

const AppWithRouter = () => (
  <BrowserRouter>
    <App />
  </BrowserRouter>
)

test('renders app with navigation', () => {
  render(<AppWithRouter />)
  
  // Check if navigation elements are present
  expect(screen.getByText('Customer Onboarding Agent')).toBeInTheDocument()
  expect(screen.getByText('Home')).toBeInTheDocument()
  expect(screen.getByText('Onboarding')).toBeInTheDocument()
  expect(screen.getByText('Analytics')).toBeInTheDocument()
  expect(screen.getByText('Login')).toBeInTheDocument()
})

test('renders home page content', () => {
  render(<AppWithRouter />)
  
  // Check if home page content is present
  expect(screen.getByText('Welcome to Customer Onboarding Agent')).toBeInTheDocument()
  expect(screen.getByText(/Transform your product documentation/)).toBeInTheDocument()
})
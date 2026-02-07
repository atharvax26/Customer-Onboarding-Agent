import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ApiProvider } from './contexts/ApiContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Documents from './pages/Documents'
import Onboarding from './pages/Onboarding'
import Analytics from './pages/Analytics'
import AnalyticsTest from './pages/AnalyticsTest'
import AnalyticsSimple from './pages/AnalyticsSimple'
import Unauthorized from './pages/Unauthorized'
import ContactUs from './pages/ContactUs'
import { setupGlobalErrorHandling } from './hooks/useErrorHandler'
import './App.css'

// Setup global error handling
setupGlobalErrorHandling()

function App() {
  return (
    <ErrorBoundary level="critical" componentName="App">
      <ApiProvider>
        <AuthProvider>
          <Layout>
            <ErrorBoundary level="page" componentName="Router">
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/unauthorized" element={<Unauthorized />} />
                <Route path="/contact" element={<ContactUs />} />
                
                {/* Protected Routes */}
                <Route 
                  path="/documents" 
                  element={
                    <ErrorBoundary level="page" componentName="Documents">
                      <ProtectedRoute>
                        <Documents />
                      </ProtectedRoute>
                    </ErrorBoundary>
                  } 
                />
                
                <Route 
                  path="/onboarding" 
                  element={
                    <ErrorBoundary level="page" componentName="Onboarding">
                      <ProtectedRoute>
                        <Onboarding />
                      </ProtectedRoute>
                    </ErrorBoundary>
                  } 
                />
                
                {/* Admin-only Routes */}
                <Route 
                  path="/analytics" 
                  element={
                    <ErrorBoundary level="page" componentName="Analytics">
                      <ProtectedRoute requiredRole="Admin">
                        <Analytics />
                      </ProtectedRoute>
                    </ErrorBoundary>
                  } 
                />
                
                <Route 
                  path="/analytics-simple" 
                  element={
                    <ErrorBoundary level="page" componentName="AnalyticsSimple">
                      <ProtectedRoute requiredRole="Admin">
                        <AnalyticsSimple />
                      </ProtectedRoute>
                    </ErrorBoundary>
                  } 
                />
                
                <Route 
                  path="/analytics-test" 
                  element={
                    <ErrorBoundary level="page" componentName="AnalyticsTest">
                      <ProtectedRoute requiredRole="Admin">
                        <AnalyticsTest />
                      </ProtectedRoute>
                    </ErrorBoundary>
                  } 
                />
              </Routes>
            </ErrorBoundary>
          </Layout>
        </AuthProvider>
      </ApiProvider>
    </ErrorBoundary>
  )
}

export default App
/**
 * API Client Usage Examples
 * Demonstrates how to use the comprehensive API client with error handling,
 * loading states, and caching
 */

import { apiClient, ApiError, NetworkError, TimeoutError } from '../services/apiClient'
import { useApiClient, useAuth, useDocuments, useOnboarding, useAnalytics } from '../hooks/useApiClient'
import { cacheInvalidation, cacheWarming } from '../utils/apiCache'

// Example 1: Basic Authentication Flow
export const authenticationExample = async () => {
  try {
    console.log('🔐 Starting authentication flow...')
    
    // Register new user
    const newUser = await apiClient.auth.register({
      email: 'developer@example.com',
      password: 'securePassword123',
      role: 'Developer'
    })
    console.log('✅ User registered:', newUser)
    
    // Login
    const loginResponse = await apiClient.auth.login({
      email: 'developer@example.com',
      password: 'securePassword123'
    })
    console.log('✅ Login successful:', loginResponse.user)
    
    // Get current user (cached)
    const currentUser = await apiClient.auth.getCurrentUser()
    console.log('✅ Current user:', currentUser)
    
    return currentUser
    
  } catch (error) {
    if (error instanceof ApiError) {
      console.error(`❌ API Error (${error.status}):`, error.message)
    } else if (error instanceof NetworkError) {
      console.error('❌ Network Error:', error.message)
    } else {
      console.error('❌ Unexpected Error:', error)
    }
    throw error
  }
}

// Example 2: Document Upload with Progress Tracking
export const documentUploadExample = async () => {
  try {
    console.log('📄 Starting document upload...')
    
    // Create a mock file for demonstration
    const fileContent = `
      # API Documentation
      
      This guide covers our REST API endpoints and authentication.
      
      ## Getting Started
      1. Sign up for an API key
      2. Make authenticated requests
      3. Handle responses properly
      
      ## Authentication
      Use Bearer token authentication for all requests.
      
      ## Rate Limits
      - Free tier: 1000 requests/hour
      - Pro tier: 10000 requests/hour
    `
    
    const file = new File([fileContent], 'api-docs.md', { type: 'text/markdown' })
    
    // Upload with progress tracking
    const result = await apiClient.documents.uploadAndProcess(
      file,
      (progress) => {
        console.log(`📊 Upload progress: ${progress.toFixed(1)}%`)
      }
    )
    
    console.log('✅ Document processed:', result)
    console.log('📝 Summary:', result.summary)
    console.log('📋 Tasks:', result.tasks)
    
    return result
    
  } catch (error) {
    console.error('❌ Document upload failed:', error)
    throw error
  }
}

// Example 3: Onboarding Flow Management
export const onboardingFlowExample = async (documentId: number) => {
  try {
    console.log('🚀 Starting onboarding flow...')
    
    // Start onboarding session
    const session = await apiClient.onboarding.start(documentId)
    console.log('✅ Onboarding session started:', session)
    
    // Get current step
    const currentStep = await apiClient.onboarding.getCurrentStep(session.id)
    console.log('📍 Current step:', currentStep)
    
    // Simulate step completion and advancement
    for (let i = 0; i < session.total_steps; i++) {
      console.log(`⏳ Completing step ${i + 1}/${session.total_steps}...`)
      
      // Track user interaction
      await apiClient.engagement.trackInteraction({
        event_type: 'step_view',
        element_id: `step_${i + 1}`,
        element_type: 'onboarding_step',
        page_url: `/onboarding/step/${i + 1}`,
        timestamp: new Date().toISOString(),
        additional_data: {
          session_id: session.id,
          step_number: i + 1
        }
      })
      
      // Advance to next step
      if (i < session.total_steps - 1) {
        await apiClient.onboarding.advanceStep(session.id)
      }
      
      // Get progress
      const progress = await apiClient.onboarding.getProgress(session.id)
      console.log(`📊 Progress: ${progress.completion_percentage}%`)
    }
    
    console.log('🎉 Onboarding completed!')
    return session
    
  } catch (error) {
    console.error('❌ Onboarding flow failed:', error)
    throw error
  }
}

// Example 4: Analytics Dashboard Data
export const analyticsExample = async () => {
  try {
    console.log('📊 Fetching analytics data...')
    
    // Get dashboard data (cached)
    const dashboardData = await apiClient.analytics.getDashboardData()
    console.log('✅ Dashboard data:', dashboardData)
    
    // Get activation rates by role
    const activationRates = await apiClient.analytics.getActivationRates({
      role: 'Developer',
      start_date: '2024-01-01',
      end_date: '2024-01-31'
    })
    console.log('✅ Activation rates:', activationRates)
    
    // Get dropoff analysis
    const dropoffAnalysis = await apiClient.analytics.getDropoffAnalysis()
    console.log('✅ Dropoff analysis:', dropoffAnalysis)
    
    // Get real-time metrics
    const realTimeMetrics = await apiClient.analytics.getRealTimeMetrics()
    console.log('✅ Real-time metrics:', realTimeMetrics)
    
    return {
      dashboard: dashboardData,
      activation: activationRates,
      dropoff: dropoffAnalysis,
      realTime: realTimeMetrics
    }
    
  } catch (error) {
    console.error('❌ Analytics fetch failed:', error)
    throw error
  }
}

// Example 5: Error Handling and Retry Logic
export const errorHandlingExample = async () => {
  try {
    console.log('🔄 Testing error handling and retry logic...')
    
    // This will likely fail and demonstrate retry logic
    const result = await apiClient.auth.getCurrentUser()
    console.log('✅ Request succeeded:', result)
    
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.status) {
        case 401:
          console.log('🔐 Authentication required - redirecting to login')
          // Handle authentication error
          break
        case 403:
          console.log('🚫 Access denied - user lacks permissions')
          // Handle authorization error
          break
        case 429:
          console.log('⏳ Rate limited - will retry automatically')
          // Rate limit handled by retry logic
          break
        case 500:
          console.log('🔧 Server error - will retry automatically')
          // Server error handled by retry logic
          break
        default:
          console.log(`❌ API Error ${error.status}: ${error.message}`)
      }
    } else if (error instanceof NetworkError) {
      console.log('🌐 Network error - check connection')
    } else if (error instanceof TimeoutError) {
      console.log('⏰ Request timeout - server taking too long')
    } else {
      console.log('❌ Unexpected error:', error)
    }
  }
}

// Example 6: Using React Hooks
export const ReactHookExample: React.FC = () => {
  const { api, isLoading, error, handleApiError } = useApiClient()
  const { login, logout, isLoading: authLoading } = useAuth()
  const { upload, getAll, isLoading: docsLoading } = useDocuments()
  
  const handleLogin = async () => {
    try {
      const result = await login({
        email: 'user@example.com',
        password: 'password'
      })
      console.log('Login successful:', result)
    } catch (error) {
      handleApiError(error)
    }
  }
  
  const handleFileUpload = async (file: File) => {
    try {
      const result = await upload(file, (progress) => {
        console.log(`Upload progress: ${progress}%`)
      })
      console.log('Upload successful:', result)
    } catch (error) {
      handleApiError(error)
    }
  }
  
  return (
    <div>
      <h2>API Client Example</h2>
      
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
      
      <button 
        onClick={handleLogin} 
        disabled={authLoading}
      >
        {authLoading ? 'Logging in...' : 'Login'}
      </button>
      
      <input 
        type="file" 
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) handleFileUpload(file)
        }}
        disabled={docsLoading}
      />
      
      {isLoading('GET:/documents') && <p>Loading documents...</p>}
    </div>
  )
}

// Example 7: Cache Management
export const cacheManagementExample = async () => {
  console.log('🗄️ Cache management examples...')
  
  // Warm up cache with common data
  await cacheWarming.warmUserData(apiClient)
  await cacheWarming.warmAnalyticsData(apiClient)
  
  // Invalidate specific data when it changes
  cacheInvalidation.invalidateUserData() // After user updates
  cacheInvalidation.invalidateDocuments() // After document changes
  cacheInvalidation.invalidateAnalytics() // After analytics refresh
  
  // Clear all cache
  cacheInvalidation.invalidateAll()
  
  console.log('✅ Cache management completed')
}

// Example 8: Request Cancellation
export const requestCancellationExample = async () => {
  console.log('🚫 Request cancellation examples...')
  
  // Start a long-running request
  const promise = apiClient.analytics.getDashboardData()
  
  // Cancel it after 1 second
  setTimeout(() => {
    apiClient.cancelRequest('GET', '/analytics/dashboard')
    console.log('✅ Request cancelled')
  }, 1000)
  
  try {
    await promise
  } catch (error) {
    console.log('Request was cancelled:', error.message)
  }
  
  // Cancel all pending requests
  apiClient.cancelAllRequests()
  console.log('✅ All requests cancelled')
}

// Example 9: Complete Workflow
export const completeWorkflowExample = async () => {
  try {
    console.log('🔄 Running complete workflow example...')
    
    // 1. Authenticate
    const user = await authenticationExample()
    
    // 2. Upload and process document
    const document = await documentUploadExample()
    
    // 3. Start onboarding flow
    const session = await onboardingFlowExample(document.id)
    
    // 4. Get analytics
    const analytics = await analyticsExample()
    
    // 5. Demonstrate cache management
    await cacheManagementExample()
    
    console.log('🎉 Complete workflow finished successfully!')
    
    return {
      user,
      document,
      session,
      analytics
    }
    
  } catch (error) {
    console.error('❌ Workflow failed:', error)
    throw error
  }
}

// Export all examples
export const apiClientExamples = {
  authentication: authenticationExample,
  documentUpload: documentUploadExample,
  onboardingFlow: onboardingFlowExample,
  analytics: analyticsExample,
  errorHandling: errorHandlingExample,
  cacheManagement: cacheManagementExample,
  requestCancellation: requestCancellationExample,
  completeWorkflow: completeWorkflowExample
}

// Make examples available in browser console for testing
if (typeof window !== 'undefined') {
  (window as any).apiClientExamples = apiClientExamples
}
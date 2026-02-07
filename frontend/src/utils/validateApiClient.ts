/**
 * API Client Validation Script
 * Simple validation to ensure API client is properly structured
 */

import { apiClient, ApiError, NetworkError, TimeoutError } from '../services/apiClient'
import { apiCache } from './apiCache'

// Validation results interface
interface ValidationResult {
  test: string
  passed: boolean
  error?: string
}

// Run validation tests
export const validateApiClient = (): ValidationResult[] => {
  const results: ValidationResult[] = []

  // Test 1: API client instance exists
  try {
    if (apiClient && typeof apiClient === 'object') {
      results.push({ test: 'API client instance exists', passed: true })
    } else {
      results.push({ test: 'API client instance exists', passed: false, error: 'API client not found' })
    }
  } catch (error) {
    results.push({ test: 'API client instance exists', passed: false, error: String(error) })
  }

  // Test 2: API client has required methods
  try {
    const requiredMethods = ['auth', 'documents', 'onboarding', 'engagement', 'intervention', 'analytics']
    const missingMethods = requiredMethods.filter(method => !(method in apiClient))
    
    if (missingMethods.length === 0) {
      results.push({ test: 'API client has required methods', passed: true })
    } else {
      results.push({ 
        test: 'API client has required methods', 
        passed: false, 
        error: `Missing methods: ${missingMethods.join(', ')}` 
      })
    }
  } catch (error) {
    results.push({ test: 'API client has required methods', passed: false, error: String(error) })
  }

  // Test 3: Auth methods exist
  try {
    const authMethods = ['login', 'register', 'logout', 'getCurrentUser']
    const missingAuthMethods = authMethods.filter(method => !(method in apiClient.auth))
    
    if (missingAuthMethods.length === 0) {
      results.push({ test: 'Auth methods exist', passed: true })
    } else {
      results.push({ 
        test: 'Auth methods exist', 
        passed: false, 
        error: `Missing auth methods: ${missingAuthMethods.join(', ')}` 
      })
    }
  } catch (error) {
    results.push({ test: 'Auth methods exist', passed: false, error: String(error) })
  }

  // Test 4: Document methods exist
  try {
    const docMethods = ['upload', 'uploadAndProcess', 'getAll', 'getById', 'delete', 'process', 'getStats']
    const missingDocMethods = docMethods.filter(method => !(method in apiClient.documents))
    
    if (missingDocMethods.length === 0) {
      results.push({ test: 'Document methods exist', passed: true })
    } else {
      results.push({ 
        test: 'Document methods exist', 
        passed: false, 
        error: `Missing document methods: ${missingDocMethods.join(', ')}` 
      })
    }
  } catch (error) {
    results.push({ test: 'Document methods exist', passed: false, error: String(error) })
  }

  // Test 5: Loading state management
  try {
    const hasLoadingMethods = typeof apiClient.isLoading === 'function' && 
                             typeof apiClient.getAllLoadingStates === 'function'
    
    if (hasLoadingMethods) {
      results.push({ test: 'Loading state management exists', passed: true })
    } else {
      results.push({ 
        test: 'Loading state management exists', 
        passed: false, 
        error: 'Missing loading state methods' 
      })
    }
  } catch (error) {
    results.push({ test: 'Loading state management exists', passed: false, error: String(error) })
  }

  // Test 6: Request cancellation
  try {
    const hasCancellationMethods = typeof apiClient.cancelRequest === 'function' && 
                                  typeof apiClient.cancelAllRequests === 'function'
    
    if (hasCancellationMethods) {
      results.push({ test: 'Request cancellation exists', passed: true })
    } else {
      results.push({ 
        test: 'Request cancellation exists', 
        passed: false, 
        error: 'Missing cancellation methods' 
      })
    }
  } catch (error) {
    results.push({ test: 'Request cancellation exists', passed: false, error: String(error) })
  }

  // Test 7: Error classes exist
  try {
    const errorClassesExist = typeof ApiError === 'function' && 
                             typeof NetworkError === 'function' && 
                             typeof TimeoutError === 'function'
    
    if (errorClassesExist) {
      results.push({ test: 'Error classes exist', passed: true })
    } else {
      results.push({ 
        test: 'Error classes exist', 
        passed: false, 
        error: 'Missing error classes' 
      })
    }
  } catch (error) {
    results.push({ test: 'Error classes exist', passed: false, error: String(error) })
  }

  // Test 8: Cache functionality
  try {
    const hasCacheMethods = typeof apiCache.get === 'function' && 
                           typeof apiCache.set === 'function' && 
                           typeof apiCache.clear === 'function'
    
    if (hasCacheMethods) {
      results.push({ test: 'Cache functionality exists', passed: true })
    } else {
      results.push({ 
        test: 'Cache functionality exists', 
        passed: false, 
        error: 'Missing cache methods' 
      })
    }
  } catch (error) {
    results.push({ test: 'Cache functionality exists', passed: false, error: String(error) })
  }

  // Test 9: Analytics methods exist
  try {
    const analyticsMethods = [
      'getActivationRates', 'getDropoffAnalysis', 'getEngagementTrends', 
      'getDashboardData', 'getRealTimeMetrics', 'getMetricsSummary'
    ]
    const missingAnalyticsMethods = analyticsMethods.filter(method => !(method in apiClient.analytics))
    
    if (missingAnalyticsMethods.length === 0) {
      results.push({ test: 'Analytics methods exist', passed: true })
    } else {
      results.push({ 
        test: 'Analytics methods exist', 
        passed: false, 
        error: `Missing analytics methods: ${missingAnalyticsMethods.join(', ')}` 
      })
    }
  } catch (error) {
    results.push({ test: 'Analytics methods exist', passed: false, error: String(error) })
  }

  // Test 10: Onboarding methods exist
  try {
    const onboardingMethods = ['start', 'getCurrentStep', 'advanceStep', 'getProgress', 'getUserSessions', 'getSessionDetails']
    const missingOnboardingMethods = onboardingMethods.filter(method => !(method in apiClient.onboarding))
    
    if (missingOnboardingMethods.length === 0) {
      results.push({ test: 'Onboarding methods exist', passed: true })
    } else {
      results.push({ 
        test: 'Onboarding methods exist', 
        passed: false, 
        error: `Missing onboarding methods: ${missingOnboardingMethods.join(', ')}` 
      })
    }
  } catch (error) {
    results.push({ test: 'Onboarding methods exist', passed: false, error: String(error) })
  }

  return results
}

// Console validation runner
export const runValidation = (): void => {
  console.log('🔍 Validating API Client Implementation...')
  console.log('=' .repeat(50))
  
  const results = validateApiClient()
  let passed = 0
  let failed = 0
  
  results.forEach(result => {
    if (result.passed) {
      console.log(`✅ ${result.test}`)
      passed++
    } else {
      console.log(`❌ ${result.test}: ${result.error}`)
      failed++
    }
  })
  
  console.log('=' .repeat(50))
  console.log(`📊 Results: ${passed} passed, ${failed} failed`)
  
  if (failed === 0) {
    console.log('🎉 All validations passed! API Client is properly implemented.')
  } else {
    console.log('⚠️  Some validations failed. Please check the implementation.')
  }
}

// Export for use in browser console
if (typeof window !== 'undefined') {
  (window as any).validateApiClient = runValidation
}
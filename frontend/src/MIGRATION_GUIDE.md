# API Client Migration Guide

This guide helps you migrate from the legacy API utilities to the new comprehensive API client.

## Overview

The new API client provides:
- ✅ Better error handling with retry logic
- ✅ Loading state management
- ✅ Response caching with TTL
- ✅ Request cancellation
- ✅ TypeScript support
- ✅ React hooks integration
- ✅ Offline support

## Migration Steps

### 1. Update Imports

**Before:**
```typescript
import { onboardingApi, engagementApi, documentApi, interventionApi } from '../utils/api'
import { analyticsApi } from '../utils/analyticsApi'
```

**After:**
```typescript
import { apiClient } from '../services/apiClient'
// OR use specialized hooks
import { useOnboarding, useEngagement, useDocuments, useIntervention, useAnalytics } from '../hooks/useApiClient'
```

### 2. Update API Calls

#### Authentication
**Before:**
```typescript
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})
const data = await response.json()
```

**After:**
```typescript
const data = await apiClient.auth.login({ email, password })
```

#### Document Operations
**Before:**
```typescript
import { documentApi } from '../utils/api'

const documents = await documentApi.getDocuments()
const result = await documentApi.uploadAndProcessDocument(file, onProgress)
```

**After:**
```typescript
import { apiClient } from '../services/apiClient'

const documents = await apiClient.documents.getAll()
const result = await apiClient.documents.uploadAndProcess(file, onProgress)
```

#### Onboarding Operations
**Before:**
```typescript
import { onboardingApi } from '../utils/api'

const sessions = await onboardingApi.getUserSessions()
const step = await onboardingApi.getCurrentStep(sessionId)
```

**After:**
```typescript
import { apiClient } from '../services/apiClient'

const sessions = await apiClient.onboarding.getUserSessions()
const step = await apiClient.onboarding.getCurrentStep(sessionId)
```

#### Analytics Operations
**Before:**
```typescript
import { analyticsApi } from '../utils/analyticsApi'

const rates = await analyticsApi.getActivationRates(filters)
const dashboard = await analyticsApi.getDashboardData()
```

**After:**
```typescript
import { apiClient } from '../services/apiClient'

const rates = await apiClient.analytics.getActivationRates(filters)
const dashboard = await apiClient.analytics.getDashboardData()
```

### 3. Add Error Handling

**Before:**
```typescript
try {
  const data = await onboardingApi.getUserSessions()
  setData(data)
} catch (error) {
  console.error('Error:', error)
  setError('Something went wrong')
}
```

**After:**
```typescript
import { ApiError, NetworkError, TimeoutError } from '../services/apiClient'

try {
  const data = await apiClient.onboarding.getUserSessions()
  setData(data)
} catch (error) {
  if (error instanceof ApiError) {
    setError(`API Error: ${error.message}`)
  } else if (error instanceof NetworkError) {
    setError('Network error. Please check your connection.')
  } else if (error instanceof TimeoutError) {
    setError('Request timeout. Please try again.')
  } else {
    setError('An unexpected error occurred.')
  }
}
```

### 4. Add Loading States

**Before:**
```typescript
const [loading, setLoading] = useState(false)

const fetchData = async () => {
  setLoading(true)
  try {
    const data = await onboardingApi.getUserSessions()
    setData(data)
  } finally {
    setLoading(false)
  }
}
```

**After:**
```typescript
import { useApiClient } from '../hooks/useApiClient'

const { api, isLoading } = useApiClient()

const fetchData = async () => {
  const data = await api.onboarding.getUserSessions()
  setData(data)
}

// In render
const loading = isLoading('GET:/onboarding/sessions')
```

### 5. Use React Hooks (Recommended)

**Before:**
```typescript
const [data, setData] = useState(null)
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)

useEffect(() => {
  const fetchData = async () => {
    setLoading(true)
    try {
      const result = await onboardingApi.getUserSessions()
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  fetchData()
}, [])
```

**After:**
```typescript
import { useOnboarding } from '../hooks/useApiClient'

const { getUserSessions, isLoading, handleError } = useOnboarding()
const [data, setData] = useState(null)

useEffect(() => {
  const fetchData = async () => {
    try {
      const result = await getUserSessions()
      setData(result)
    } catch (error) {
      handleError(error) // Automatically handles error display
    }
  }
  fetchData()
}, [])

// In render
if (isLoading('sessions')) return <div>Loading...</div>
```

## Component Migration Examples

### AuthContext Migration

**Before:**
```typescript
const login = async (email: string, password: string) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  
  if (!response.ok) {
    throw new Error('Login failed')
  }
  
  const data = await response.json()
  localStorage.setItem('auth_token', data.access_token)
  setUser(data.user)
}
```

**After:**
```typescript
import { apiClient } from '../services/apiClient'

const login = async (email: string, password: string) => {
  const data = await apiClient.auth.login({ email, password })
  // Token is automatically stored by the API client
  setUser(data.user)
}
```

### Document Upload Component

**Before:**
```typescript
const handleUpload = async (file: File) => {
  setUploading(true)
  try {
    const result = await documentApi.uploadAndProcessDocument(
      file,
      (progress) => setProgress(progress)
    )
    setResult(result)
  } catch (error) {
    setError(error.message)
  } finally {
    setUploading(false)
  }
}
```

**After:**
```typescript
import { useDocuments } from '../hooks/useApiClient'

const { uploadAndProcess, isLoading, handleError } = useDocuments()

const handleUpload = async (file: File) => {
  try {
    const result = await uploadAndProcess(
      file,
      (progress) => setProgress(progress)
    )
    setResult(result)
  } catch (error) {
    handleError(error)
  }
}

// In render
const uploading = isLoading('upload-and-process')
```

### Analytics Dashboard

**Before:**
```typescript
useEffect(() => {
  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      const [dashboard, rates, dropoff] = await Promise.all([
        analyticsApi.getDashboardData(),
        analyticsApi.getActivationRates(filters),
        analyticsApi.getDropoffAnalysis(filters)
      ])
      setDashboard(dashboard)
      setRates(rates)
      setDropoff(dropoff)
    } catch (error) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }
  fetchAnalytics()
}, [filters])
```

**After:**
```typescript
import { useAnalytics } from '../hooks/useApiClient'

const { 
  getDashboardData, 
  getActivationRates, 
  getDropoffAnalysis,
  isLoading,
  handleError 
} = useAnalytics()

useEffect(() => {
  const fetchAnalytics = async () => {
    try {
      const [dashboard, rates, dropoff] = await Promise.all([
        getDashboardData(),
        getActivationRates(filters),
        getDropoffAnalysis(filters)
      ])
      setDashboard(dashboard)
      setRates(rates)
      setDropoff(dropoff)
    } catch (error) {
      handleError(error)
    }
  }
  fetchAnalytics()
}, [filters])

// Loading states are automatically managed
const loading = isLoading('dashboard') || isLoading('activation-rates') || isLoading('dropoff-analysis')
```

## Advanced Features

### Request Cancellation
```typescript
import { useEffect } from 'react'
import { apiClient } from '../services/apiClient'

useEffect(() => {
  const fetchData = async () => {
    try {
      const data = await apiClient.analytics.getDashboardData()
      setData(data)
    } catch (error) {
      if (error.message !== 'Request was cancelled') {
        handleError(error)
      }
    }
  }
  
  fetchData()
  
  // Cancel request on unmount
  return () => {
    apiClient.cancelRequest('GET', '/analytics/dashboard')
  }
}, [])
```

### Cache Management
```typescript
import { cacheInvalidation } from '../utils/apiCache'

const handleDataUpdate = async () => {
  // Update data
  await apiClient.documents.upload(file)
  
  // Invalidate related cache
  cacheInvalidation.invalidateDocuments()
  
  // Refresh UI
  fetchDocuments()
}
```

### Global Error Handling
```typescript
import { ApiProvider } from '../contexts/ApiContext'

function App() {
  return (
    <ApiProvider>
      <Router>
        <Routes>
          {/* Your routes */}
        </Routes>
      </Router>
    </ApiProvider>
  )
}
```

## Testing Migration

### Before
```typescript
// Mock fetch
global.fetch = jest.fn()

test('should fetch user sessions', async () => {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: 1, status: 'active' }]
  })
  
  const sessions = await onboardingApi.getUserSessions()
  expect(sessions).toHaveLength(1)
})
```

### After
```typescript
import { apiClient } from '../services/apiClient'

// Mock the API client
jest.mock('../services/apiClient', () => ({
  apiClient: {
    onboarding: {
      getUserSessions: jest.fn()
    }
  }
}))

test('should fetch user sessions', async () => {
  const mockSessions = [{ id: 1, status: 'active' }]
  apiClient.onboarding.getUserSessions.mockResolvedValue(mockSessions)
  
  const sessions = await apiClient.onboarding.getUserSessions()
  expect(sessions).toEqual(mockSessions)
})
```

## Checklist

- [ ] Update all API imports
- [ ] Replace direct fetch calls with API client methods
- [ ] Add proper error handling with typed errors
- [ ] Implement loading states using hooks or client methods
- [ ] Update tests to mock the new API client
- [ ] Remove old API utility files (after migration)
- [ ] Add ApiProvider to app root
- [ ] Test all API functionality
- [ ] Update documentation

## Benefits After Migration

1. **Better Error Handling**: Automatic retry logic and user-friendly error messages
2. **Loading States**: Built-in loading state management
3. **Caching**: Automatic response caching for better performance
4. **Type Safety**: Full TypeScript support with proper types
5. **Request Management**: Ability to cancel requests and handle timeouts
6. **Offline Support**: Request queuing for offline scenarios
7. **Consistent API**: Unified interface for all backend services
8. **React Integration**: Specialized hooks for React components

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to import from the correct paths
2. **Type Errors**: Ensure response types match the expected interfaces
3. **Loading States**: Use the correct loading key format
4. **Cache Issues**: Clear cache if seeing stale data
5. **Error Handling**: Make sure to handle all error types

### Getting Help

1. Check the API client README: `frontend/src/services/README.md`
2. Review usage examples: `frontend/src/examples/apiClientUsage.ts`
3. Run validation: `frontend/src/utils/validateApiClient.ts`
4. Check the test suite: `frontend/src/test/apiClient.test.ts`
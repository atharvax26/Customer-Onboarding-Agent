# API Client Services

This directory contains the comprehensive API client implementation for the Customer Onboarding Agent frontend, providing typed API access with advanced error handling, retry logic, loading states, and caching.

## Overview

The API client is designed to work seamlessly with the ScaleDown AI-powered backend, providing:

- **Typed API Access**: Full TypeScript support with proper type definitions
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Retry Logic**: Exponential backoff retry for network errors and rate limits
- **Loading States**: Real-time loading state management for UI feedback
- **Response Caching**: Intelligent caching with TTL and invalidation patterns
- **Request Cancellation**: Ability to cancel individual or all pending requests
- **Offline Support**: Request queuing for offline scenarios

## Files

### `apiClient.ts`
The main API client implementation with all service endpoints:

- **Authentication**: Login, register, logout, get current user
- **Documents**: Upload, process, manage documents (ScaleDown AI integration)
- **Onboarding**: Start sessions, manage steps, track progress
- **Engagement**: Track interactions, get engagement scores
- **Intervention**: Check for help, trigger manual help, submit feedback
- **Analytics**: Get metrics, dashboard data, real-time updates

### Key Features

#### Error Handling
```typescript
try {
  const user = await apiClient.auth.getCurrentUser()
} catch (error) {
  if (error instanceof ApiError) {
    // Handle API errors (4xx, 5xx)
    console.log(`API Error ${error.status}: ${error.message}`)
  } else if (error instanceof NetworkError) {
    // Handle network connectivity issues
    console.log('Network error:', error.message)
  } else if (error instanceof TimeoutError) {
    // Handle request timeouts
    console.log('Request timeout:', error.message)
  }
}
```

#### Loading States
```typescript
// Check if specific operation is loading
const isLoading = apiClient.isLoading('GET:/auth/me')

// Get all loading states
const allStates = apiClient.getAllLoadingStates()
```

#### Request Cancellation
```typescript
// Cancel specific request
apiClient.cancelRequest('GET', '/auth/me')

// Cancel all pending requests
apiClient.cancelAllRequests()
```

#### Caching
```typescript
// Cached requests (GET only)
const user = await apiClient.auth.getCurrentUser() // Cached for 5 minutes

// Manual cache management
import { cacheInvalidation } from '../utils/apiCache'
cacheInvalidation.invalidateUserData()
```

## Usage Examples

### Basic Authentication
```typescript
import { apiClient } from '../services/apiClient'

// Login
const response = await apiClient.auth.login({
  email: 'user@example.com',
  password: 'password'
})

// Get current user (cached)
const user = await apiClient.auth.getCurrentUser()
```

### Document Upload with Progress
```typescript
const file = new File(['content'], 'document.txt')

const result = await apiClient.documents.uploadAndProcess(
  file,
  (progress) => console.log(`Progress: ${progress}%`)
)

console.log('Summary:', result.summary)
console.log('Tasks:', result.tasks)
```

### Onboarding Flow
```typescript
// Start onboarding
const session = await apiClient.onboarding.start(documentId)

// Get current step
const step = await apiClient.onboarding.getCurrentStep(session.id)

// Advance step
await apiClient.onboarding.advanceStep(session.id)
```

### Analytics Data
```typescript
// Get dashboard data
const dashboard = await apiClient.analytics.getDashboardData()

// Get activation rates with filters
const rates = await apiClient.analytics.getActivationRates({
  role: 'Developer',
  start_date: '2024-01-01',
  end_date: '2024-01-31'
})
```

## React Hooks

The `useApiClient` hook provides React integration:

```typescript
import { useApiClient, useAuth, useDocuments } from '../hooks/useApiClient'

const MyComponent = () => {
  const { api, isLoading, error, handleApiError } = useApiClient()
  const { login, logout } = useAuth()
  const { upload, getAll } = useDocuments()
  
  // Component logic here
}
```

### Specialized Hooks

- `useAuth()`: Authentication operations
- `useDocuments()`: Document management
- `useOnboarding()`: Onboarding flow management
- `useAnalytics()`: Analytics data access
- `useEngagement()`: Engagement tracking
- `useIntervention()`: Intervention system

## Context Provider

Use the `ApiProvider` for global state management:

```typescript
import { ApiProvider } from '../contexts/ApiContext'

function App() {
  return (
    <ApiProvider>
      <YourAppComponents />
    </ApiProvider>
  )
}
```

## Configuration

### Environment Variables
The API client uses these configuration options:

- `API_BASE_URL`: Base URL for API requests (default: '/api')
- `DEFAULT_TIMEOUT`: Request timeout in milliseconds (default: 30000)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `CACHE_DURATION`: Cache TTL in milliseconds (default: 300000)

### Customization
```typescript
import { ApiClient } from '../services/apiClient'

// Create custom client with different configuration
const customClient = new ApiClient()
```

## Error Types

### `ApiError`
HTTP errors from the API (4xx, 5xx status codes)
```typescript
class ApiError extends Error {
  constructor(public status: number, message: string, public response?: Response)
}
```

### `NetworkError`
Network connectivity issues
```typescript
class NetworkError extends Error {
  constructor(message: string = 'Network error occurred')
}
```

### `TimeoutError`
Request timeout errors
```typescript
class TimeoutError extends Error {
  constructor(message: string = 'Request timeout')
}
```

## Caching System

### Cache Features
- **TTL-based expiration**: Automatic cache invalidation
- **Tag-based invalidation**: Group-based cache clearing
- **Pattern-based invalidation**: Regex-based cache clearing
- **Storage persistence**: Optional localStorage persistence
- **LRU eviction**: Least recently used eviction policy

### Cache Management
```typescript
import { apiCache, cacheInvalidation } from '../utils/apiCache'

// Manual cache operations
apiCache.set('/api/users/me', userData, { ttl: 300000, tags: ['user'] })
const cached = apiCache.get('/api/users/me')

// Invalidation patterns
cacheInvalidation.invalidateUserData()
cacheInvalidation.invalidateDocuments()
cacheInvalidation.invalidateAll()
```

## Testing

### Validation
Run the validation script to check implementation:
```typescript
import { runValidation } from '../utils/validateApiClient'
runValidation()
```

### Unit Tests
Comprehensive test suite available in `../test/apiClient.test.ts`:
- Error handling scenarios
- Retry logic verification
- Loading state management
- Cache functionality
- Request cancellation

## Integration with ScaleDown AI

The API client is specifically designed to work with ScaleDown AI for document processing:

- **Single API Call Processing**: Documents are processed in one ScaleDown AI API call
- **Structured Responses**: Handles ScaleDown AI's JSON response format
- **Error Handling**: Specific error handling for ScaleDown AI rate limits and errors
- **Progress Tracking**: Real-time progress updates during document processing

## Best Practices

1. **Always handle errors**: Use try-catch blocks and proper error handling
2. **Use loading states**: Provide user feedback during API operations
3. **Leverage caching**: Use cached endpoints for frequently accessed data
4. **Cancel requests**: Cancel requests when components unmount
5. **Use hooks**: Prefer React hooks for component integration
6. **Type safety**: Always use TypeScript types for API responses

## Troubleshooting

### Common Issues

1. **Authentication errors**: Check token storage and expiration
2. **Network errors**: Verify API endpoint availability
3. **Cache issues**: Clear cache or disable caching for debugging
4. **Loading states**: Ensure proper loading state management
5. **Type errors**: Verify response types match expected interfaces

### Debug Mode
Enable debug logging:
```typescript
// In browser console
localStorage.setItem('debug', 'api-client')
```

## Migration from Legacy API

The new API client replaces the old `api.ts` utilities:

```typescript
// Old way
import { onboardingApi } from '../utils/api'
const sessions = await onboardingApi.getUserSessions()

// New way
import { apiClient } from '../services/apiClient'
const sessions = await apiClient.onboarding.getUserSessions()
```

The legacy API utilities are kept for backward compatibility but should be migrated to the new client.
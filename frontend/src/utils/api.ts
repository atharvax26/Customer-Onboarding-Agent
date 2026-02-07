/**
 * Legacy API utilities - DEPRECATED
 * Use the new apiClient from '../services/apiClient' instead
 * This file is kept for backward compatibility
 */

import { apiClient, ApiError } from '../services/apiClient'

// Re-export for backward compatibility
export { ApiError }

// Legacy API functions - use apiClient instead
export const onboardingApi = apiClient.onboarding
export const engagementApi = apiClient.engagement
export const documentApi = apiClient.documents
export const interventionApi = apiClient.intervention
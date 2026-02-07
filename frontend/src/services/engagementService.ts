/**
 * Engagement Service
 * Tracks user engagement events and interactions
 */

import { apiClient } from './apiClient'

export interface EngagementEvent {
  type: string
  data: Record<string, any>
  timestamp?: string
}

export interface EngagementScore {
  user_id: number
  score: number
  last_activity: string
  activity_count: number
}

/**
 * Track an engagement event
 */
export async function trackEngagementEvent(event: EngagementEvent): Promise<void> {
  try {
    const eventData = {
      event_type: event.type,
      page_url: window.location.href,
      timestamp: event.timestamp || new Date().toISOString(),
      additional_data: event.data
    }

    await apiClient.post('/engagement/track-interaction', eventData)
  } catch (error) {
    // Silently fail for engagement tracking to not disrupt user experience
    console.warn('Failed to track engagement event:', error)
  }
}

/**
 * Get engagement score for current user
 */
export async function getEngagementScore(): Promise<EngagementScore | null> {
  try {
    const response = await apiClient.get('/engagement/score')
    return response
  } catch (error) {
    console.error('Failed to get engagement score:', error)
    return null
  }
}

/**
 * Track page view
 */
export async function trackPageView(page: string, metadata?: Record<string, any>): Promise<void> {
  await trackEngagementEvent({
    type: 'page_view',
    data: {
      page,
      url: window.location.href,
      referrer: document.referrer,
      ...metadata
    }
  })
}

/**
 * Track button click
 */
export async function trackButtonClick(buttonId: string, metadata?: Record<string, any>): Promise<void> {
  await trackEngagementEvent({
    type: 'button_click',
    data: {
      button_id: buttonId,
      page: window.location.pathname,
      ...metadata
    }
  })
}

/**
 * Track form submission
 */
export async function trackFormSubmission(formId: string, success: boolean, metadata?: Record<string, any>): Promise<void> {
  await trackEngagementEvent({
    type: 'form_submission',
    data: {
      form_id: formId,
      success,
      page: window.location.pathname,
      ...metadata
    }
  })
}

/**
 * Track time spent on page
 */
export async function trackTimeOnPage(page: string, duration: number): Promise<void> {
  await trackEngagementEvent({
    type: 'time_on_page',
    data: {
      page,
      duration_seconds: duration,
      url: window.location.href
    }
  })
}

/**
 * Track user interaction
 */
export async function trackInteraction(interactionType: string, metadata?: Record<string, any>): Promise<void> {
  await trackEngagementEvent({
    type: 'interaction',
    data: {
      interaction_type: interactionType,
      page: window.location.pathname,
      ...metadata
    }
  })
}

export default {
  trackEngagementEvent,
  getEngagementScore,
  trackPageView,
  trackButtonClick,
  trackFormSubmission,
  trackTimeOnPage,
  trackInteraction
}

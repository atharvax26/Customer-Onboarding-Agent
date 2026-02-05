import { useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { engagementApi } from '../utils/api'
import { InteractionEvent } from '../types/onboarding'

interface UseInteractionTrackingOptions {
  sessionId?: number
  enableClickTracking?: boolean
  enableScrollTracking?: boolean
  enableTimeTracking?: boolean
  enableFocusTracking?: boolean
  debounceMs?: number
}

export const useInteractionTracking = (options: UseInteractionTrackingOptions = {}) => {
  const { user } = useAuth()
  const {
    sessionId,
    enableClickTracking = true,
    enableScrollTracking = true,
    enableTimeTracking = true,
    enableFocusTracking = true,
    debounceMs = 500
  } = options

  const pageStartTime = useRef<number>(Date.now())
  const lastScrollTime = useRef<number>(0)
  const lastFocusTime = useRef<number>(0)
  const interactionQueue = useRef<InteractionEvent[]>([])
  const flushTimeoutRef = useRef<NodeJS.Timeout>()

  // Debounced flush function
  const flushInteractions = useCallback(async () => {
    if (interactionQueue.current.length === 0) return

    const events = [...interactionQueue.current]
    interactionQueue.current = []

    try {
      // Send all queued interactions
      await Promise.all(
        events.map(event => engagementApi.trackInteraction(event))
      )
    } catch (error) {
      console.error('Failed to track interactions:', error)
      // Re-queue failed events (with a limit to prevent infinite growth)
      if (interactionQueue.current.length < 50) {
        interactionQueue.current.unshift(...events)
      }
    }
  }, [])

  // Queue interaction for batched sending
  const queueInteraction = useCallback((event: Omit<InteractionEvent, 'timestamp' | 'page_url'>) => {
    if (!user) return

    const interaction: InteractionEvent = {
      ...event,
      page_url: window.location.pathname,
      timestamp: new Date().toISOString()
    }

    interactionQueue.current.push(interaction)

    // Clear existing timeout and set new one
    if (flushTimeoutRef.current) {
      clearTimeout(flushTimeoutRef.current)
    }

    flushTimeoutRef.current = setTimeout(flushInteractions, debounceMs)
  }, [user, debounceMs, flushInteractions])

  // Track click interactions
  const trackClick = useCallback((event: MouseEvent) => {
    if (!enableClickTracking) return

    const target = event.target as HTMLElement
    const elementId = target.id || target.className || 'unknown'
    const elementType = target.tagName.toLowerCase()

    queueInteraction({
      event_type: 'click',
      element_id: elementId,
      element_type: elementType,
      additional_data: {
        x: event.clientX,
        y: event.clientY,
        button: event.button,
        session_id: sessionId
      }
    })
  }, [enableClickTracking, queueInteraction, sessionId])

  // Track scroll interactions
  const trackScroll = useCallback(() => {
    if (!enableScrollTracking) return

    const now = Date.now()
    if (now - lastScrollTime.current < 1000) return // Throttle to once per second

    lastScrollTime.current = now

    const scrollPercentage = Math.round(
      (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100
    )

    queueInteraction({
      event_type: 'scroll',
      additional_data: {
        scroll_percentage: Math.min(100, Math.max(0, scrollPercentage)),
        scroll_y: window.scrollY,
        session_id: sessionId
      }
    })
  }, [enableScrollTracking, queueInteraction, sessionId])

  // Track focus/blur interactions
  const trackFocus = useCallback(() => {
    if (!enableFocusTracking) return

    const now = Date.now()
    lastFocusTime.current = now

    queueInteraction({
      event_type: 'focus',
      additional_data: {
        session_id: sessionId,
        timestamp: now
      }
    })
  }, [enableFocusTracking, queueInteraction, sessionId])

  const trackBlur = useCallback(() => {
    if (!enableFocusTracking) return

    const now = Date.now()
    const focusTime = lastFocusTime.current > 0 ? now - lastFocusTime.current : 0

    queueInteraction({
      event_type: 'blur',
      additional_data: {
        focus_duration: focusTime,
        session_id: sessionId,
        timestamp: now
      }
    })
  }, [enableFocusTracking, queueInteraction, sessionId])

  // Track page time when component unmounts
  const trackPageTime = useCallback(() => {
    if (!enableTimeTracking) return

    const timeSpent = Date.now() - pageStartTime.current

    queueInteraction({
      event_type: 'page_time',
      additional_data: {
        time_spent_ms: timeSpent,
        session_id: sessionId
      }
    })

    // Flush immediately for page unload
    flushInteractions()
  }, [enableTimeTracking, queueInteraction, sessionId, flushInteractions])

  // Manual tracking functions for specific interactions
  const trackCustomEvent = useCallback((eventType: string, data?: Record<string, any>) => {
    queueInteraction({
      event_type: eventType,
      additional_data: {
        ...data,
        session_id: sessionId
      }
    })
  }, [queueInteraction, sessionId])

  const trackButtonClick = useCallback((buttonId: string, buttonText?: string) => {
    queueInteraction({
      event_type: 'button_click',
      element_id: buttonId,
      element_type: 'button',
      additional_data: {
        button_text: buttonText,
        session_id: sessionId
      }
    })
  }, [queueInteraction, sessionId])

  const trackStepAdvance = useCallback((fromStep: number, toStep: number) => {
    queueInteraction({
      event_type: 'step_advance',
      additional_data: {
        from_step: fromStep,
        to_step: toStep,
        session_id: sessionId
      }
    })
  }, [queueInteraction, sessionId])

  const trackStepComplete = useCallback((stepNumber: number, timeSpent: number) => {
    queueInteraction({
      event_type: 'step_complete',
      additional_data: {
        step_number: stepNumber,
        time_spent_ms: timeSpent,
        session_id: sessionId
      }
    })
  }, [queueInteraction, sessionId])

  // Set up event listeners
  useEffect(() => {
    if (!user) return

    // Add event listeners
    if (enableClickTracking) {
      document.addEventListener('click', trackClick, true)
    }

    if (enableScrollTracking) {
      window.addEventListener('scroll', trackScroll, { passive: true })
    }

    if (enableFocusTracking) {
      window.addEventListener('focus', trackFocus)
      window.addEventListener('blur', trackBlur)
    }

    // Track page visibility changes
    const handleVisibilityChange = () => {
      if (document.hidden) {
        trackBlur()
      } else {
        trackFocus()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    // Track page unload
    window.addEventListener('beforeunload', trackPageTime)

    // Cleanup function
    return () => {
      if (enableClickTracking) {
        document.removeEventListener('click', trackClick, true)
      }

      if (enableScrollTracking) {
        window.removeEventListener('scroll', trackScroll)
      }

      if (enableFocusTracking) {
        window.removeEventListener('focus', trackFocus)
        window.removeEventListener('blur', trackBlur)
      }

      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('beforeunload', trackPageTime)

      // Clear timeout and flush remaining interactions
      if (flushTimeoutRef.current) {
        clearTimeout(flushTimeoutRef.current)
      }
      flushInteractions()
    }
  }, [
    user,
    enableClickTracking,
    enableScrollTracking,
    enableFocusTracking,
    trackClick,
    trackScroll,
    trackFocus,
    trackBlur,
    trackPageTime,
    flushInteractions
  ])

  return {
    trackCustomEvent,
    trackButtonClick,
    trackStepAdvance,
    trackStepComplete,
    flushInteractions
  }
}
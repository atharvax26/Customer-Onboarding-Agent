import React, { useRef, useEffect, cloneElement, ReactElement } from 'react'
import { useInteractionTracking } from '../../hooks/useInteractionTracking'

interface InteractionTrackerProps {
  children: ReactElement
  trackClicks?: boolean
  trackHovers?: boolean
  trackFocus?: boolean
  eventPrefix?: string
  sessionId?: number
  additionalData?: Record<string, any>
}

const InteractionTracker: React.FC<InteractionTrackerProps> = ({
  children,
  trackClicks = true,
  trackHovers = false,
  trackFocus = false,
  eventPrefix = '',
  sessionId,
  additionalData = {}
}) => {
  const elementRef = useRef<HTMLElement>(null)
  const hoverStartTime = useRef<number>(0)
  const focusStartTime = useRef<number>(0)
  
  const { trackCustomEvent } = useInteractionTracking({ sessionId })

  // Get element identifier
  const getElementId = (element: HTMLElement): string => {
    return element.id || 
           element.className || 
           element.tagName.toLowerCase() || 
           'unknown-element'
  }

  // Track click events
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    if (!trackClicks || !elementRef.current) return

    const elementId = getElementId(elementRef.current)
    const eventType = eventPrefix ? `${eventPrefix}_click` : 'element_click'

    trackCustomEvent(eventType, {
      element_id: elementId,
      element_type: elementRef.current.tagName.toLowerCase(),
      click_x: event.clientX,
      click_y: event.clientY,
      button: event.button,
      ...additionalData
    })

    // Call original onClick if it exists
    if (children.props.onClick) {
      children.props.onClick(event)
    }
  }

  // Track hover events
  const handleMouseEnter = (event: React.MouseEvent<HTMLElement>) => {
    if (!trackHovers || !elementRef.current) return

    hoverStartTime.current = Date.now()
    const elementId = getElementId(elementRef.current)
    const eventType = eventPrefix ? `${eventPrefix}_hover_start` : 'element_hover_start'

    trackCustomEvent(eventType, {
      element_id: elementId,
      element_type: elementRef.current.tagName.toLowerCase(),
      ...additionalData
    })

    // Call original onMouseEnter if it exists
    if (children.props.onMouseEnter) {
      children.props.onMouseEnter(event)
    }
  }

  const handleMouseLeave = (event: React.MouseEvent<HTMLElement>) => {
    if (!trackHovers || !elementRef.current) return

    const hoverDuration = hoverStartTime.current > 0 ? Date.now() - hoverStartTime.current : 0
    const elementId = getElementId(elementRef.current)
    const eventType = eventPrefix ? `${eventPrefix}_hover_end` : 'element_hover_end'

    trackCustomEvent(eventType, {
      element_id: elementId,
      element_type: elementRef.current.tagName.toLowerCase(),
      hover_duration: hoverDuration,
      ...additionalData
    })

    hoverStartTime.current = 0

    // Call original onMouseLeave if it exists
    if (children.props.onMouseLeave) {
      children.props.onMouseLeave(event)
    }
  }

  // Track focus events
  const handleFocus = (event: React.FocusEvent<HTMLElement>) => {
    if (!trackFocus || !elementRef.current) return

    focusStartTime.current = Date.now()
    const elementId = getElementId(elementRef.current)
    const eventType = eventPrefix ? `${eventPrefix}_focus` : 'element_focus'

    trackCustomEvent(eventType, {
      element_id: elementId,
      element_type: elementRef.current.tagName.toLowerCase(),
      ...additionalData
    })

    // Call original onFocus if it exists
    if (children.props.onFocus) {
      children.props.onFocus(event)
    }
  }

  const handleBlur = (event: React.FocusEvent<HTMLElement>) => {
    if (!trackFocus || !elementRef.current) return

    const focusDuration = focusStartTime.current > 0 ? Date.now() - focusStartTime.current : 0
    const elementId = getElementId(elementRef.current)
    const eventType = eventPrefix ? `${eventPrefix}_blur` : 'element_blur'

    trackCustomEvent(eventType, {
      element_id: elementId,
      element_type: elementRef.current.tagName.toLowerCase(),
      focus_duration: focusDuration,
      ...additionalData
    })

    focusStartTime.current = 0

    // Call original onBlur if it exists
    if (children.props.onBlur) {
      children.props.onBlur(event)
    }
  }

  // Clone the child element with tracking props
  const trackedChild = cloneElement(children, {
    ref: elementRef,
    ...(trackClicks && { onClick: handleClick }),
    ...(trackHovers && { 
      onMouseEnter: handleMouseEnter,
      onMouseLeave: handleMouseLeave 
    }),
    ...(trackFocus && { 
      onFocus: handleFocus,
      onBlur: handleBlur 
    })
  })

  return trackedChild
}

export default InteractionTracker
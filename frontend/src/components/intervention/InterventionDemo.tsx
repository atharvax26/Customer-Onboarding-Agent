import React, { useState } from 'react'
import HelpMessage from './HelpMessage'
import InterventionSystem from './InterventionSystem'
import HelpTrigger from './HelpTrigger'
import { HelpMessage as HelpMessageType, InterventionFeedback } from '../../types/intervention'

/**
 * Demo component to showcase the intervention system components
 * This is for testing and demonstration purposes
 */
const InterventionDemo: React.FC = () => {
  const [showDemo, setShowDemo] = useState(false)
  const [demoMessages, setDemoMessages] = useState<HelpMessageType[]>([])

  const sampleMessages: HelpMessageType[] = [
    {
      message_id: 'demo-contextual-1',
      content: 'Having trouble with API authentication? Check that your API key is correctly formatted and has the right permissions. You can find your API key in the developer console.',
      message_type: 'contextual_help',
      context: {
        step_number: 1,
        step_title: 'API Authentication Setup',
        user_role: 'Developer',
        engagement_score: 25
      },
      dismissible: true
    },
    {
      message_id: 'demo-low-engagement-1',
      content: 'We notice you might need extra support. This step is important for your developer workflow. Take your time and don\'t hesitate to explore the available options.',
      message_type: 'low_engagement_help',
      context: {
        step_number: 2,
        step_title: 'Making Your First API Call',
        user_role: 'Developer',
        engagement_score: 15
      },
      dismissible: true
    },
    {
      message_id: 'demo-generic-1',
      content: 'Need help? We\'re here to assist you with your onboarding journey.',
      message_type: 'generic_help',
      context: {
        step_number: 3,
        user_role: 'Business_User'
      },
      dismissible: true
    }
  ]

  const handleShowDemo = () => {
    setShowDemo(true)
    setDemoMessages(sampleMessages)
  }

  const handleDismissMessage = (messageId: string) => {
    setDemoMessages(prev => prev.filter(msg => msg.message_id !== messageId))
  }

  const handleFeedback = (feedback: InterventionFeedback) => {
    console.log('Demo feedback received:', feedback)
    // In a real app, this would be sent to the API
  }

  const handleClearDemo = () => {
    setDemoMessages([])
    setShowDemo(false)
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Intervention System Demo</h2>
      <p>This demo showcases the contextual help message components.</p>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={handleShowDemo}
          style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            marginRight: '10px'
          }}
        >
          Show Demo Messages
        </button>
        
        <button 
          onClick={handleClearDemo}
          style={{
            background: '#6b7280',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            marginRight: '10px'
          }}
        >
          Clear Demo
        </button>

        <HelpTrigger 
          sessionId={123}
          currentStep={2}
          className="demo-help-trigger"
        />
      </div>

      {showDemo && (
        <div>
          <h3>Sample Help Messages:</h3>
          {demoMessages.map((message) => (
            <HelpMessage
              key={message.message_id}
              helpMessage={message}
              onDismiss={handleDismissMessage}
              onFeedback={handleFeedback}
              interventionId={Math.floor(Math.random() * 1000)}
              sessionId={123}
            />
          ))}
          
          {demoMessages.length === 0 && (
            <p style={{ color: '#6b7280', fontStyle: 'italic' }}>
              All demo messages have been dismissed.
            </p>
          )}
        </div>
      )}

      <div style={{ marginTop: '40px', padding: '20px', background: '#f9fafb', borderRadius: '8px' }}>
        <h3>Component Features:</h3>
        <ul>
          <li><strong>HelpMessage:</strong> Displays contextual help with different styles based on message type</li>
          <li><strong>InterventionSystem:</strong> Monitors engagement and automatically shows help messages</li>
          <li><strong>HelpTrigger:</strong> Manual help request button for users</li>
          <li><strong>Feedback Collection:</strong> Users can rate helpfulness of interventions</li>
          <li><strong>Dismissible Messages:</strong> Users can close help messages when done</li>
          <li><strong>Responsive Design:</strong> Works on mobile and desktop</li>
          <li><strong>Accessibility:</strong> Supports high contrast and reduced motion preferences</li>
        </ul>
      </div>
    </div>
  )
}

export default InterventionDemo
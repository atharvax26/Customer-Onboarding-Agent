"""
Gemini AI client for document processing and onboarding guide generation
Uses the new google-genai package (google.generativeai is deprecated)
"""

import os
import logging
import json
from typing import Dict, List, Any
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini AI API using new google-genai package"""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini AI client with new API"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini with new API
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = 'gemini-2.5-flash'  # Latest stable model
        
        logger.info(f"Gemini AI client initialized successfully with model: {self.model_name}")
    
    async def generate_onboarding_guide(
        self, 
        document_content: str, 
        user_role: str = "Developer"
    ) -> Dict[str, Any]:
        """
        Generate a step-by-step onboarding guide from document content
        
        Args:
            document_content: The full text content of the document
            user_role: The role of the user (Developer, Business_User, Admin)
            
        Returns:
            Dictionary with summary and step-by-step tasks
        """
        try:
            # Truncate content if too long to avoid timeouts
            max_content_length = 8000
            truncated_content = document_content[:max_content_length]
            if len(document_content) > max_content_length:
                logger.warning(f"Document truncated from {len(document_content)} to {max_content_length} characters")
            
            # Create a detailed prompt for Gemini
            prompt = f"""
You are an expert onboarding guide creator. Analyze the following document and create a comprehensive, step-by-step onboarding guide.

Document Content:
{truncated_content}

User Role: {user_role}

Please create:
1. A concise summary of the document (2-3 sentences)
2. A step-by-step onboarding guide with 5-7 steps

For each step, provide:
- A clear, action-oriented title
- A detailed description (2-3 sentences) explaining what the user needs to do
- Estimated time in minutes
- 2-3 specific subtasks or action items
- A helpful tip or best practice for completing this step

Format your response as JSON with this exact structure:
{{
  "summary": "Brief summary of the document",
  "steps": [
    {{
      "step": 1,
      "title": "Step title",
      "description": "Detailed description of what to do",
      "estimated_time": 10,
      "subtasks": [
        "First specific action",
        "Second specific action",
        "Third specific action"
      ],
      "tip": "A helpful tip or best practice for this step"
    }}
  ]
}}

Make the guide practical, actionable, and tailored to a {user_role} role.
Focus on the most important concepts and actions from the document.
IMPORTANT: Return ONLY valid JSON, no markdown formatting or extra text.
"""

            # Generate content with Gemini using new API
            logger.info(f"Generating onboarding guide for {user_role} role...")
            
            # Configure generation parameters
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
                response_mime_type="application/json"  # Request JSON response
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            # Parse the response
            response_text = response.text.strip()
            logger.info(f"Received response from Gemini ({len(response_text)} characters)")
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate the structure
            if "summary" not in result or "steps" not in result:
                logger.warning("Response missing required fields, using fallback")
                return self._create_fallback_guide(document_content, user_role)
            
            logger.info(f"Successfully generated {len(result.get('steps', []))} steps")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.error(f"Response text preview: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
            
            # Fallback: create structured data from text response
            return self._create_fallback_guide(document_content, user_role)
            
        except Exception as e:
            logger.error(f"Error generating onboarding guide: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Return fallback guide instead of raising error
            logger.info("Using fallback guide due to error")
            return self._create_fallback_guide(document_content, user_role)
    
    def _create_fallback_guide(self, content: str, role: str) -> Dict[str, Any]:
        """Create a basic guide if JSON parsing fails"""
        content_preview = content[:500] if len(content) > 500 else content
        
        return {
            "summary": f"This document provides important information for {role}s. Review the content carefully to understand the key concepts and procedures.",
            "steps": [
                {
                    "step": 1,
                    "title": "Review Document Overview",
                    "description": f"Read through the document to understand its purpose and scope. {content_preview}",
                    "estimated_time": 10,
                    "subtasks": [
                        "Read the introduction and overview sections",
                        "Identify the main topics covered",
                        "Note any prerequisites or requirements"
                    ],
                    "tip": "Take notes as you read to help retain key information and create a quick reference guide."
                },
                {
                    "step": 2,
                    "title": "Understand Key Concepts",
                    "description": "Focus on the core concepts and terminology used in the document.",
                    "estimated_time": 15,
                    "subtasks": [
                        "Review technical terms and definitions",
                        "Understand the main features or components",
                        "Note important relationships and dependencies"
                    ],
                    "tip": "Create a glossary of terms to reference later. Understanding the vocabulary is crucial for success."
                },
                {
                    "step": 3,
                    "title": "Follow Setup Instructions",
                    "description": "Complete any setup or configuration steps described in the document.",
                    "estimated_time": 20,
                    "subtasks": [
                        "Gather required tools and resources",
                        "Follow installation or setup procedures",
                        "Verify the setup is working correctly"
                    ],
                    "tip": "Document your setup process as you go. This will help you troubleshoot issues and onboard others later."
                },
                {
                    "step": 4,
                    "title": "Practice with Examples",
                    "description": "Work through examples and tutorials provided in the document.",
                    "estimated_time": 25,
                    "subtasks": [
                        "Try the basic examples first",
                        "Experiment with different options",
                        "Troubleshoot any issues that arise"
                    ],
                    "tip": "Don't just copy examples - modify them to understand how they work. Experimentation leads to deeper learning."
                },
                {
                    "step": 5,
                    "title": "Apply to Your Use Case",
                    "description": "Adapt what you've learned to your specific needs and workflow.",
                    "estimated_time": 30,
                    "subtasks": [
                        "Identify how this applies to your work",
                        "Create a plan for implementation",
                        "Start with a small pilot or proof of concept"
                    ],
                    "tip": "Start small and iterate. A working prototype is better than a perfect plan that never gets implemented."
                }
            ]
        }
    
    async def generate_summary(self, document_content: str) -> str:
        """Generate a concise summary of the document"""
        try:
            prompt = f"""
Provide a concise 2-3 sentence summary of the following document:

{document_content[:5000]}

Summary:
"""
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=256
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Summary of document ({len(document_content)} characters)"

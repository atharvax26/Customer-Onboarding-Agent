"""
Claude API client for document processing
Handles single-call document processing with retry logic and structured prompts
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import os

from anthropic import AsyncAnthropic
from anthropic.types import Message
from anthropic._exceptions import (
    RateLimitError, 
    APIError, 
    AuthenticationError,
    BadRequestError,
    InternalServerError
)

from fastapi import HTTPException


logger = logging.getLogger(__name__)


class ClaudeAPIClient:
    """Client for interacting with Claude API for document processing"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude API client
        
        Args:
            api_key: Anthropic API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter is required")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        
        # Configuration
        self.model = "claude-3-haiku-20240307"  # Fast and cost-effective model
        self.max_tokens = 4000
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        self.max_delay = 60.0  # Maximum delay between retries
    
    async def process_document_single_call(
        self, 
        content: str, 
        filename: str = "document"
    ) -> Dict[str, Any]:
        """
        Process document content in a single Claude API call
        
        Args:
            content: Document text content
            filename: Original filename for context
            
        Returns:
            Dictionary with 'summary' and 'tasks' keys
            
        Raises:
            HTTPException: If processing fails after retries
        """
        start_time = datetime.utcnow()
        
        try:
            # Build structured prompt for single-call processing
            prompt = self._build_processing_prompt(content, filename)
            
            # Make API call with retry logic
            response = await self._make_request_with_retry(prompt)
            
            # Parse and validate response
            result = self._parse_response(response)
            
            # Add processing metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result['processing_time'] = processing_time
            result['model_used'] = self.model
            result['processed_at'] = start_time.isoformat()
            
            logger.info(f"Successfully processed document '{filename}' in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process document '{filename}': {str(e)}")
            raise
    
    def _build_processing_prompt(self, content: str, filename: str) -> str:
        """
        Build structured prompt for document processing
        
        Args:
            content: Document content
            filename: Original filename
            
        Returns:
            Formatted prompt string
        """
        # Calculate target summary length (25% of original)
        original_length = len(content)
        target_summary_length = max(100, int(original_length * 0.25))
        
        prompt = f"""You are a document processing assistant. Your task is to analyze the provided document and extract two key outputs in a single response:

1. **Summary**: Create a concise summary that captures the main points and key information from the document. The summary should be approximately {target_summary_length} characters (about 25% of the original length).

2. **Step-by-Step Tasks**: Extract actionable tasks, procedures, or steps that users should follow based on the document content. Focus on concrete, implementable actions.

**Document to Process:**
Filename: {filename}
Content Length: {original_length} characters

---
{content}
---

**Required Output Format:**
Please respond with a valid JSON object containing exactly these two fields:

```json
{{
    "summary": "Your concise summary here (approximately {target_summary_length} characters)",
    "tasks": [
        "First actionable task or step",
        "Second actionable task or step",
        "Additional tasks as needed"
    ]
}}
```

**Important Instructions:**
- Ensure the response is valid JSON that can be parsed
- The summary should be informative but concise
- Tasks should be specific and actionable
- Include 3-8 tasks depending on document complexity
- Focus on the most important information and actions
- Do not include any text outside the JSON response"""

        return prompt
    
    async def _make_request_with_retry(self, prompt: str) -> Message:
        """
        Make API request with exponential backoff retry logic
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            Claude API response message
            
        Raises:
            HTTPException: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making Claude API request (attempt {attempt + 1}/{self.max_retries})")
                
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                logger.debug("Claude API request successful")
                return response
                
            except RateLimitError as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    logger.error(f"Rate limit exceeded after {self.max_retries} attempts")
                    raise HTTPException(
                        status_code=429,
                        detail="Claude API rate limit exceeded. Please try again later."
                    )
                
                # Exponential backoff with jitter
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                jitter = delay * 0.1  # Add 10% jitter
                total_delay = delay + jitter
                
                logger.warning(f"Rate limit hit, retrying in {total_delay:.2f}s (attempt {attempt + 1})")
                await asyncio.sleep(total_delay)
                
            except AuthenticationError as e:
                logger.error(f"Claude API authentication failed: {str(e)}")
                raise HTTPException(
                    status_code=401,
                    detail="Claude API authentication failed. Please check your API key."
                )
                
            except BadRequestError as e:
                logger.error(f"Claude API bad request: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid request to Claude API: {str(e)}"
                )
                
            except InternalServerError as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    logger.error(f"Claude API internal server error after {self.max_retries} attempts")
                    raise HTTPException(
                        status_code=502,
                        detail="Claude API is temporarily unavailable. Please try again later."
                    )
                
                # Shorter delay for server errors
                delay = min(self.base_delay * (1.5 ** attempt), 30.0)
                logger.warning(f"Server error, retrying in {delay:.2f}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)
                
            except APIError as e:
                last_exception = e
                logger.error(f"Claude API error: {str(e)}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Claude API error: {str(e)}"
                )
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error during Claude API request: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected error during document processing: {str(e)}"
                )
        
        # If we get here, all retries failed
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed after {self.max_retries} attempts: {str(last_exception)}"
        )
    
    def _parse_response(self, response: Message) -> Dict[str, Any]:
        """
        Parse and validate Claude API response
        
        Args:
            response: Claude API response message
            
        Returns:
            Parsed response dictionary
            
        Raises:
            HTTPException: If response parsing fails
        """
        try:
            # Extract text content from response
            if not response.content or len(response.content) == 0:
                raise HTTPException(
                    status_code=502,
                    detail="Empty response from Claude API"
                )
            
            # Get the text content (Claude returns a list of content blocks)
            text_content = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    text_content += content_block.text
            
            if not text_content.strip():
                raise HTTPException(
                    status_code=502,
                    detail="No text content in Claude API response"
                )
            
            # Try to extract JSON from the response
            json_content = self._extract_json_from_text(text_content)
            
            # Validate required fields
            if 'summary' not in json_content:
                raise HTTPException(
                    status_code=502,
                    detail="Claude API response missing 'summary' field"
                )
            
            if 'tasks' not in json_content:
                raise HTTPException(
                    status_code=502,
                    detail="Claude API response missing 'tasks' field"
                )
            
            if not isinstance(json_content['tasks'], list):
                raise HTTPException(
                    status_code=502,
                    detail="Claude API response 'tasks' field must be a list"
                )
            
            # Validate content quality
            if len(json_content['summary'].strip()) < 50:
                raise HTTPException(
                    status_code=502,
                    detail="Claude API returned summary that is too short"
                )
            
            if len(json_content['tasks']) == 0:
                raise HTTPException(
                    status_code=502,
                    detail="Claude API returned no tasks"
                )
            
            logger.debug(f"Successfully parsed response: {len(json_content['summary'])} char summary, {len(json_content['tasks'])} tasks")
            return json_content
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {str(e)}")
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON in Claude API response: {str(e)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing Claude response: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse Claude API response: {str(e)}"
            )
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON content from text response
        
        Args:
            text: Response text that may contain JSON
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        # Try to find JSON in code blocks first
        import re
        
        # Look for JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Try to find JSON object in the text
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(brace_pattern, text, re.DOTALL)
        
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Last resort: try to parse the entire text as JSON
        return json.loads(text.strip())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Claude API
        
        Returns:
            Health status information
        """
        try:
            start_time = datetime.utcnow()
            
            # Simple test request
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[
                    {
                        "role": "user",
                        "content": "Respond with just the word 'healthy' if you can process this message."
                    }
                ]
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "model": self.model,
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat()
            }
"""
ScaleDown.ai API client for document processing
Handles document intelligence and processing with ScaleDown.ai's specialized API
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
import httpx

from fastapi import HTTPException


logger = logging.getLogger(__name__)


class ScaleDownAIClient:
    """Client for interacting with ScaleDown.ai API for document processing"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ScaleDown.ai API client
        
        Args:
            api_key: ScaleDown.ai API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("SCALEDOWN_API_KEY")
        if not self.api_key:
            raise ValueError("SCALEDOWN_API_KEY environment variable or api_key parameter is required")
        
        # Configuration
        self.base_url = "https://scaledown.ai/api"  # Try different pattern
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        self.max_delay = 60.0  # Maximum delay between retries
        self.timeout = 120.0  # 2 minutes timeout for document processing
        
        # HTTP client configuration
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "CustomerOnboardingAgent/1.0"
        }
    
    async def process_document_single_call(
        self, 
        content: str, 
        filename: str = "document"
    ) -> Dict[str, Any]:
        """
        Process document content in a single ScaleDown.ai API call
        
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
            # Build request payload for ScaleDown.ai
            payload = self._build_processing_payload(content, filename)
            
            # Make API call with retry logic
            response = await self._make_request_with_retry(payload)
            
            # Parse and validate response
            result = self._parse_response(response)
            
            # Add processing metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result['processing_time'] = processing_time
            result['model_used'] = 'scaledown-ai'
            result['processed_at'] = start_time.isoformat()
            
            logger.info(f"Successfully processed document '{filename}' in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process document '{filename}': {str(e)}")
            raise
    
    def _build_processing_payload(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Build request payload for ScaleDown.ai API
        
        Args:
            content: Document content
            filename: Original filename
            
        Returns:
            Request payload dictionary
        """
        # Calculate target summary length (25% of original)
        original_length = len(content)
        target_summary_length = max(100, int(original_length * 0.25))
        
        payload = {
            "document": {
                "content": content,
                "filename": filename,
                "content_type": "text/plain"
            },
            "processing_options": {
                "extract_summary": True,
                "extract_tasks": True,
                "summary_target_length": target_summary_length,
                "task_format": "actionable_steps",
                "min_tasks": 3,
                "max_tasks": 8
            },
            "output_format": "structured_json"
        }
        
        return payload
    
    async def _make_request_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API request with exponential backoff retry logic
        
        Args:
            payload: Request payload
            
        Returns:
            ScaleDown.ai API response
            
        Raises:
            HTTPException: If all retries fail
        """
        last_exception = None
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"Making ScaleDown.ai API request (attempt {attempt + 1}/{self.max_retries})")
                    
                    response = await client.post(
                        f"{self.base_url}/process/document",
                        json=payload,
                        headers=self.headers
                    )
                    
                    # Handle different HTTP status codes
                    if response.status_code == 200:
                        logger.debug("ScaleDown.ai API request successful")
                        return response.json()
                    
                    elif response.status_code == 429:
                        # Rate limit
                        last_exception = HTTPException(status_code=429, detail="Rate limit exceeded")
                        if attempt == self.max_retries - 1:
                            logger.error(f"Rate limit exceeded after {self.max_retries} attempts")
                            raise HTTPException(
                                status_code=429,
                                detail="ScaleDown.ai API rate limit exceeded. Please try again later."
                            )
                        
                        # Exponential backoff with jitter
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        jitter = delay * 0.1  # Add 10% jitter
                        total_delay = delay + jitter
                        
                        logger.warning(f"Rate limit hit, retrying in {total_delay:.2f}s (attempt {attempt + 1})")
                        await asyncio.sleep(total_delay)
                        continue
                    
                    elif response.status_code == 401:
                        logger.error("ScaleDown.ai API authentication failed")
                        raise HTTPException(
                            status_code=401,
                            detail="ScaleDown.ai API authentication failed. Please check your API key."
                        )
                    
                    elif response.status_code == 400:
                        error_detail = "Invalid request"
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("error", error_detail)
                        except:
                            pass
                        
                        logger.error(f"ScaleDown.ai API bad request: {error_detail}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid request to ScaleDown.ai API: {error_detail}"
                        )
                    
                    elif response.status_code >= 500:
                        # Server error - retry
                        last_exception = HTTPException(status_code=502, detail="Server error")
                        if attempt == self.max_retries - 1:
                            logger.error(f"ScaleDown.ai API server error after {self.max_retries} attempts")
                            raise HTTPException(
                                status_code=502,
                                detail="ScaleDown.ai API is temporarily unavailable. Please try again later."
                            )
                        
                        # Shorter delay for server errors
                        delay = min(self.base_delay * (1.5 ** attempt), 30.0)
                        logger.warning(f"Server error, retrying in {delay:.2f}s (attempt {attempt + 1})")
                        await asyncio.sleep(delay)
                        continue
                    
                    else:
                        # Other error
                        error_detail = f"HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            error_detail = error_data.get("error", error_detail)
                        except:
                            pass
                        
                        raise HTTPException(
                            status_code=502,
                            detail=f"ScaleDown.ai API error: {error_detail}"
                        )
                        
                except httpx.TimeoutException:
                    last_exception = HTTPException(status_code=504, detail="Request timeout")
                    if attempt == self.max_retries - 1:
                        logger.error(f"Request timeout after {self.max_retries} attempts")
                        raise HTTPException(
                            status_code=504,
                            detail="ScaleDown.ai API request timed out. Please try again."
                        )
                    
                    delay = min(self.base_delay * (1.5 ** attempt), 30.0)
                    logger.warning(f"Request timeout, retrying in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    
                except httpx.NetworkError as e:
                    last_exception = e
                    if attempt == self.max_retries - 1:
                        logger.error(f"Network error after {self.max_retries} attempts: {str(e)}")
                        raise HTTPException(
                            status_code=503,
                            detail="Network error connecting to ScaleDown.ai API. Please try again."
                        )
                    
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Network error, retrying in {delay:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    
                except HTTPException:
                    raise
                    
                except Exception as e:
                    last_exception = e
                    logger.error(f"Unexpected error during ScaleDown.ai API request: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Unexpected error during document processing: {str(e)}"
                    )
        
        # If we get here, all retries failed
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed after {self.max_retries} attempts: {str(last_exception)}"
        )
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate ScaleDown.ai API response
        
        Args:
            response_data: API response data
            
        Returns:
            Parsed response dictionary
            
        Raises:
            HTTPException: If response parsing fails
        """
        try:
            # Check for API-level errors
            if "error" in response_data:
                raise HTTPException(
                    status_code=502,
                    detail=f"ScaleDown.ai API error: {response_data['error']}"
                )
            
            # Extract results from response
            if "results" not in response_data:
                raise HTTPException(
                    status_code=502,
                    detail="Invalid response format from ScaleDown.ai API"
                )
            
            results = response_data["results"]
            
            # Extract summary
            summary = ""
            if "summary" in results:
                if isinstance(results["summary"], dict):
                    summary = results["summary"].get("text", "")
                else:
                    summary = str(results["summary"])
            
            if not summary:
                raise HTTPException(
                    status_code=502,
                    detail="ScaleDown.ai API response missing summary"
                )
            
            # Extract tasks
            tasks = []
            if "tasks" in results:
                if isinstance(results["tasks"], list):
                    tasks = results["tasks"]
                elif isinstance(results["tasks"], dict) and "items" in results["tasks"]:
                    tasks = results["tasks"]["items"]
            
            if not tasks:
                raise HTTPException(
                    status_code=502,
                    detail="ScaleDown.ai API response missing tasks"
                )
            
            # Validate content quality
            if len(summary.strip()) < 50:
                raise HTTPException(
                    status_code=502,
                    detail="ScaleDown.ai API returned summary that is too short"
                )
            
            if len(tasks) == 0:
                raise HTTPException(
                    status_code=502,
                    detail="ScaleDown.ai API returned no tasks"
                )
            
            # Clean up tasks (ensure they're strings)
            cleaned_tasks = []
            for task in tasks:
                if isinstance(task, dict):
                    # If task is an object, extract the text
                    task_text = task.get("text", task.get("description", task.get("title", str(task))))
                    cleaned_tasks.append(task_text)
                else:
                    cleaned_tasks.append(str(task))
            
            result = {
                "summary": summary.strip(),
                "tasks": cleaned_tasks
            }
            
            logger.debug(f"Successfully parsed response: {len(result['summary'])} char summary, {len(result['tasks'])} tasks")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing ScaleDown.ai response: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse ScaleDown.ai API response: {str(e)}"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on ScaleDown.ai API
        
        Returns:
            Health status information
        """
        try:
            start_time = datetime.utcnow()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Simple health check request
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self.headers
                )
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time": response_time,
                        "model": "scaledown-ai",
                        "timestamp": start_time.isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "model": "scaledown-ai",
                        "timestamp": start_time.isoformat()
                    }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": "scaledown-ai",
                "timestamp": datetime.utcnow().isoformat()
            }
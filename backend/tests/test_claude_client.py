"""
Tests for Claude API client functionality
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from anthropic.types import Message, TextBlock, Usage
from anthropic._exceptions import RateLimitError, AuthenticationError, APIError

from app.services.claude_client import ClaudeAPIClient


class TestClaudeAPIClient:
    """Test Claude API client functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock API key for testing
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-api-key'}):
            self.client = ClaudeAPIClient()
    
    def _create_mock_message(self, text_content: str) -> Message:
        """Helper to create properly structured mock Message"""
        text_block = TextBlock(text=text_content, type="text")
        usage = Usage(
            input_tokens=100,
            output_tokens=50,
            cache_creation_input_tokens=None,
            cache_read_input_tokens=None
        )
        
        return Message(
            id="test-id",
            content=[text_block],
            model="claude-3-haiku-20240307",
            role="assistant",
            stop_reason="end_turn",
            stop_sequence=None,
            type="message",
            usage=usage
        )
    
    def test_init_with_api_key(self):
        """Test client initialization with API key"""
        client = ClaudeAPIClient(api_key="test-key")
        assert client.api_key == "test-key"
    
    def test_init_without_api_key(self):
        """Test client initialization fails without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                ClaudeAPIClient()
    
    def test_build_processing_prompt(self):
        """Test prompt generation for document processing"""
        content = "This is test document content for processing."
        filename = "test.txt"
        
        prompt = self.client._build_processing_prompt(content, filename)
        
        assert filename in prompt
        assert "summary" in prompt.lower()
        assert "tasks" in prompt.lower()
        assert "json" in prompt.lower()
        assert str(len(content)) in prompt
    
    def test_extract_json_from_text_code_block(self):
        """Test JSON extraction from code block"""
        text = '''Here is the response:
        
        ```json
        {
            "summary": "Test summary",
            "tasks": ["Task 1", "Task 2"]
        }
        ```
        
        That's the result.'''
        
        result = self.client._extract_json_from_text(text)
        
        assert result["summary"] == "Test summary"
        assert result["tasks"] == ["Task 1", "Task 2"]
    
    def test_extract_json_from_text_plain_json(self):
        """Test JSON extraction from plain text"""
        text = '{"summary": "Plain JSON", "tasks": ["Task A"]}'
        
        result = self.client._extract_json_from_text(text)
        
        assert result["summary"] == "Plain JSON"
        assert result["tasks"] == ["Task A"]
    
    def test_extract_json_from_text_embedded_json(self):
        """Test JSON extraction from embedded JSON in text"""
        text = '''The analysis shows that {"summary": "Embedded summary", "tasks": ["Embedded task"]} is the result.'''
        
        result = self.client._extract_json_from_text(text)
        
        assert result["summary"] == "Embedded summary"
        assert result["tasks"] == ["Embedded task"]
    
    def test_extract_json_invalid(self):
        """Test JSON extraction failure with invalid JSON"""
        text = "This is not JSON at all"
        
        with pytest.raises(json.JSONDecodeError):
            self.client._extract_json_from_text(text)
    
    @pytest.mark.asyncio
    async def test_parse_response_success(self):
        """Test successful response parsing"""
        mock_response = self._create_mock_message('{"summary": "This is a comprehensive test summary that is long enough to pass validation", "tasks": ["Task 1", "Task 2"]}')
        
        result = self.client._parse_response(mock_response)
        
        assert "This is a comprehensive test summary" in result["summary"]
        assert result["tasks"] == ["Task 1", "Task 2"]
    
    @pytest.mark.asyncio
    async def test_parse_response_missing_summary(self):
        """Test response parsing failure with missing summary"""
        mock_response = self._create_mock_message('{"tasks": ["Task 1"]}')
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self.client._parse_response(mock_response)
        
        assert exc_info.value.status_code == 502
        assert "missing 'summary' field" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_parse_response_missing_tasks(self):
        """Test response parsing failure with missing tasks"""
        mock_response = self._create_mock_message('{"summary": "Test summary"}')
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self.client._parse_response(mock_response)
        
        assert exc_info.value.status_code == 502
        assert "missing 'tasks' field" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_parse_response_short_summary(self):
        """Test response parsing failure with too short summary"""
        mock_response = self._create_mock_message('{"summary": "Short", "tasks": ["Task 1"]}')
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self.client._parse_response(mock_response)
        
        assert exc_info.value.status_code == 502
        assert "summary that is too short" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_parse_response_empty_tasks(self):
        """Test response parsing failure with empty tasks"""
        mock_response = self._create_mock_message('{"summary": "This is a long enough summary for testing purposes", "tasks": []}')
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            self.client._parse_response(mock_response)
        
        assert exc_info.value.status_code == 502
        assert "returned no tasks" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_success(self):
        """Test successful API request"""
        mock_response = self._create_mock_message('{"summary": "Test summary", "tasks": ["Task 1"]}')
        
        with patch.object(self.client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await self.client._make_request_with_retry("test prompt")
            
            assert result == mock_response
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_rate_limit(self):
        """Test retry logic with rate limit error"""
        with patch.object(self.client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            # First two calls raise rate limit, third succeeds
            success_response = self._create_mock_message('{"summary": "This is a comprehensive test summary that is long enough to pass validation", "tasks": ["Task 1"]}')
            
            # Create mock response objects for exceptions
            mock_response = MagicMock()
            mock_response.request = MagicMock()
            
            mock_create.side_effect = [
                RateLimitError("Rate limit exceeded", response=mock_response, body=None),
                RateLimitError("Rate limit exceeded", response=mock_response, body=None),
                success_response
            ]
            
            # Mock sleep to speed up test
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await self.client._make_request_with_retry("test prompt")
            
            assert result == success_response
            assert mock_create.call_count == 3
    
    @pytest.mark.asyncio
    async def test_make_request_with_retry_auth_error(self):
        """Test authentication error handling"""
        with patch.object(self.client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            # Create mock response object for exception
            mock_response = MagicMock()
            mock_response.request = MagicMock()
            
            mock_create.side_effect = AuthenticationError("Invalid API key", response=mock_response, body=None)
            
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await self.client._make_request_with_retry("test prompt")
            
            assert exc_info.value.status_code == 401
            assert "authentication failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_process_document_single_call_success(self):
        """Test successful document processing"""
        content = "This is a test document with enough content to process properly."
        filename = "test.txt"
        
        # Mock the API call
        mock_response = self._create_mock_message(
            '{"summary": "This is a comprehensive summary of the test document content", "tasks": ["Review document", "Extract key points"]}'
        )
        
        with patch.object(self.client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await self.client.process_document_single_call(content, filename)
            
            assert "summary" in result
            assert "tasks" in result
            assert "processing_time" in result
            assert "model_used" in result
            assert result["model_used"] == self.client.model
            assert len(result["tasks"]) > 0
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        mock_response = self._create_mock_message("healthy")
        
        with patch.object(self.client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await self.client.health_check()
            
            assert result["status"] == "healthy"
            assert "response_time" in result
            assert result["model"] == self.client.model
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure"""
        with patch.object(self.client.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            # Create mock request object for exception
            mock_request = MagicMock()
            mock_create.side_effect = APIError("API Error", request=mock_request, body=None)
            
            result = await self.client.health_check()
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert result["model"] == self.client.model
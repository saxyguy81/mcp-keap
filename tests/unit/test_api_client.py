"""
Unit tests for the Keap API client with comprehensive coverage.
"""

import os
import time
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.client import (
    KeapApiService, 
    create_keap_client, 
    create_keap_v2_client,
    KeapClient,
    KeapV2Client
)


class TestKeapApiServiceInit:
    """Test API service initialization."""
    
    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        client = KeapApiService(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.api_version == "v1"
        assert client.base_url == "https://api.infusionsoft.com/crm/rest/v1"
    
    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "env_key"}):
            client = KeapApiService()
            assert client.api_key == "env_key"
    
    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="KEAP_API_KEY must be provided"):
                KeapApiService()
    
    def test_init_with_v2_api(self):
        """Test initialization with API v2."""
        client = KeapApiService(api_key="test_key", api_version="v2")
        assert client.api_version == "v2"
        assert client.base_url == "https://api.infusionsoft.com/crm/rest/v2"
    
    def test_session_configuration(self):
        """Test that HTTP session is properly configured."""
        client = KeapApiService(api_key="test_key")
        assert str(client.session.base_url) == "https://api.infusionsoft.com/crm/rest/v1/"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test_key"
        assert client.session.headers["Content-Type"] == "application/json"
    
    def test_diagnostics_initialization(self):
        """Test that diagnostics are properly initialized."""
        client = KeapApiService(api_key="test_key")
        assert client.diagnostics["total_requests"] == 0
        assert client.diagnostics["successful_requests"] == 0
        assert client.diagnostics["failed_requests"] == 0
        assert "endpoints_called" in client.diagnostics
        assert "error_counts" in client.diagnostics


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_should_rate_limit_daily_limit(self):
        """Test daily rate limit check."""
        client = KeapApiService(api_key="test_key")
        client.daily_request_count = 25000
        assert client._should_rate_limit() is True
    
    def test_should_rate_limit_time_gap(self):
        """Test minimum time gap rate limiting."""
        client = KeapApiService(api_key="test_key")
        client.last_request_time = time.time()
        assert client._should_rate_limit() is True
    
    def test_should_rate_limit_remaining_low(self):
        """Test rate limiting when remaining requests are low."""
        client = KeapApiService(api_key="test_key")
        client.rate_limit_remaining = 5
        assert client._should_rate_limit() is True
    
    def test_should_not_rate_limit_normal_conditions(self):
        """Test no rate limiting under normal conditions."""
        client = KeapApiService(api_key="test_key")
        client.last_request_time = time.time() - 1  # 1 second ago
        client.rate_limit_remaining = 100
        client.daily_request_count = 100
        assert client._should_rate_limit() is False
    
    @pytest.mark.asyncio
    async def test_wait_for_rate_limit(self):
        """Test rate limit waiting."""
        client = KeapApiService(api_key="test_key")
        client.last_request_time = time.time()  # Recent request
        
        start_time = time.time()
        await client._wait_for_rate_limit()
        elapsed = time.time() - start_time
        
        # Should wait at least 0.1 seconds
        assert elapsed >= 0.05  # Allow for timing variance


class TestDiagnostics:
    """Test diagnostic functionality."""
    
    def test_update_diagnostics_success(self):
        """Test updating diagnostics for successful request."""
        client = KeapApiService(api_key="test_key")
        client._update_diagnostics("/test", success=True, response_time=0.5)
        
        assert client.diagnostics["total_requests"] == 1
        assert client.diagnostics["successful_requests"] == 1
        assert client.diagnostics["failed_requests"] == 0
        assert client.diagnostics["endpoints_called"]["/test"] == 1
        assert client.diagnostics["average_response_time"] == 0.5
    
    def test_update_diagnostics_failure(self):
        """Test updating diagnostics for failed request."""
        client = KeapApiService(api_key="test_key")
        client._update_diagnostics("/test", success=False, response_time=1.0, error="HTTP_500")
        
        assert client.diagnostics["total_requests"] == 1
        assert client.diagnostics["successful_requests"] == 0
        assert client.diagnostics["failed_requests"] == 1
        assert client.diagnostics["error_counts"]["HTTP_500"] == 1
    
    def test_update_diagnostics_retry(self):
        """Test updating diagnostics for retried request."""
        client = KeapApiService(api_key="test_key")
        client._update_diagnostics("/test", success=True, response_time=0.8, was_retry=True)
        
        assert client.diagnostics["retried_requests"] == 1
    
    def test_get_diagnostics(self):
        """Test getting comprehensive diagnostics."""
        client = KeapApiService(api_key="test_key")
        client._update_diagnostics("/test", success=True, response_time=0.5)
        
        diagnostics = client.get_diagnostics()
        
        assert "rate_limit_remaining" in diagnostics
        assert "daily_requests_remaining" in diagnostics
        assert "uptime_hours" in diagnostics
        assert "requests_per_hour" in diagnostics
        assert diagnostics["total_requests"] == 1


class TestSessionManagement:
    """Test session management functionality."""
    
    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing the HTTP session."""
        client = KeapApiService(api_key="test_key")
        client.session.aclose = AsyncMock()
        
        await client.close()
        client.session.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality."""
        async with KeapApiService(api_key="test_key") as client:
            assert isinstance(client, KeapApiService)
        # Session should be closed after exiting context


class TestRequestMaking:
    """Test HTTP request making with mocked responses."""
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful HTTP request."""
        client = KeapApiService(api_key="test_key")
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            response = await client._make_request("GET", "/test")
            
            assert response == mock_response
            mock_request.assert_called_once_with("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limited(self):
        """Test handling of rate limited response."""
        client = KeapApiService(api_key="test_key")
        
        # Mock rate limited response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "1"}
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # First call returns 429, second call returns 200
                mock_response_success = MagicMock()
                mock_response_success.status_code = 200
                mock_response_success.headers = {}
                
                mock_request.side_effect = [mock_response, mock_response_success]
                
                response = await client._make_request("GET", "/test")
                
                assert response == mock_response_success
                mock_sleep.assert_called_with(1)  # Should sleep for Retry-After duration
    
    @pytest.mark.asyncio
    async def test_make_request_server_error_retry(self):
        """Test retry logic for server errors."""
        client = KeapApiService(api_key="test_key")
        client.max_retries = 1
        
        mock_response_error = MagicMock()
        mock_response_error.status_code = 500
        mock_response_error.headers = {}
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.headers = {}
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                mock_request.side_effect = [mock_response_error, mock_response_success]
                
                response = await client._make_request("GET", "/test")
                
                assert response == mock_response_success
                assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_make_request_client_error_no_retry(self):
        """Test that client errors (4xx) are not retried."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(httpx.HTTPStatusError):
                await client._make_request("GET", "/test")
            
            # Should only be called once (no retry)
            assert mock_request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_make_request_network_error_retry(self):
        """Test retry logic for network errors."""
        client = KeapApiService(api_key="test_key")
        client.max_retries = 1
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                # First call raises NetworkError, second succeeds
                mock_request.side_effect = [
                    httpx.NetworkError("Connection failed"),
                    mock_response
                ]
                
                response = await client._make_request("GET", "/test")
                
                assert response == mock_response
                assert mock_request.call_count == 2


class TestAPIEndpoints:
    """Test API endpoint methods with mocked responses."""
    
    @pytest.mark.asyncio
    async def test_get_contacts(self):
        """Test get_contacts method."""
        client = KeapApiService(api_key="test_key")
        
        mock_data = {"contacts": [{"id": 1, "name": "Test"}]}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_data
            
            result = await client.get_contacts(limit=50, offset=10)
            
            assert result == mock_data
            mock_get.assert_called_once_with('/contacts', {'limit': 50, 'offset': 10})
    
    @pytest.mark.asyncio
    async def test_get_contact(self):
        """Test get_contact method."""
        client = KeapApiService(api_key="test_key")
        
        mock_data = {"id": 123, "name": "Test Contact"}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_data
            
            result = await client.get_contact("123")
            
            assert result == mock_data
            mock_get.assert_called_once_with('/contacts/123')
    
    @pytest.mark.asyncio
    async def test_create_contact(self):
        """Test create_contact method."""
        client = KeapApiService(api_key="test_key")
        
        contact_data = {"given_name": "John", "family_name": "Doe"}
        mock_response = {"id": 123, **contact_data}
        
        with patch.object(client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.create_contact(contact_data)
            
            assert result == mock_response
            mock_post.assert_called_once_with('/contacts', contact_data)
    
    @pytest.mark.asyncio
    async def test_update_contact(self):
        """Test update_contact method."""
        client = KeapApiService(api_key="test_key")
        
        contact_data = {"given_name": "Jane"}
        mock_response = {"id": 123, **contact_data}
        
        with patch.object(client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response
            
            result = await client.update_contact("123", contact_data)
            
            assert result == mock_response
            mock_put.assert_called_once_with('/contacts/123', contact_data)
    
    @pytest.mark.asyncio
    async def test_update_contact_custom_field_success(self):
        """Test successful custom field update."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = {"id": 123}
        
        with patch.object(client, 'patch', new_callable=AsyncMock) as mock_patch:
            mock_patch.return_value = mock_response
            
            result = await client.update_contact_custom_field("123", "7", "VIP")
            
            assert result["success"] is True
            assert result["contact_id"] == "123"
            assert result["field_id"] == "7"
            assert result["value"] == "VIP"
            
            expected_data = {
                'custom_fields': [{'id': 7, 'content': 'VIP'}]
            }
            mock_patch.assert_called_once_with('/contacts/123', expected_data)
    
    @pytest.mark.asyncio
    async def test_update_contact_custom_field_failure(self):
        """Test custom field update failure."""
        client = KeapApiService(api_key="test_key")
        
        with patch.object(client, 'patch', new_callable=AsyncMock) as mock_patch:
            mock_patch.side_effect = Exception("API Error")
            
            result = await client.update_contact_custom_field("123", "7", "VIP")
            
            assert result["success"] is False
            assert "API Error" in result["error"]


class TestTagMethods:
    """Test tag-related API methods."""
    
    @pytest.mark.asyncio
    async def test_get_tags_with_cache_hit(self):
        """Test get_tags with cache hit."""
        client = KeapApiService(api_key="test_key")
        
        # Set up cache
        mock_data = {"tags": [{"id": 1, "name": "Test Tag"}]}
        client._tag_cache = mock_data
        client._tag_cache_timestamp = time.time()
        
        result = await client.get_tags()
        
        assert result == mock_data
        assert client.diagnostics["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_get_tags_with_cache_miss(self):
        """Test get_tags with cache miss."""
        client = KeapApiService(api_key="test_key")
        
        mock_data = {"tags": [{"id": 1, "name": "Test Tag"}]}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_data
            
            result = await client.get_tags(limit=100)
            
            assert result == mock_data
            assert client.diagnostics["cache_misses"] == 1
            assert client._tag_cache == mock_data
            mock_get.assert_called_once_with('/tags', {'limit': 100, 'offset': 0})
    
    @pytest.mark.asyncio
    async def test_get_tag(self):
        """Test get_tag method."""
        client = KeapApiService(api_key="test_key")
        
        mock_data = {"id": 123, "name": "Test Tag"}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_data
            
            result = await client.get_tag("123")
            
            assert result == mock_data
            mock_get.assert_called_once_with('/tags/123')
    
    @pytest.mark.asyncio
    async def test_create_tag(self):
        """Test create_tag method."""
        client = KeapApiService(api_key="test_key")
        
        tag_data = {"name": "New Tag", "description": "Test"}
        mock_response = {"id": 123, **tag_data}
        
        with patch.object(client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.create_tag(tag_data)
            
            assert result == mock_response
            mock_post.assert_called_once_with('/tags', tag_data)


class TestHttpMethods:
    """Test HTTP method implementations."""
    
    @pytest.mark.asyncio
    async def test_get_method(self):
        """Test GET method."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            result = await client.get('/test', {'param': 'value'})
            
            assert result == {"data": "test"}
            mock_make_request.assert_called_once_with("GET", "/test", params={'param': 'value'})
    
    @pytest.mark.asyncio
    async def test_post_method(self):
        """Test POST method."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 123}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            result = await client.post('/test', {'name': 'test'})
            
            assert result == {"id": 123}
            mock_make_request.assert_called_once_with("POST", "/test", json={'name': 'test'})
    
    @pytest.mark.asyncio
    async def test_put_method(self):
        """Test PUT method."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"updated": True}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            result = await client.put('/test', {'name': 'updated'})
            
            assert result == {"updated": True}
            mock_make_request.assert_called_once_with("PUT", "/test", json={'name': 'updated'})
    
    @pytest.mark.asyncio
    async def test_patch_method(self):
        """Test PATCH method."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"patched": True}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            result = await client.patch('/test', {'field': 'value'})
            
            assert result == {"patched": True}
            mock_make_request.assert_called_once_with("PATCH", "/test", json={'field': 'value'})
    
    @pytest.mark.asyncio
    async def test_delete_method_with_content(self):
        """Test DELETE method with content."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.content = b'{"deleted": true}'
        mock_response.json.return_value = {"deleted": True}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            result = await client.delete('/test')
            
            assert result == {"deleted": True}
            mock_make_request.assert_called_once_with("DELETE", "/test")
    
    @pytest.mark.asyncio
    async def test_delete_method_no_content(self):
        """Test DELETE method with no content."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.content = b''
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            result = await client.delete('/test')
            
            assert result == {}
            mock_make_request.assert_called_once_with("DELETE", "/test")


class TestPagination:
    """Test pagination functionality."""
    
    @pytest.mark.asyncio
    async def test_get_paginated_contacts(self):
        """Test paginated retrieval with contacts format."""
        client = KeapApiService(api_key="test_key")
        
        # Mock responses for multiple pages - need full page size to continue
        page1 = {"contacts": [{"id": i} for i in range(1, 201)]}  # 200 items (full page)
        page2 = {"contacts": [{"id": i} for i in range(201, 203)]}  # 2 items (partial page)
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [page1, page2]
            
            result = await client.get_paginated('/contacts', {'filter': 'test'})
            
            assert len(result) == 202
            assert result[0]["id"] == 1
            assert result[201]["id"] == 202
            assert mock_get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_paginated_tags(self):
        """Test paginated retrieval with tags format."""
        client = KeapApiService(api_key="test_key")
        
        # Small page - will stop immediately because < page_size (200)
        page1 = {"tags": [{"id": 1}, {"id": 2}]}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [page1]
            
            result = await client.get_paginated('/tags')
            
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert mock_get.call_count == 1
    
    @pytest.mark.asyncio
    async def test_get_paginated_data_format(self):
        """Test paginated retrieval with data format."""
        client = KeapApiService(api_key="test_key")
        
        page1 = {"data": [{"id": 1}, {"id": 2}]}
        page2 = {"data": []}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [page1, page2]
            
            result = await client.get_paginated('/custom')
            
            assert len(result) == 2
            assert result[0]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_paginated_list_format(self):
        """Test paginated retrieval with direct list format."""
        client = KeapApiService(api_key="test_key")
        
        page1 = [{"id": 1}, {"id": 2}]
        page2 = []
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [page1, page2]
            
            result = await client.get_paginated('/list')
            
            assert len(result) == 2
            assert result[0]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_paginated_with_limit(self):
        """Test paginated retrieval with user-specified limit."""
        client = KeapApiService(api_key="test_key")
        
        page1 = {"contacts": [{"id": 1}, {"id": 2}, {"id": 3}]}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = page1
            
            result = await client.get_paginated('/contacts', limit=2)
            
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 2
    
    @pytest.mark.asyncio
    async def test_get_paginated_fallback_format(self):
        """Test paginated retrieval with fallback to empty list."""
        client = KeapApiService(api_key="test_key")
        
        response = {"unknown_format": "data"}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = response
            
            result = await client.get_paginated('/unknown')
            
            assert result == []


class TestSearchMethods:
    """Test search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_contacts(self):
        """Test contact search functionality."""
        client = KeapApiService(api_key="test_key")
        
        mock_result = {"contacts": [{"id": 1, "email": "test@example.com"}]}
        
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_result
            
            result = await client.search_contacts("test@example.com", limit=50)
            
            expected_params = {
                'email': 'test@example.com',
                'given_name': 'test@example.com',
                'family_name': 'test@example.com',
                'limit': 50
            }
            
            assert result == mock_result
            mock_get.assert_called_once_with('/contacts', expected_params)
    
    @pytest.mark.asyncio
    async def test_get_contacts_by_tag(self):
        """Test getting contacts by tag."""
        client = KeapApiService(api_key="test_key")
        
        mock_contacts = [{"id": 1, "tag_ids": ["123"]}, {"id": 2, "tag_ids": ["123"]}]
        
        with patch.object(client, 'get_paginated', new_callable=AsyncMock) as mock_paginated:
            mock_paginated.return_value = mock_contacts
            
            result = await client.get_contacts_by_tag("123", limit=100)
            
            assert result == mock_contacts
            mock_paginated.assert_called_once_with('/contacts', 
                                                  params={'tag_id': '123'}, 
                                                  limit=100)


class TestTagOperations:
    """Test tag operation methods."""
    
    @pytest.mark.asyncio
    async def test_apply_tag_to_contact_v1(self):
        """Test applying tag to contact with v1 API."""
        client = KeapApiService(api_key="test_key", api_version="v1")
        
        mock_result = {"success": True}
        
        with patch.object(client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_result
            
            result = await client.apply_tag_to_contact("123", "456")
            
            assert result == mock_result
            mock_post.assert_called_once_with('/contacts/123/tags', {'tagId': '456'})
    
    @pytest.mark.asyncio
    async def test_apply_tag_to_contact_v2(self):
        """Test applying tag to contact with v2 API."""
        client = KeapApiService(api_key="test_key", api_version="v2")
        
        mock_result = {"success": True}
        
        with patch.object(client, 'apply_tags_to_contacts', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = mock_result
            
            result = await client.apply_tag_to_contact("123", "456")
            
            assert result == mock_result
            mock_batch.assert_called_once_with(['456'], ['123'])
    
    @pytest.mark.asyncio
    async def test_remove_tag_from_contact(self):
        """Test removing tag from contact."""
        client = KeapApiService(api_key="test_key")
        
        mock_result = {"success": True}
        
        with patch.object(client, 'delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = mock_result
            
            result = await client.remove_tag_from_contact("123", "456")
            
            assert result == mock_result
            mock_delete.assert_called_once_with('/contacts/123/tags/456')
    
    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts_v2(self):
        """Test batch applying tags to contacts with v2 API."""
        client = KeapApiService(api_key="test_key", api_version="v2")
        
        mock_result = {"success": True, "operations": 4}
        
        with patch.object(client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_result
            
            result = await client.apply_tags_to_contacts(["1", "2"], ["101", "102"])
            
            expected_data = {
                'tagIds': ["1", "2"],
                'contactIds': ["101", "102"]
            }
            
            assert result == mock_result
            mock_post.assert_called_once_with('/contacts/tags', expected_data)
    
    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts_v1_error(self):
        """Test that batch tag operations fail with v1 API."""
        client = KeapApiService(api_key="test_key", api_version="v1")
        
        with pytest.raises(ValueError, match="Batch tag operations require API v2"):
            await client.apply_tags_to_contacts(["1"], ["101"])


class TestCacheOperations:
    """Test cache functionality."""
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        client = KeapApiService(api_key="test_key")
        
        # Set up cache data
        client._tag_cache = {"tags": [{"id": 1}]}
        client._tag_cache_timestamp = time.time()
        
        assert client._tag_cache != {}
        assert client._tag_cache_timestamp != 0
        
        client.clear_cache()
        
        assert client._tag_cache == {}
        assert client._tag_cache_timestamp == 0


class TestErrorHandling:
    """Test enhanced error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_make_request_timeout_exhausts_retries(self):
        """Test that timeout errors exhaust retries properly."""
        client = KeapApiService(api_key="test_key")
        client.max_retries = 2
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                mock_request.side_effect = httpx.TimeoutException("Timeout")
                
                with pytest.raises(httpx.TimeoutException):
                    await client._make_request("GET", "/test")
                
                # Should be called max_retries + 1 times
                assert mock_request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_make_request_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        client = KeapApiService(api_key="test_key")
        client.max_retries = 1
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                mock_request.side_effect = RuntimeError("Unexpected error")
                
                with pytest.raises(RuntimeError, match="Unexpected error"):
                    await client._make_request("GET", "/test")
                
                assert mock_request.call_count == 2  # max_retries + 1
    
    @pytest.mark.asyncio
    async def test_make_request_5xx_error_success_after_retry(self):
        """Test 5xx errors succeed after retry."""
        client = KeapApiService(api_key="test_key")
        
        mock_error_response = MagicMock()
        mock_error_response.status_code = 503
        mock_error_response.headers = {}
        
        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.headers = {}
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                mock_request.side_effect = [mock_error_response, mock_success_response]
                
                response = await client._make_request("GET", "/test")
                
                assert response == mock_success_response
                assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_make_request_other_status_codes(self):
        """Test handling of other status codes."""
        client = KeapApiService(api_key="test_key")
        
        mock_response = MagicMock()
        mock_response.status_code = 418  # I'm a teapot
        mock_response.headers = {}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "I'm a teapot", request=MagicMock(), response=mock_response
        )
        
        with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            with pytest.raises(httpx.HTTPStatusError):
                await client._make_request("GET", "/test")


class TestFactoryFunctions:
    """Test factory functions and backward compatibility."""
    
    def test_create_keap_client(self):
        """Test create_keap_client factory function."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_key"}):
            client = create_keap_client()
            
            assert isinstance(client, KeapApiService)
            assert client.api_version == "v1"
            assert client.api_key == "test_key"
    
    def test_create_keap_client_with_key(self):
        """Test create_keap_client with explicit API key."""
        client = create_keap_client("explicit_key")
        
        assert isinstance(client, KeapApiService)
        assert client.api_version == "v1"
        assert client.api_key == "explicit_key"
    
    def test_create_keap_v2_client(self):
        """Test create_keap_v2_client factory function."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_key"}):
            client = create_keap_v2_client()
            
            assert isinstance(client, KeapApiService)
            assert client.api_version == "v2"
            assert client.api_key == "test_key"
    
    def test_keap_client_alias(self):
        """Test KeapClient backward compatibility alias."""
        client = KeapClient(api_key="test_key")
        
        assert isinstance(client, KeapApiService)
        assert client.api_key == "test_key"
    
    def test_keap_v2_client_function(self):
        """Test KeapV2Client backward compatibility function."""
        client = KeapV2Client(api_key="test_key")
        
        assert isinstance(client, KeapApiService)
        assert client.api_version == "v2"
        assert client.api_key == "test_key"


class TestGetApiInfo:
    """Test API info method."""
    
    def test_get_api_info(self):
        """Test get_api_info method."""
        client = KeapApiService(api_key="test_key", api_version="v2")
        
        info = client.get_api_info()
        
        assert info["api_version"] == "v2"
        assert info["base_url"] == "https://api.infusionsoft.com/crm/rest/v2"
        assert "rate_limit_remaining" in info
        assert "cache_entries" in info
        assert "cache_age_seconds" in info
    
    def test_get_api_info_with_cache(self):
        """Test get_api_info with cache data."""
        client = KeapApiService(api_key="test_key")
        
        # Set up cache
        client._tag_cache = {"tags": [{"id": 1}]}
        client._tag_cache_timestamp = time.time() - 100
        
        info = client.get_api_info()
        
        assert info["cache_entries"] == 1
        assert info["cache_age_seconds"] >= 100
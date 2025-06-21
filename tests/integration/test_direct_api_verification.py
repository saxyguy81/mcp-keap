"""
Core API Verification Integration Tests

Essential tests to verify core API connectivity and basic functionality.
Focuses on integration verification without extensive exploration.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock

from src.api.client import KeapApiService
from src.mcp.tools_collections import list_contacts, get_api_diagnostics
from mcp.server.fastmcp import Context


@pytest.fixture
def skip_if_no_api_key():
    """Skip tests if KEAP_API_KEY is not available"""
    api_key = os.getenv('KEAP_API_KEY')
    if not api_key:
        pytest.skip("KEAP_API_KEY not available in environment")


@pytest.fixture
def context():
    """Create MCP context for testing."""
    return Context()


class TestCoreAPIConnectivity:
    """Test core API connectivity and basic operations."""

    @pytest.mark.asyncio
    async def test_api_client_basic_connectivity(self, skip_if_no_api_key):
        """Test that API client can establish basic connectivity."""
        api_client = KeapApiService()
        
        try:
            # Test basic contact endpoint access
            response = await api_client.get_contacts(limit=1)
            
            # Verify response structure
            assert isinstance(response, dict)
            assert "contacts" in response
            
            print(f"API connectivity verified - retrieved {len(response.get('contacts', []))} contacts")
            
        except Exception as e:
            pytest.fail(f"Basic API connectivity failed: {e}")
        finally:
            await api_client.close()

    @pytest.mark.asyncio
    async def test_mcp_tools_api_integration(self, context, skip_if_no_api_key):
        """Test that MCP tools can successfully integrate with API."""
        # Test basic list_contacts functionality
        result = await list_contacts(context, limit=2)
        
        # Verify MCP tool response structure
        assert "collection_id" in result
        assert "count" in result
        assert isinstance(result["count"], int)
        assert result["count"] >= 0
        
        print(f"MCP-API integration verified - collection with {result['count']} contacts")

    @pytest.mark.asyncio
    async def test_api_diagnostics_integration(self, context, skip_if_no_api_key):
        """Test that API diagnostics can gather system information."""
        # Get API diagnostics
        diagnostics = await get_api_diagnostics(context)
        
        # Verify diagnostics structure
        assert "api_diagnostics" in diagnostics
        assert "performance_metrics" in diagnostics
        
        # Verify basic metrics are present
        perf_metrics = diagnostics["performance_metrics"]
        assert "total_requests" in perf_metrics
        assert "success_rate" in perf_metrics
        
        print(f"API diagnostics verified - {perf_metrics['total_requests']} total requests")


class TestAPIErrorHandling:
    """Test API error handling and resilience."""

    @pytest.mark.asyncio
    async def test_invalid_api_key_handling(self, context):
        """Test handling of invalid API credentials."""
        # Mock API client with invalid credentials
        with patch('src.mcp.tools_collections.get_api_client') as mock_get_api:
            mock_api_client = AsyncMock()
            mock_api_client.get_contacts.side_effect = Exception("401 Unauthorized")
            mock_api_client.close = AsyncMock()
            mock_get_api.return_value = mock_api_client
            
            # Should raise an exception for invalid credentials
            with pytest.raises(Exception, match="401 Unauthorized"):
                await list_contacts(context, limit=1)

    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(self, context):
        """Test handling of API rate limits."""
        # Mock API client with rate limit error
        with patch('src.mcp.tools_collections.get_api_client') as mock_get_api:
            mock_api_client = AsyncMock()
            mock_api_client.get_contacts.side_effect = Exception("429 Too Many Requests")
            mock_api_client.close = AsyncMock()
            mock_get_api.return_value = mock_api_client
            
            # Should raise an exception for rate limits
            with pytest.raises(Exception, match="429 Too Many Requests"):
                await list_contacts(context, limit=1)


class TestAPIParameterValidation:
    """Test API parameter validation and edge cases."""

    @pytest.mark.asyncio
    async def test_api_parameter_limits(self, context, skip_if_no_api_key):
        """Test API parameter limits and validation."""
        # Test with minimum parameters
        result = await list_contacts(context, limit=1, offset=0)
        assert result["count"] >= 0
        
        # Test with reasonable parameters
        result = await list_contacts(context, limit=3, offset=0)
        assert result["count"] >= 0
        
        print("API parameter validation passed")

    @pytest.mark.asyncio
    async def test_api_with_filters(self, context, skip_if_no_api_key):
        """Test API integration with basic filters."""
        # Test with simple filter
        filters = [{"field": "email", "operator": "contains", "value": "@"}]
        result = await list_contacts(context, filters=filters, limit=2)
        
        assert "collection_id" in result
        assert "count" in result
        assert result["count"] >= 0
        
        print(f"API filter integration verified - {result['count']} filtered contacts")
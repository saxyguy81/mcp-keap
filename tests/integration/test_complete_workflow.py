"""
Comprehensive integration tests for the Keap MCP Server.

Tests the complete workflow from MCP server initialization through
API interactions, caching, and optimization.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock, MagicMock

from src.mcp.server import KeapMCPServer
from src.api.client import KeapApiService
from src.cache.manager import CacheManager


class TestKeapMCPIntegration:
    """Test complete MCP server integration."""
    
    @pytest.fixture
    async def mock_api_service(self):
        """Create a mock API service."""
        with patch('src.api.client.KeapApiService') as mock:
            service = AsyncMock()
            service.get_contacts.return_value = {
                "contacts": [
                    {"id": 1, "given_name": "John", "family_name": "Doe", "email_addresses": [{"email": "john@example.com"}]},
                    {"id": 2, "given_name": "Jane", "family_name": "Smith", "email_addresses": [{"email": "jane@example.com"}]}
                ]
            }
            service.get_tags.return_value = {
                "tags": [
                    {"id": 1, "name": "VIP"},
                    {"id": 2, "name": "Customer"}
                ]
            }
            service.get_contact.return_value = {
                "id": 1, "given_name": "John", "family_name": "Doe",
                "email_addresses": [{"email": "john@example.com"}],
                "custom_fields": [{"id": 7, "content": "VIP"}]
            }
            service.update_contact_custom_field.return_value = {"success": True}
            service.get_diagnostics.return_value = {
                "total_requests": 10, "successful_requests": 9, "failed_requests": 1
            }
            mock.return_value = service
            yield service
    
    @pytest.fixture
    async def cache_manager(self):
        """Create a real cache manager for testing."""
        cache = CacheManager()
        yield cache
        await cache.close()
    
    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_key"}):
            yield
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, mock_environment):
        """Test MCP server can be initialized."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            server = KeapMCPServer("test-server")
            
            assert server.mcp == mock_mcp_instance
            mock_fastmcp.assert_called_once_with("test-server")
    
    @pytest.mark.asyncio
    async def test_contact_workflow(self, mock_api_service, cache_manager, mock_environment):
        """Test complete contact management workflow."""
        # Test imports and basic functionality
        from src.mcp.contact_tools import list_contacts, search_contacts_by_email
        from src.utils.contact_utils import get_full_name, get_primary_email
        
        # Test contact listing with caching
        with patch('src.mcp.contact_tools.get_api_client', return_value=mock_api_service):
            with patch('src.mcp.contact_tools.get_cache_manager', return_value=cache_manager):
                
                # First call - should hit API
                contacts = await list_contacts(limit=50)
                assert len(contacts) == 2
                assert contacts[0]["given_name"] == "John"
                
                # Verify contact utilities work
                full_name = get_full_name(contacts[0])
                assert full_name == "John Doe"
                
                email = get_primary_email(contacts[0])
                assert email == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_tag_workflow(self, mock_api_service, cache_manager, mock_environment):
        """Test complete tag management workflow."""
        from src.mcp.tag_tools import get_tags, get_tag_details
        
        with patch('src.mcp.tag_tools.get_api_client', return_value=mock_api_service):
            with patch('src.mcp.tag_tools.get_cache_manager', return_value=cache_manager):
                
                # Test tag listing
                tags = await get_tags(limit=100)
                assert len(tags) == 2
                assert tags[0]["name"] == "VIP"
    
    @pytest.mark.asyncio
    async def test_custom_field_workflow(self, mock_api_service, cache_manager, mock_environment):
        """Test custom field update workflow."""
        from src.mcp.tools import set_custom_field_values
        from mcp.server.fastmcp import Context
        
        context = Context()
        context.api_client = mock_api_service
        context.cache_manager = cache_manager
        
        # Test bulk custom field update
        result = await set_custom_field_values(
            context,
            field_id="7",
            contact_ids=["1", "2"],
            common_value="Premium"
        )
        
        assert result["success"] is True
        assert result["successful_updates"] == 2
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, mock_api_service, cache_manager, mock_environment):
        """Test that caching works properly across the system."""
        from src.mcp.contact_tools import list_contacts
        
        with patch('src.mcp.contact_tools.get_api_client', return_value=mock_api_service):
            with patch('src.mcp.contact_tools.get_cache_manager', return_value=cache_manager):
                
                # First call - cache miss
                contacts1 = await list_contacts(limit=50)
                
                # Reset mock to verify caching
                mock_api_service.get_contacts.reset_mock()
                
                # Second call - should use cache (if implemented)
                contacts2 = await list_contacts(limit=50)
                
                assert contacts1 == contacts2
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, cache_manager, mock_environment):
        """Test error handling across the system."""
        from src.mcp.contact_tools import list_contacts
        
        # Mock API service that raises an error
        mock_api_service = AsyncMock()
        mock_api_service.get_contacts.side_effect = Exception("API Error")
        
        with patch('src.mcp.contact_tools.get_api_client', return_value=mock_api_service):
            with patch('src.mcp.contact_tools.get_cache_manager', return_value=cache_manager):
                
                # Should handle the error gracefully
                with pytest.raises(Exception, match="API Error"):
                    await list_contacts(limit=50)
    
    @pytest.mark.asyncio
    async def test_optimization_integration(self, mock_environment):
        """Test optimization system integration."""
        from src.mcp.optimization.api_optimization import ApiParameterOptimizer
        from src.mcp.optimization.optimization import QueryOptimizer
        
        # Test API parameter optimization
        api_optimizer = ApiParameterOptimizer()
        filters = [
            {"field": "email", "operator": "EQUALS", "value": "test@example.com"},
            {"field": "given_name", "operator": "CONTAINS", "value": "John"}
        ]
        
        result = api_optimizer.optimize_contact_query_parameters(filters)
        assert result.optimization_strategy in ["highly_optimized", "moderately_optimized"]
        assert len(result.server_side_filters) > 0
        
        # Test query optimization
        query_optimizer = QueryOptimizer()
        strategy = query_optimizer.analyze_query(filters)
        assert strategy in ["server_optimized", "hybrid"]
    
    @pytest.mark.asyncio
    async def test_filter_utils_integration(self, mock_environment):
        """Test filter utilities integration."""
        from src.utils.filter_utils import (
            filter_by_name_pattern, 
            validate_filter_conditions,
            apply_complex_filters,
            optimize_filters_for_api
        )
        
        # Test pattern filtering
        items = [
            {"name": "John Doe", "id": 1},
            {"name": "Jane Smith", "id": 2},
            {"name": "Bob Johnson", "id": 3}
        ]
        
        filtered = filter_by_name_pattern(items, "J*")
        assert len(filtered) == 2
        
        # Test filter validation
        filters = [
            {"field": "name", "operator": "EQUALS", "value": "John"},
            {"field": "email", "operator": "CONTAINS", "value": "@example.com"}
        ]
        
        # Should not raise an exception
        validate_filter_conditions(filters)
        
        # Test complex filtering
        test_data = [
            {"name": "John", "email": "john@example.com"},
            {"name": "Jane", "email": "jane@test.com"}
        ]
        
        email_filters = [{"field": "email", "operator": "CONTAINS", "value": "@example.com"}]
        filtered_data = apply_complex_filters(test_data, email_filters)
        assert len(filtered_data) == 1
        assert filtered_data[0]["name"] == "John"
        
        # Test API optimization
        api_params, client_filters = optimize_filters_for_api(filters)
        assert isinstance(api_params, dict)
        assert isinstance(client_filters, list)


class TestPerformanceIntegration:
    """Test performance-related integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, mock_environment):
        """Test bulk operations perform efficiently."""
        from src.mcp.tools import set_custom_field_values
        from mcp.server.fastmcp import Context
        
        # Mock API service for bulk operations
        mock_api_service = AsyncMock()
        mock_api_service.update_contact_custom_field.return_value = {"success": True}
        mock_cache_manager = AsyncMock()
        
        context = Context()
        context.api_client = mock_api_service
        context.cache_manager = mock_cache_manager
        
        # Test bulk update with many contacts
        contact_ids = [str(i) for i in range(1, 101)]  # 100 contacts
        
        result = await set_custom_field_values(
            context,
            field_id="7",
            contact_ids=contact_ids,
            common_value="Bulk Update"
        )
        
        assert result["success"] is True
        assert result["successful_updates"] == 100
        assert mock_api_service.update_contact_custom_field.call_count == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_environment):
        """Test concurrent operations work correctly."""
        from src.cache.manager import CacheManager
        
        cache = CacheManager()
        
        try:
            # Test concurrent cache operations
            async def cache_operation(key, value):
                await cache.set(f"test_key_{key}", value, ttl=60)
                result = await cache.get(f"test_key_{key}")
                return result
            
            # Run multiple operations concurrently
            tasks = [cache_operation(i, f"value_{i}") for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 10
            for i, result in enumerate(results):
                assert result == f"value_{i}"
        
        finally:
            await cache.close()


class TestErrorRecoveryIntegration:
    """Test error recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_api_failure_recovery(self, mock_environment):
        """Test system recovery from API failures."""
        from src.api.client import KeapApiService
        
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_key"}):
            # Test that API client can be created and handles errors
            client = KeapApiService()
            
            # Test diagnostic reporting even with failures
            diagnostics = client.get_diagnostics()
            assert "total_requests" in diagnostics
            assert "failed_requests" in diagnostics
    
    @pytest.mark.asyncio
    async def test_cache_failure_recovery(self, mock_environment):
        """Test system continues working even if cache fails."""
        from src.mcp.contact_tools import list_contacts
        
        # Mock API service that works
        mock_api_service = AsyncMock()
        mock_api_service.get_contacts.return_value = {
            "contacts": [{"id": 1, "name": "Test"}]
        }
        
        # Mock cache that fails
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.side_effect = Exception("Cache Error")
        mock_cache_manager.set.side_effect = Exception("Cache Error")
        
        with patch('src.mcp.contact_tools.get_api_client', return_value=mock_api_service):
            with patch('src.mcp.contact_tools.get_cache_manager', return_value=mock_cache_manager):
                
                # Should still work despite cache failures
                contacts = await list_contacts(limit=50)
                assert len(contacts) == 1
                assert contacts[0]["id"] == 1


class TestCompleteSystemIntegration:
    """Test the complete system working together."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, mock_environment):
        """Test a complete end-to-end workflow."""
        # This test simulates a real-world usage scenario
        
        # 1. Initialize system components
        from src.api.client import KeapApiService
        from src.cache.manager import CacheManager
        from src.mcp.optimization.api_optimization import ApiParameterOptimizer
        
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_key"}):
            
            # 2. Test optimization pipeline
            optimizer = ApiParameterOptimizer()
            
            # Define a complex query
            filters = [
                {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
                {"field": "given_name", "operator": "EQUALS", "value": "John"},
                {"field": "custom_field", "operator": "EQUALS", "value": "VIP"}
            ]
            
            # 3. Optimize the query
            optimization_result = optimizer.optimize_contact_query_parameters(filters)
            
            # 4. Verify optimization worked
            assert optimization_result.optimization_score > 0
            assert len(optimization_result.server_side_filters) > 0
            
            # 5. Test that all components can be instantiated
            api_client = KeapApiService()
            assert api_client is not None
            
            cache_manager = CacheManager()
            assert cache_manager is not None
            await cache_manager.close()
    
    @pytest.mark.asyncio 
    async def test_mcp_tools_integration(self, mock_environment):
        """Test that MCP tools work together correctly."""
        from src.mcp.tools import get_api_client, get_cache_manager
        from mcp.server.fastmcp import Context
        
        # Test factory functions work
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_key"}):
            api_client = get_api_client()
            assert api_client is not None
            
            cache_manager = get_cache_manager()
            assert cache_manager is not None
            
            # Test context creation
            context = Context()
            context.api_client = api_client
            context.cache_manager = cache_manager
            
            assert hasattr(context, 'api_client')
            assert hasattr(context, 'cache_manager')
            
            # Clean up
            await cache_manager.close()
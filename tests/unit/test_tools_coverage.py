"""
Unit tests to improve coverage for tools.py module.

Focuses on covering error paths, edge cases, and less-tested code paths
in the main tools module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.server.fastmcp import Context

from src.mcp.tools import (
    get_api_client,
    get_cache_manager,
    query_contacts_optimized,
    get_available_tools
)


class TestFactoryFunctions:
    """Test factory functions for API client and cache manager."""

    def test_get_api_client_with_no_env_var(self):
        """Test get_api_client when no KEAP_API_KEY is set."""
        with patch.dict('os.environ', {}, clear=True):
            # Should set a default test key
            client = get_api_client()
            assert client is not None
            
    def test_get_api_client_with_env_var(self):
        """Test get_api_client when KEAP_API_KEY is already set."""
        with patch.dict('os.environ', {'KEAP_API_KEY': 'real_api_key'}):
            client = get_api_client()
            assert client is not None

    def test_get_cache_manager(self):
        """Test get_cache_manager factory function."""
        manager = get_cache_manager()
        assert manager is not None
        
        # Test that multiple calls return the same type
        manager2 = get_cache_manager()
        assert type(manager) == type(manager2)


class TestQueryContactsOptimizedEdgeCases:
    """Test edge cases and error paths in query_contacts_optimized."""

    @pytest.mark.asyncio
    async def test_query_contacts_optimized_with_optimization_disabled(self):
        """Test query_contacts_optimized with optimization disabled."""
        context = Context()
        
        # Mock the underlying contact_tools.list_contacts function
        with patch("src.mcp.contact_tools.list_contacts") as mock_list_contacts:
            mock_list_contacts.return_value = [{"id": 1, "name": "Test"}]
            
            result = await query_contacts_optimized(
                context=context,
                filters=[],
                limit=100,
                offset=0,
                enable_optimization=False,  # Disabled
                return_metrics=True
            )
            
            assert "contacts" in result
            assert "count" in result
            assert len(result["contacts"]) == 1
            # When optimization is disabled, metrics are not included
            assert "performance_metrics" not in result

    @pytest.mark.asyncio
    async def test_query_contacts_optimized_error_handling(self):
        """Test query_contacts_optimized error handling paths."""
        context = Context()
        
        # Mock QueryExecutor to raise an exception
        with patch("src.mcp.optimization.optimization.QueryExecutor") as mock_executor_class:
            mock_executor = AsyncMock()
            mock_executor_class.return_value = mock_executor
            mock_executor.execute_optimized_query.side_effect = Exception("Query failed")
            
            with pytest.raises(Exception, match="Query failed"):
                await query_contacts_optimized(
                    context=context,
                    filters=[],
                    limit=100,
                    offset=0
                )

    @pytest.mark.asyncio
    async def test_query_contacts_optimized_with_complex_filters(self):
        """Test query_contacts_optimized with complex nested filters."""
        context = Context()
        
        complex_filters = [
            {
                "operator": "OR",
                "conditions": [
                    {"field": "first_name", "operator": "=", "value": "John"},
                    {
                        "operator": "AND",
                        "conditions": [
                            {"field": "last_name", "operator": "=", "value": "Smith"},
                            {"field": "id", "operator": ">", "value": 100}
                        ]
                    }
                ]
            }
        ]
        
        # Mock QueryExecutor
        with patch("src.mcp.optimization.optimization.QueryExecutor") as mock_executor_class:
            from src.mcp.optimization.optimization import QueryMetrics, QueryStrategy
            
            mock_executor = AsyncMock()
            mock_executor_class.return_value = mock_executor
            
            # Create proper metrics object
            metrics = QueryMetrics(
                total_duration_ms=50.0,
                api_calls=1,
                cache_hit=False,
                strategy_used="HYBRID",
                filters_applied=1,
                results_count=1,
                server_side_filters=0,
                client_side_filters=1,
                optimization_ratio=0.0
            )
            
            mock_executor.execute_optimized_query.return_value = (
                [{"id": 1, "name": "John Smith"}], 
                metrics
            )
            
            result = await query_contacts_optimized(
                context=context,
                filters=complex_filters,
                limit=50,
                offset=10,
                order_by="name",
                order_direction="DESC",
                include=["custom_fields"],
                enable_optimization=True,
                return_metrics=True
            )
            
            assert "contacts" in result
            assert "performance_metrics" in result
            assert result["performance_metrics"]["strategy_used"] == "HYBRID"

    @pytest.mark.asyncio
    async def test_query_contacts_optimized_metrics_disabled(self):
        """Test query_contacts_optimized with metrics disabled."""
        context = Context()
        
        with patch("src.mcp.optimization.optimization.QueryExecutor") as mock_executor_class:
            from src.mcp.optimization.optimization import QueryMetrics
            
            mock_executor = AsyncMock()
            mock_executor_class.return_value = mock_executor
            
            metrics = QueryMetrics(
                total_duration_ms=25.0,
                api_calls=1,
                cache_hit=False,
                strategy_used="BULK_RETRIEVE",
                filters_applied=0,
                results_count=1,
                server_side_filters=0,
                client_side_filters=0,
                optimization_ratio=0.0
            )
            
            mock_executor.execute_optimized_query.return_value = (
                [{"id": 1}], 
                metrics
            )
            
            result = await query_contacts_optimized(
                context=context,
                filters=[],
                limit=100,
                offset=0,
                return_metrics=False  # Disabled
            )
            
            # Should only return contacts, no performance_metrics
            assert "contacts" in result
            assert "count" in result
            assert "performance_metrics" not in result

    @pytest.mark.asyncio 
    async def test_query_contacts_optimized_all_parameters(self):
        """Test query_contacts_optimized with all parameters specified."""
        context = Context()
        
        with patch("src.mcp.optimization.optimization.QueryExecutor") as mock_executor_class:
            from src.mcp.optimization.optimization import QueryMetrics
            
            mock_executor = AsyncMock()
            mock_executor_class.return_value = mock_executor
            
            metrics = QueryMetrics(
                total_duration_ms=75.5,
                api_calls=0,
                cache_hit=True,
                strategy_used="CACHED_RESULT",
                filters_applied=1,
                results_count=1,
                server_side_filters=1,
                client_side_filters=0,
                optimization_ratio=1.0
            )
            
            mock_executor.execute_optimized_query.return_value = (
                [{"id": 1, "name": "Test User"}], 
                metrics
            )
            
            filters = [{"field": "name", "operator": "contains", "value": "Test"}]
            include_fields = ["custom_fields", "tags"]
            
            result = await query_contacts_optimized(
                context=context,
                filters=filters,
                limit=250,
                offset=50,
                order_by="last_name",
                order_direction="ASC",
                include=include_fields,
                enable_optimization=True,
                return_metrics=True
            )
            
            assert "contacts" in result
            assert "performance_metrics" in result
            assert result["contacts"][0]["name"] == "Test User"
            assert result["performance_metrics"]["cache_hit"] is True


class TestGetAvailableTools:
    """Test the get_available_tools function."""

    def test_get_available_tools_returns_list(self):
        """Test that get_available_tools returns a list of tool definitions."""
        tools = get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check that returned items are tool definitions with expected structure
        for tool in tools:
            assert isinstance(tool, dict)
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
        
        # Extract tool names and check that expected tools are in the list
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "list_contacts",
            "search_contacts_by_email", 
            "search_contacts_by_name",
            "get_tags",
            "get_contacts_with_tag",
            "set_custom_field_values"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    def test_get_available_tools_consistency(self):
        """Test that get_available_tools returns consistent results."""
        tools1 = get_available_tools()
        tools2 = get_available_tools()
        
        assert tools1 == tools2
        assert len(tools1) == len(tools2)


class TestToolsModuleFunctions:
    """Test other functions in the tools module for coverage."""

    @pytest.mark.asyncio
    async def test_search_contacts_by_email_error_handling(self):
        """Test search_contacts_by_email error handling."""
        from src.mcp.tools import search_contacts_by_email
        from src.mcp.contact_tools import search_contacts_by_email as _search_by_email
        
        context = Context()
        
        # Mock the underlying contact_tools function to raise an exception
        with patch("src.mcp.contact_tools.search_contacts_by_email") as mock_search:
            mock_search.side_effect = Exception("API error")
            
            with pytest.raises(Exception, match="API error"):
                await search_contacts_by_email(context, "test@example.com")

    @pytest.mark.asyncio
    async def test_search_contacts_by_name_empty_result(self):
        """Test search_contacts_by_name with empty API result."""
        from src.mcp.tools import search_contacts_by_name
        
        context = Context()
        
        # Mock the underlying contact_tools function to return empty result
        with patch("src.mcp.contact_tools.search_contacts_by_name") as mock_search:
            mock_search.return_value = []
            
            result = await search_contacts_by_name(context, "NonexistentName")
            assert result == []

    @pytest.mark.asyncio
    async def test_get_tags_with_category_filter(self):
        """Test get_tags with category filtering."""
        from src.mcp.tools import get_tags
        
        context = Context()
        
        # Mock the underlying tag_tools function
        with patch("src.mcp.tag_tools.get_tags") as mock_get_tags:
            mock_get_tags.return_value = [
                {"id": 1, "name": "VIP", "category_id": 5},
                {"id": 2, "name": "Lead", "category_id": 5}
            ]
            
            result = await get_tags(context, filters=[{"field": "category_id", "operator": "=", "value": 5}], limit=50)
            assert len(result) == 2
            assert all(tag["category_id"] == 5 for tag in result)

    @pytest.mark.asyncio
    async def test_get_contacts_with_tag_pagination(self):
        """Test get_contacts_with_tag with different pagination."""
        from src.mcp.tools import get_contacts_with_tag
        
        context = Context()
        
        # Mock the underlying tag_tools function
        with patch("src.mcp.tag_tools.get_contacts_with_tag") as mock_get_contacts:
            mock_get_contacts.return_value = [
                {"id": 1, "name": "Test", "tags": [{"id": 10}]}
            ]
            
            result = await get_contacts_with_tag(context, tag_id="10", limit=75)
            assert len(result) == 1
            assert result[0]["id"] == 1
            
            # Verify function was called with correct parameters
            mock_get_contacts.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_custom_field_values_success(self):
        """Test set_custom_field_values successful operation."""
        from src.mcp.tools import set_custom_field_values
        
        context = Context()
        
        # Mock the API client to return success
        with patch("src.mcp.tools.get_api_client") as mock_get_api:
            with patch("src.mcp.tools.get_cache_manager") as mock_get_cache:
                mock_api_client = AsyncMock()
                mock_cache_manager = AsyncMock()
                mock_get_api.return_value = mock_api_client
                mock_get_cache.return_value = mock_cache_manager
                
                # Mock the specific method that the function expects
                mock_api_client.update_contact_custom_field.return_value = {"success": True}
                mock_cache_manager.invalidate_pattern = AsyncMock()
                
                # Use the correct parameter signature
                result = await set_custom_field_values(
                    context, 
                    field_id="test_field", 
                    contact_values={"456": "new_value"}
                )
                
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_api_diagnostics_comprehensive(self):
        """Test get_api_diagnostics with full response."""
        from src.mcp.tools import get_api_diagnostics
        
        context = Context()
        
        # Mock get_api_client and get_cache_manager to return mocked objects
        with patch("src.mcp.tools.get_api_client") as mock_get_api:
            with patch("src.mcp.tools.get_cache_manager") as mock_get_cache:
                mock_api_client = MagicMock()
                mock_cache_manager = MagicMock()
                mock_get_api.return_value = mock_api_client
                mock_get_cache.return_value = mock_cache_manager
                
                # Mock API diagnostics (sync method)
                mock_api_client.get_diagnostics.return_value = {
                    "successful_requests": 100,
                    "total_requests": 120,
                    "failed_requests": 20,
                    "average_response_time_ms": 45.2
                }
                
                # Mock cache diagnostics if available
                mock_cache_manager.get_diagnostics.return_value = {
                    "cache_hits": 80,
                    "cache_misses": 20,
                    "total_entries": 150
                }
                
                result = await get_api_diagnostics(context)
                
                assert isinstance(result, dict)
                # Should contain some diagnostic information
                assert len(result) > 0
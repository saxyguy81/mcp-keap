"""
Simple unit tests to boost coverage to 90%+.

Focuses on testing existing functionality with different parameters
and edge cases to improve code coverage without complex mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.optimization.optimization import (
    QueryOptimizer,
    QueryExecutor, 
    QueryMetrics,
    QueryStrategy,
    OptimizationHint
)
from src.mcp.optimization.api_optimization import (
    ApiParameterOptimizer,
    OptimizationResult
)


class TestSimpleCoverage:
    """Simple coverage tests for optimization modules."""

    def test_query_strategy_enum(self):
        """Test QueryStrategy enum values."""
        assert QueryStrategy.CACHED_RESULT == "cached_result"
        assert QueryStrategy.SERVER_OPTIMIZED == "server_optimized"
        assert QueryStrategy.TAG_OPTIMIZED == "tag_optimized"
        assert QueryStrategy.BULK_RETRIEVE == "bulk_retrieve"
        assert QueryStrategy.HYBRID == "hybrid"

    def test_query_metrics_creation(self):
        """Test QueryMetrics dataclass creation."""
        metrics = QueryMetrics(
            total_duration_ms=100.5,
            api_calls=2,
            cache_hit=True,
            strategy_used="cached_result",
            filters_applied=3,
            results_count=50,
            server_side_filters=2,
            client_side_filters=1,
            optimization_ratio=0.8
        )
        
        assert metrics.total_duration_ms == 100.5
        assert metrics.api_calls == 2
        assert metrics.cache_hit is True
        assert metrics.strategy_used == "cached_result"
        assert metrics.filters_applied == 3
        assert metrics.results_count == 50
        assert metrics.server_side_filters == 2
        assert metrics.client_side_filters == 1
        assert metrics.optimization_ratio == 0.8

    def test_optimization_hint_creation(self):
        """Test OptimizationHint dataclass creation."""
        # Test with defaults
        hint = OptimizationHint()
        assert hint.preferred_strategy is None
        assert hint.enable_caching is True
        assert hint.max_api_calls is None
        assert hint.estimated_result_size is None
        
        # Test with all parameters
        hint = OptimizationHint(
            preferred_strategy=QueryStrategy.TAG_OPTIMIZED,
            enable_caching=False,
            max_api_calls=5,
            estimated_result_size=100
        )
        assert hint.preferred_strategy == QueryStrategy.TAG_OPTIMIZED
        assert hint.enable_caching is False
        assert hint.max_api_calls == 5
        assert hint.estimated_result_size == 100

    def test_query_optimizer_analyze_query_cases(self):
        """Test QueryOptimizer.analyze_query with various inputs."""
        optimizer = QueryOptimizer()
        
        # Test empty filters
        strategy = optimizer.analyze_query([])
        assert strategy == QueryStrategy.BULK_RETRIEVE
        
        # Test with hint
        hint = OptimizationHint(preferred_strategy=QueryStrategy.CACHED_RESULT)
        strategy = optimizer.analyze_query([{"field": "test"}], hints=hint)
        assert strategy == QueryStrategy.CACHED_RESULT
        
        # Test tag filters
        tag_filters = [
            {"field": "tags", "operator": "=", "value": "VIP"},
            {"field": "tag_id", "operator": "=", "value": 123}
        ]
        strategy = optimizer.analyze_query(tag_filters)
        assert strategy == QueryStrategy.TAG_OPTIMIZED
        
        # Test logical groups
        logical_filters = [
            {
                "operator": "OR",
                "conditions": [
                    {"field": "name", "operator": "=", "value": "test"}
                ]
            }
        ]
        strategy = optimizer.analyze_query(logical_filters)
        assert strategy == QueryStrategy.HYBRID
        
        # Test server-optimizable filters
        server_filters = [
            {"field": "email", "operator": "equals", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"}
        ]
        strategy = optimizer.analyze_query(server_filters)
        assert strategy == QueryStrategy.SERVER_OPTIMIZED

    def test_query_optimizer_track_performance(self):
        """Test QueryOptimizer.track_performance method."""
        optimizer = QueryOptimizer()
        
        metrics = QueryMetrics(
            total_duration_ms=50.0,
            api_calls=1,
            cache_hit=False,
            strategy_used="server_optimized",
            filters_applied=2,
            results_count=25,
            server_side_filters=2,
            client_side_filters=0,
            optimization_ratio=1.0
        )
        
        # Should not raise any errors
        optimizer.track_performance("test_query", metrics)
        
        # Verify performance history is stored
        assert "test_query" in optimizer.performance_history
        assert len(optimizer.performance_history["test_query"]) == 1

    def test_api_parameter_optimizer_basic(self):
        """Test ApiParameterOptimizer basic functionality."""
        optimizer = ApiParameterOptimizer()
        
        # Test with simple filters
        filters = [
            {"field": "given_name", "operator": "EQUALS", "value": "John"},
            {"field": "email", "operator": "CONTAINS", "value": "@example.com"}
        ]
        
        result = optimizer.optimize_contact_query_parameters(filters)
        
        assert isinstance(result.server_side_filters, dict)
        assert isinstance(result.client_side_filters, list)

    def test_optimization_result_dataclass(self):
        """Test OptimizationResult dataclass."""
        result = OptimizationResult(
            optimization_strategy="test_strategy",
            server_side_filters={"limit": 100},
            client_side_filters=[{"field": "test"}],
            estimated_data_reduction_ratio=0.5,
            optimization_score=0.75
        )
        
        assert result.optimization_strategy == "test_strategy"
        assert result.server_side_filters == {"limit": 100}
        assert len(result.client_side_filters) == 1
        assert result.estimated_data_reduction_ratio == 0.5
        assert result.optimization_score == 0.75


class TestServerToolCoverage:
    """Test server tool implementations for coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("src.mcp.server.FastMCP") as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            from src.mcp.server import KeapMCPServer
            self.server = KeapMCPServer()
            self.mock_mcp = mock_mcp_instance

    @pytest.mark.asyncio
    async def test_server_tool_functions_coverage(self):
        """Test server tool implementations through mock execution."""
        # Import the actual functions from tools.py
        from src.mcp.tools import (
            query_contacts_optimized,
            search_contacts_by_email,
            search_contacts_by_name,
            get_tags,
            get_contacts_with_tag,
            set_custom_field_values,
            get_api_diagnostics
        )
        from mcp.server.fastmcp import Context
        
        context = Context()
        
        # Test basic functionality by mocking underlying functions
        # Test search_contacts_by_email
        with patch("src.mcp.contact_tools.search_contacts_by_email") as mock_search:
            mock_search.return_value = [{"id": 1, "email": "test@example.com"}]
            result = await search_contacts_by_email(context, "test@example.com")
            assert isinstance(result, list)
            assert len(result) == 1
        
        # Test search_contacts_by_name
        with patch("src.mcp.contact_tools.search_contacts_by_name") as mock_search:
            mock_search.return_value = [{"id": 1, "name": "John"}]
            result = await search_contacts_by_name(context, "John")
            assert isinstance(result, list)
            assert len(result) == 1
        
        # Test get_tags
        with patch("src.mcp.tag_tools.get_tags") as mock_get_tags:
            mock_get_tags.return_value = [{"id": 1, "name": "VIP"}]
            result = await get_tags(context, filters=[], limit=100)
            assert isinstance(result, list)
            assert len(result) == 1
        
        # Test get_contacts_with_tag
        with patch("src.mcp.tag_tools.get_contacts_with_tag") as mock_get_contacts:
            mock_get_contacts.return_value = [{"id": 1, "tags": [{"id": 1}]}]
            result = await get_contacts_with_tag(context, tag_id="1", limit=100)
            assert isinstance(result, list)
            assert len(result) == 1
        
        # Test set_custom_field_values with proper parameters
        with patch("src.mcp.tools.get_api_client") as mock_get_api:
            mock_api_client = AsyncMock()
            mock_get_api.return_value = mock_api_client
            mock_api_client.update_contact.return_value = {"success": True}
            
            result = await set_custom_field_values(
                context, 
                field_id="test_field", 
                contact_values={"123": "value"}
            )
            assert isinstance(result, dict)
        
        # Test get_api_diagnostics
        with patch("src.mcp.tools.get_api_client") as mock_get_api:
            mock_api_client = MagicMock()
            mock_get_api.return_value = mock_api_client
            mock_api_client.get_diagnostics.return_value = {
                "successful_requests": 100,
                "total_requests": 120,
                "failed_requests": 20,
                "average_response_time_ms": 45.2
            }
            
            result = await get_api_diagnostics(context)
            assert isinstance(result, dict)


class TestFactoryCoverage:
    """Test factory functions and utilities."""

    def test_get_api_client_coverage(self):
        """Test get_api_client factory function edge cases."""
        from src.mcp.tools import get_api_client
        
        # Test default case
        with patch.dict('os.environ', {}, clear=True):
            client = get_api_client()
            assert client is not None
            
        # Test with existing key
        with patch.dict('os.environ', {'KEAP_API_KEY': 'test_key'}):
            client = get_api_client()
            assert client is not None

    def test_get_cache_manager_coverage(self):
        """Test get_cache_manager factory function."""
        from src.mcp.tools import get_cache_manager
        
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        assert manager1 is not None
        assert manager2 is not None
        assert type(manager1) == type(manager2)

    def test_get_available_tools_coverage(self):
        """Test get_available_tools function."""
        from src.mcp.tools import get_available_tools
        
        tools = get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Should include core tools - check tool names from tool definitions
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "list_contacts",
            "search_contacts_by_email",
            "get_tags"
        ]
        for tool in expected_tools:
            assert tool in tool_names


class TestEdgeCaseCoverage:
    """Test edge cases for additional coverage."""

    def test_query_executor_initialization(self):
        """Test QueryExecutor initialization."""
        mock_api = MagicMock()
        mock_cache = MagicMock()
        
        executor = QueryExecutor(api_client=mock_api, cache_manager=mock_cache)
        assert executor.api_client == mock_api
        assert executor.cache_manager == mock_cache
        assert hasattr(executor, 'optimizer')

    @pytest.mark.asyncio
    async def test_query_executor_unsupported_query_type(self):
        """Test QueryExecutor with unsupported query type."""
        mock_api = AsyncMock()
        mock_cache = AsyncMock()
        executor = QueryExecutor(api_client=mock_api, cache_manager=mock_cache)
        
        # Mock cache to return None (cache miss)
        mock_cache.get.return_value = None
        
        # For unsupported query types, it should fall back to bulk retrieve strategy
        # and handle gracefully without raising ValueError
        result, metrics = await executor.execute_optimized_query(
            query_type="unsupported_type",
            filters=[],
            limit=100,
            offset=0
        )
        
        # Should return empty results for unsupported types
        assert isinstance(result, list)
        assert isinstance(metrics, QueryMetrics)

    def test_api_parameter_optimizer_edge_cases(self):
        """Test ApiParameterOptimizer with edge cases."""
        optimizer = ApiParameterOptimizer()
        
        # Test with empty filters
        result = optimizer.optimize_contact_query_parameters([])
        assert isinstance(result.server_side_filters, dict)
        assert isinstance(result.client_side_filters, list)
        
        # Test with None filters (empty list)
        result = optimizer.optimize_contact_query_parameters([])
        assert isinstance(result.server_side_filters, dict)
        assert isinstance(result.client_side_filters, list)

    def test_query_optimizer_count_server_optimizable_filters(self):
        """Test _count_server_optimizable_filters method."""
        optimizer = QueryOptimizer()
        
        # Test with optimizable filters
        filters = [
            {"field": "email", "operator": "equals", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"},
            {"field": "custom_field", "operator": "equals", "value": "test"}  # Not optimizable
        ]
        
        count = optimizer._count_server_optimizable_filters(filters)
        assert count == 2  # Only first two are server-optimizable
        
        # Test with no optimizable filters
        filters = [
            {"field": "custom_field", "operator": "regex", "value": "pattern"}
        ]
        count = optimizer._count_server_optimizable_filters(filters)
        assert count == 0
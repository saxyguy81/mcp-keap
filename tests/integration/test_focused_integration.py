"""
Focused integration tests that directly exercise the main MCP tools
and achieve meaningful coverage of the integration paths.

These tests focus on the actual tool functions available in src/mcp/tools.py
and their integration with API client, cache, and utility functions.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.tools import (
    list_contacts,
    get_tags,
    search_contacts_by_email,
    get_contact_details,
    apply_tags_to_contacts,
    query_contacts_optimized,
    analyze_query_performance,
    get_api_diagnostics,
    intersect_id_lists,
    query_contacts_by_custom_field,
    set_custom_field_values,
    get_available_tools,
    get_tool_by_name,
)
from src.api.client import KeapApiService


class TestFocusedIntegration:
    """Focused integration tests for main MCP tool functions."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass

    @pytest.fixture
    def mock_context(self):
        """Create mock context for tool execution."""
        context = MagicMock()
        return context

    @pytest.fixture
    def sample_contacts(self):
        """Sample contact data for testing."""
        return [
            {
                "id": 1,
                "given_name": "John",
                "family_name": "Doe",
                "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}],
                "tag_ids": [10, 20, 30],
                "custom_fields": [
                    {"id": 7, "content": "VIP"},
                    {"id": 8, "content": "Premium"},
                ],
                "date_created": "2024-01-15T10:30:00Z",
            },
            {
                "id": 2,
                "given_name": "Jane",
                "family_name": "Smith",
                "email_addresses": [{"email": "jane@company.com", "field": "EMAIL1"}],
                "tag_ids": [10, 40],
                "custom_fields": [{"id": 7, "content": "Regular"}],
                "date_created": "2024-01-16T11:30:00Z",
            },
        ]

    @pytest.fixture
    def sample_tags(self):
        """Sample tag data for testing."""
        return [
            {"id": 10, "name": "Customer", "description": "Customer tag"},
            {"id": 20, "name": "VIP", "description": "VIP customer"},
            {"id": 30, "name": "Newsletter", "description": "Newsletter subscriber"},
        ]





    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts_integration(self, mock_context):
        """Test applying tags to contacts integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.apply_tags_to_contacts.return_value = {"success": True}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.invalidate_contacts = AsyncMock()
        mock_cache_manager.invalidate_tags = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):
            # Apply tags
            result = await apply_tags_to_contacts(
                mock_context, ["10", "20"], ["1", "2"]
            )

            # Verify result
            assert result["success"] is True
            assert "operations_completed" in result

            # Verify API calls
            assert mock_api_client.apply_tags_to_contacts.call_count >= 1

            # Verify cache invalidation
            mock_cache_manager.invalidate_contacts.assert_called()
            mock_cache_manager.invalidate_tags.assert_called()

    @pytest.mark.asyncio
    async def test_intersect_id_lists_integration(self, mock_context):
        """Test ID list intersection utility."""
        lists = [
            {"item_ids": [1, 2, 3, 4]},
            {"item_ids": [2, 3, 4, 5]},
            {"item_ids": [3, 4, 5, 6]},
        ]

        # Test intersection
        result = await intersect_id_lists(mock_context, lists)

        # Verify intersection
        assert result["success"] is True
        assert set(result["intersection"]) == {3, 4}
        assert result["count"] == 2
        assert result["lists_processed"] == 3



    @pytest.mark.asyncio
    async def test_get_api_diagnostics_integration(self, mock_context):
        """Test API diagnostics integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_diagnostics.return_value = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "retried_requests": 10,
            "rate_limited_requests": 2,
            "average_response_time": 1.2,
            "cache_hits": 50,
            "cache_misses": 50,
            "endpoints_called": {"/contacts": 80, "/tags": 20},
            "error_counts": {"HTTP_500": 3, "HTTP_429": 2},
            "requests_per_hour": 100,
        }

        with patch("src.mcp.tools.get_api_client", return_value=mock_api_client):
            # Get diagnostics
            result = await get_api_diagnostics(mock_context)

            # Verify structure
            assert "api_diagnostics" in result
            assert "performance_metrics" in result
            assert "recommendations" in result

            # Verify data
            api_diag = result["api_diagnostics"]
            assert api_diag["total_requests"] == 100
            assert api_diag["successful_requests"] == 95

            # Verify performance metrics
            perf_metrics = result["performance_metrics"]
            assert "success_rate" in perf_metrics
            assert "cache_hit_rate" in perf_metrics


    @pytest.mark.asyncio
    async def test_analyze_query_performance_integration(self, mock_context):
        """Test query performance analysis integration."""
        filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "Test"},
        ]

        with (
            patch(
                "src.mcp.optimization.api_optimization.ApiParameterOptimizer"
            ) as mock_api_opt,
            patch("src.mcp.optimization.optimization.QueryOptimizer") as mock_query_opt,
        ):
            # Configure optimization mocks
            mock_optimization_result = MagicMock()
            mock_optimization_result.optimization_strategy = "highly_optimized"
            mock_optimization_result.optimization_score = 0.9
            mock_optimization_result.estimated_data_reduction_ratio = 0.8
            mock_optimization_result.server_side_filters = [filters[0]]
            mock_optimization_result.client_side_filters = [filters[1]]

            mock_api_optimizer = mock_api_opt.return_value
            mock_api_optimizer.optimize_contact_query_parameters.return_value = (
                mock_optimization_result
            )
            mock_api_optimizer.analyze_filter_performance.return_value = {
                "performance_rating": "excellent"
            }
            mock_api_optimizer.get_field_optimization_info.return_value = {
                "email": "high_performance"
            }

            mock_query_optimizer = mock_query_opt.return_value
            mock_query_optimizer.analyze_query.return_value = "server_optimized"

            # Analyze query performance
            result = await analyze_query_performance(
                mock_context, filters, query_type="contact"
            )

            # Verify analysis structure
            assert "query_analysis" in result
            assert "filter_breakdown" in result
            assert "optimization_suggestions" in result

            # Verify analysis data
            query_analysis = result["query_analysis"]
            assert query_analysis["optimization_score"] == 0.9
            assert query_analysis["optimization_strategy"] == "highly_optimized"

    @pytest.mark.asyncio
    async def test_tool_registry_integration(self):
        """Test tool registry and discovery integration."""
        # Get all available tools
        available_tools = get_available_tools()

        # Verify tools are registered
        assert isinstance(available_tools, list)
        assert len(available_tools) > 0

        # Verify tool structure
        for tool in available_tools:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert "parameters" in tool

        # Test tool discovery
        list_contacts_tool = get_tool_by_name("list_contacts")
        assert list_contacts_tool is not None
        assert list_contacts_tool["name"] == "list_contacts"

        # Test non-existent tool
        invalid_tool = get_tool_by_name("non_existent_tool")
        assert invalid_tool is None



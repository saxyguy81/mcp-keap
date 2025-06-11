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
    async def test_list_contacts_integration(self, mock_context, sample_contacts):
        """Test list_contacts integration with API and cache."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": sample_contacts}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None  # Cache miss
        mock_cache_manager.set = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):
            # Call the actual function
            result = await list_contacts(mock_context, limit=10)

            # Verify results
            assert len(result) == 2
            assert result[0]["given_name"] == "John"
            assert result[1]["given_name"] == "Jane"

            # Verify API was called
            mock_api_client.get_contacts.assert_called_once()

            # Verify cache was attempted
            mock_cache_manager.get.assert_called()
            mock_cache_manager.set.assert_called()

    @pytest.mark.asyncio
    async def test_get_tags_integration(self, mock_context, sample_tags):
        """Test get_tags integration with API and cache."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_tags.return_value = {"tags": sample_tags}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None  # Cache miss
        mock_cache_manager.set = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):
            # Call the actual function
            result = await get_tags(mock_context, include_categories=True)

            # Verify results
            assert len(result) == 3
            assert result[0]["name"] == "Customer"
            assert result[1]["name"] == "VIP"

            # Verify API was called
            mock_api_client.get_tags.assert_called_once()

            # Verify cache was attempted
            mock_cache_manager.get.assert_called()
            mock_cache_manager.set.assert_called()

    @pytest.mark.asyncio
    async def test_search_contacts_by_email_integration(
        self, mock_context, sample_contacts
    ):
        """Test email search integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": sample_contacts}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):
            # Search for John's email
            result = await search_contacts_by_email(mock_context, "john@example.com")

            # Should find John's contact
            assert len(result) == 1
            assert result[0]["given_name"] == "John"
            assert "john@example.com" in [
                addr["email"] for addr in result[0]["email_addresses"]
            ]

    @pytest.mark.asyncio
    async def test_get_contact_details_integration(self, mock_context, sample_contacts):
        """Test get contact details integration."""
        john_contact = sample_contacts[0]

        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contact.return_value = john_contact

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):
            # Get contact details
            result = await get_contact_details(mock_context, "1")

            # Verify details
            assert result["id"] == 1
            assert result["given_name"] == "John"
            assert len(result["custom_fields"]) == 2

            # Verify API was called
            mock_api_client.get_contact.assert_called_once_with("1")

    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts_integration(self, mock_context):
        """Test applying tags to contacts integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.apply_tag_to_contacts.return_value = {"success": True}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.invalidate_pattern = AsyncMock()

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
            assert "applied_count" in result

            # Verify API calls
            assert mock_api_client.apply_tag_to_contacts.call_count >= 1

            # Verify cache invalidation
            mock_cache_manager.invalidate_pattern.assert_called()

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
    async def test_query_contacts_by_custom_field_integration(
        self, mock_context, sample_contacts
    ):
        """Test custom field query integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": sample_contacts}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
            patch("src.utils.contact_utils.get_custom_field_value") as mock_get_field,
            patch("src.utils.contact_utils.format_contact_data") as mock_format,
        ):
            # Mock utility functions
            def mock_get_custom_field(contact, field_id):
                if field_id == "7":
                    return "VIP" if contact["id"] == 1 else "Regular"
                return None

            mock_get_field.side_effect = mock_get_custom_field
            mock_format.side_effect = lambda x: x

            # Query contacts by custom field
            result = await query_contacts_by_custom_field(
                mock_context, field_id="7", field_value="VIP", operator="equals"
            )

            # Should find John (VIP)
            assert len(result) == 1
            assert result[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_set_custom_field_values_integration(self, mock_context):
        """Test setting custom field values integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.update_contact_custom_field.return_value = {"success": True}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.invalidate_contacts = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):
            # Set custom field values
            result = await set_custom_field_values(
                mock_context,
                contact_ids=["1", "2"],
                field_id="7",
                field_value="Premium",
            )

            # Verify result
            assert result["success"] is True
            assert "updated_count" in result

            # Verify API calls
            assert mock_api_client.update_contact_custom_field.call_count >= 1

            # Verify cache invalidation
            mock_cache_manager.invalidate_contacts.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_api_diagnostics_integration(self, mock_context):
        """Test API diagnostics integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_diagnostics.return_value = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "average_response_time": 1.2,
            "cache_hits": 50,
            "cache_misses": 50,
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
    async def test_query_contacts_optimized_integration(
        self, mock_context, sample_contacts
    ):
        """Test optimized query integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": sample_contacts}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
            patch("src.mcp.contact_tools.list_contacts", return_value=sample_contacts),
        ):
            filters = [
                {"field": "email", "operator": "=", "value": "john@example.com"},
                {"field": "given_name", "operator": "contains", "value": "John"},
            ]

            # Execute optimized query
            result = await query_contacts_optimized(
                mock_context,
                filters=filters,
                enable_optimization=False,  # Use basic path
                return_metrics=True,
            )

            # Verify result structure
            assert "contacts" in result
            assert "count" in result
            assert "metrics" in result

            # Verify data
            assert result["count"] >= 0
            assert isinstance(result["contacts"], list)

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
            assert query_analysis["strategy"] == "highly_optimized"

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

    @pytest.mark.asyncio
    async def test_concurrent_tool_operations(
        self, mock_context, sample_contacts, sample_tags
    ):
        """Test concurrent operations across different tools."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": sample_contacts}
        mock_api_client.get_tags.return_value = {"tags": sample_tags}
        mock_api_client.apply_tag_to_contacts.return_value = {"success": True}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()
        mock_cache_manager.invalidate_pattern = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):

            async def contact_operations():
                contacts = await list_contacts(mock_context, limit=10)
                return len(contacts)

            async def tag_operations():
                tags = await get_tags(mock_context)
                return len(tags)

            async def apply_operations():
                result = await apply_tags_to_contacts(mock_context, ["10"], ["1"])
                return result["success"]

            # Execute operations concurrently
            results = await asyncio.gather(
                contact_operations(),
                tag_operations(),
                apply_operations(),
                return_exceptions=True,
            )

            # Verify all operations completed successfully
            assert len(results) == 3
            assert all(not isinstance(result, Exception) for result in results)

            # Verify results
            contact_count, tag_count, apply_success = results
            assert contact_count == 2
            assert tag_count == 3
            assert apply_success is True

    @pytest.mark.asyncio
    async def test_cache_integration_patterns(self, mock_context, sample_contacts):
        """Test cache integration patterns across different tools."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": sample_contacts}

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None  # First call misses
        mock_cache_manager.set = AsyncMock()

        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch("src.mcp.tools.get_cache_manager", return_value=mock_cache_manager),
        ):
            # First call should hit API
            contacts1 = await list_contacts(mock_context, limit=10)

            # Configure cache hit for second call
            mock_cache_manager.get.return_value = sample_contacts

            # Second call should hit cache
            contacts2 = await list_contacts(mock_context, limit=10)

            # Verify results are consistent
            assert len(contacts1) == len(contacts2)

            # Verify cache operations were called
            assert mock_cache_manager.get.call_count >= 2
            mock_cache_manager.set.assert_called()

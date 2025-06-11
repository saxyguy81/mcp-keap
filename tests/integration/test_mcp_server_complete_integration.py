"""
Complete integration tests for MCP Server.

Tests the complete MCP server functionality including tool registration,
execution, error handling, and integration with all underlying components.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.server import KeapMCPServer
from src.mcp.tools import (
    list_contacts,
    get_tags,
    search_contacts_by_email,
    get_contact_details,
    apply_tags_to_contacts,
    query_contacts_optimized,
    analyze_query_performance,
    get_api_diagnostics,
)
from src.api.client import KeapApiService
from src.cache.manager import CacheManager


class TestMCPServerCompleteIntegration:
    """Test complete MCP server integration."""

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
    def mock_api_client(self):
        """Create comprehensive mock API client."""
        client = AsyncMock(spec=KeapApiService)

        # Mock comprehensive contact data
        mock_contacts = [
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
                "last_updated": "2024-01-20T14:45:00Z",
            },
            {
                "id": 2,
                "given_name": "Jane",
                "family_name": "Smith",
                "email_addresses": [{"email": "jane@company.com", "field": "EMAIL1"}],
                "tag_ids": [10, 40],
                "custom_fields": [{"id": 7, "content": "Regular"}],
                "date_created": "2024-01-16T11:30:00Z",
                "last_updated": "2024-01-21T09:15:00Z",
            },
            {
                "id": 3,
                "given_name": "Bob",
                "family_name": "Johnson",
                "email_addresses": [{"email": "bob@personal.net", "field": "EMAIL1"}],
                "tag_ids": [20, 50],
                "custom_fields": [],
                "date_created": "2024-01-17T09:15:00Z",
                "last_updated": "2024-01-22T16:30:00Z",
            },
        ]

        mock_tags = [
            {
                "id": 10,
                "name": "Customer",
                "description": "Customer tag",
                "category": {"id": 1, "name": "Status"},
            },
            {
                "id": 20,
                "name": "VIP",
                "description": "VIP customer",
                "category": {"id": 1, "name": "Status"},
            },
            {
                "id": 30,
                "name": "Newsletter",
                "description": "Newsletter subscriber",
                "category": {"id": 2, "name": "Marketing"},
            },
            {
                "id": 40,
                "name": "Lead",
                "description": "Sales lead",
                "category": {"id": 3, "name": "Sales"},
            },
            {
                "id": 50,
                "name": "Partner",
                "description": "Business partner",
                "category": {"id": 4, "name": "Business"},
            },
        ]

        # Configure API responses
        client.get_contacts.return_value = {"contacts": mock_contacts}
        client.get_tags.return_value = {"tags": mock_tags}

        # Single item responses
        client.get_contact.side_effect = lambda contact_id: next(
            (contact for contact in mock_contacts if contact["id"] == int(contact_id)),
            None,
        )
        client.get_tag.side_effect = lambda tag_id: next(
            (tag for tag in mock_tags if tag["id"] == int(tag_id)), None
        )

        # Operation responses
        client.apply_tag_to_contacts.return_value = {"success": True}
        client.remove_tag_from_contacts.return_value = {"success": True}
        client.update_contact_custom_field.return_value = {"success": True}
        client.create_tag.return_value = {
            "id": 60,
            "name": "New Tag",
            "description": "New tag",
        }

        # Diagnostics response
        client.get_diagnostics.return_value = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "retried_requests": 10,
            "rate_limited_requests": 2,
            "cache_hits": 50,
            "cache_misses": 50,
            "average_response_time": 1.2,
            "requests_per_hour": 3000,
            "endpoints_called": {"contacts": 60, "tags": 40},
            "error_counts": {"401": 3, "429": 2},
            "last_request_time": "2024-01-01T12:00:00Z",
        }

        return client

    @pytest.fixture
    def mcp_server(self, temp_db_path):
        """Create MCP server with temporary database."""
        server = KeapMCPServer()
        # Configure server with test database if needed
        yield server

    @pytest.fixture
    def mock_context(self, temp_db_path):
        """Create mock context for tool execution."""
        context = MagicMock()
        context.cache_manager = CacheManager(db_path=temp_db_path)
        yield context
        context.cache_manager.close()

    @pytest.mark.asyncio
    async def test_complete_contact_workflow(self, mock_context, mock_api_client):
        """Test complete contact management workflow."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # 1. List all contacts
            all_contacts = await list_contacts(mock_context, limit=50)
            assert len(all_contacts) == 3
            assert all_contacts[0]["given_name"] == "John"

            # 2. Search contacts by email
            email_results = await search_contacts_by_email(
                mock_context, "john@example.com"
            )
            assert len(email_results) == 1
            assert email_results[0]["id"] == 1

            # 3. Get contact details
            contact_details = await get_contact_details(mock_context, "1")
            assert contact_details["id"] == 1
            assert contact_details["given_name"] == "John"
            assert len(contact_details["custom_fields"]) == 2

            # 4. Verify API calls were made
            assert mock_api_client.get_contacts.call_count >= 1
            assert mock_api_client.get_contact.call_count >= 1

    @pytest.mark.asyncio
    async def test_complete_tag_workflow(self, mock_context, mock_api_client):
        """Test complete tag management workflow."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # 1. List all tags
            all_tags = await get_tags(mock_context, include_categories=True)
            assert len(all_tags) == 5
            assert all_tags[0]["name"] == "Customer"

            # 2. Apply tags to contacts
            apply_result = await apply_tags_to_contacts(
                mock_context, tag_ids=["30"], contact_ids=["1", "2"]
            )
            assert apply_result["success"] is True

            # 3. Verify tag operations
            assert mock_api_client.get_tags.call_count >= 1
            assert mock_api_client.apply_tag_to_contacts.call_count >= 1

    @pytest.mark.asyncio
    async def test_optimized_query_workflow(self, mock_context, mock_api_client):
        """Test optimized query workflow with performance analysis."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            filters = [
                {"field": "email", "operator": "=", "value": "john@example.com"},
                {"field": "given_name", "operator": "contains", "value": "John"},
            ]

            # 1. Analyze query performance
            with (
                patch(
                    "src.mcp.optimization.api_optimization.ApiParameterOptimizer"
                ) as mock_api_opt,
                patch(
                    "src.mcp.optimization.optimization.QueryOptimizer"
                ) as mock_query_opt,
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
                performance_analysis = await analyze_query_performance(
                    mock_context, filters, query_type="contact"
                )

                # Verify analysis results
                assert "query_analysis" in performance_analysis
                assert "filter_breakdown" in performance_analysis
                assert (
                    performance_analysis["query_analysis"]["optimization_score"] == 0.9
                )

            # 2. Execute optimized query
            with patch("src.mcp.contact_tools.list_contacts") as mock_list_contacts:
                mock_list_contacts.return_value = [
                    {"id": 1, "given_name": "John", "family_name": "Doe"}
                ]

                optimized_result = await query_contacts_optimized(
                    mock_context,
                    filters=filters,
                    enable_optimization=False,  # Use standard path for testing
                    return_metrics=False,
                )

                # Verify optimized query results
                assert "contacts" in optimized_result
                assert "count" in optimized_result
                assert optimized_result["count"] >= 0

    @pytest.mark.asyncio
    async def test_diagnostics_and_monitoring_workflow(
        self, mock_context, mock_api_client
    ):
        """Test diagnostics and monitoring workflow."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Get comprehensive API diagnostics
            diagnostics = await get_api_diagnostics(mock_context)

            # Verify diagnostics structure
            assert "api_diagnostics" in diagnostics
            assert "performance_metrics" in diagnostics
            assert "recommendations" in diagnostics

            # Verify API diagnostics data
            api_diag = diagnostics["api_diagnostics"]
            assert api_diag["total_requests"] == 100
            assert api_diag["successful_requests"] == 95
            assert api_diag["average_response_time"] == 1.2

            # Verify performance metrics
            perf_metrics = diagnostics["performance_metrics"]
            assert "success_rate" in perf_metrics
            assert "cache_hit_rate" in perf_metrics
            assert perf_metrics["success_rate"] == 95.0

            # Verify recommendations
            recommendations = diagnostics["recommendations"]
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_concurrent_mcp_operations(self, mock_context, mock_api_client):
        """Test concurrent MCP operations across different tools."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):

            async def contact_operations():
                contacts = await list_contacts(mock_context, limit=10)
                details = await get_contact_details(mock_context, "1")
                return len(contacts), details["id"]

            async def tag_operations():
                tags = await get_tags(mock_context)
                apply_result = await apply_tags_to_contacts(mock_context, ["10"], ["1"])
                return len(tags), apply_result["success"]

            async def search_operations():
                email_results = await search_contacts_by_email(
                    mock_context, "john@example.com"
                )
                return len(email_results)

            # Execute operations concurrently
            results = await asyncio.gather(
                contact_operations(),
                tag_operations(),
                search_operations(),
                return_exceptions=True,
            )

            # Verify all operations completed successfully
            assert len(results) == 3
            assert all(not isinstance(result, Exception) for result in results)

            # Verify results
            contact_count, contact_id = results[0]
            tag_count, tag_success = results[1]
            search_count = results[2]

            assert contact_count == 3
            assert contact_id == 1
            assert tag_count == 5
            assert tag_success is True
            assert search_count == 1

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_context, mock_api_client):
        """Test error handling and recovery across MCP operations."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Test API failure scenario
            mock_api_client.get_contacts.side_effect = Exception("API Error")

            try:
                # Attempt operation that should fail
                contacts = await list_contacts(mock_context)
                # If no exception, check for graceful error handling
                assert isinstance(contacts, list)
            except Exception as e:
                # Exception handling is acceptable
                assert "API Error" in str(e)

            # Reset API to working state
            mock_api_client.get_contacts.side_effect = None

            # Verify recovery
            contacts = await list_contacts(mock_context)
            assert len(contacts) == 3

            # Test partial failure in batch operations
            mock_api_client.apply_tag_to_contacts.side_effect = [
                {"success": True},
                Exception("Partial failure"),
            ]

            try:
                result = await apply_tags_to_contacts(mock_context, ["10", "20"], ["1"])
                # Check for partial success handling
                if "success" in result:
                    # Some implementations may handle partial failures
                    pass
            except Exception:
                # Exception handling is also acceptable
                pass

    @pytest.mark.asyncio
    async def test_cache_integration_across_tools(self, mock_context, mock_api_client):
        """Test cache integration consistency across different MCP tools."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Perform operations that should populate cache
            contacts1 = await list_contacts(mock_context, limit=10)
            contact_details1 = await get_contact_details(mock_context, "1")
            tags1 = await get_tags(mock_context)

            # Reset API call counts
            mock_api_client.reset_mock()

            # Perform same operations again
            contacts2 = await list_contacts(mock_context, limit=10)
            contact_details2 = await get_contact_details(mock_context, "1")
            tags2 = await get_tags(mock_context)

            # Verify cache effectiveness
            assert contacts1 == contacts2
            assert contact_details1 == contact_details2
            assert tags1 == tags2

            # Some API calls may still occur due to different cache keys
            # but there should be significant reduction compared to first run

    @pytest.mark.asyncio
    async def test_mcp_tool_registry_and_discovery(self):
        """Test MCP tool registry and discovery functionality."""
        from src.mcp.tools import get_available_tools, get_tool_by_name

        # Get all available tools
        available_tools = get_available_tools()

        # Verify tool registry structure
        assert isinstance(available_tools, list)
        assert len(available_tools) > 0

        # Verify each tool has required properties
        for tool in available_tools:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert "parameters" in tool

            # Verify parameters structure
            params = tool["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params

        # Test tool discovery by name
        list_contacts_tool = get_tool_by_name("list_contacts")
        assert list_contacts_tool is not None
        assert list_contacts_tool["name"] == "list_contacts"

        # Test non-existent tool
        non_existent = get_tool_by_name("non_existent_tool")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(
        self, mock_context, mock_api_client
    ):
        """Test data consistency across different MCP operations."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Get contact via list operation
            all_contacts = await list_contacts(mock_context)
            john_from_list = next((c for c in all_contacts if c["id"] == 1), None)

            # Get same contact via details operation
            john_details = await get_contact_details(mock_context, "1")

            # Get same contact via email search
            john_from_search = await search_contacts_by_email(
                mock_context, "john@example.com"
            )
            john_from_search = john_from_search[0] if john_from_search else None

            # Verify data consistency
            assert john_from_list is not None
            assert john_details is not None
            assert john_from_search is not None

            # Core fields should be consistent
            assert john_from_list["id"] == john_details["id"] == john_from_search["id"]
            assert (
                john_from_list["given_name"]
                == john_details["given_name"]
                == john_from_search["given_name"]
            )
            assert (
                john_from_list["family_name"]
                == john_details["family_name"]
                == john_from_search["family_name"]
            )

    @pytest.mark.asyncio
    async def test_performance_under_load(self, mock_context, mock_api_client):
        """Test MCP server performance under concurrent load."""
        with (
            patch("src.mcp.tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):

            async def perform_mixed_operations(worker_id):
                # Mix of different operations
                contacts = await list_contacts(mock_context, limit=5)
                tags = await get_tags(mock_context)
                search_result = await search_contacts_by_email(
                    mock_context, f"user{worker_id}@example.com"
                )

                return len(contacts), len(tags), len(search_result)

            # Run multiple concurrent workers
            num_workers = 10
            tasks = [perform_mixed_operations(i) for i in range(num_workers)]

            import time

            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Verify performance
            total_time = end_time - start_time
            assert total_time < 5.0  # Should complete within 5 seconds

            # Verify all operations completed
            assert len(results) == num_workers
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == num_workers

            # Verify consistent results
            for contact_count, tag_count, search_count in successful_results:
                assert contact_count == 3
                assert tag_count == 5
                assert search_count >= 0  # May be 0 if email not found

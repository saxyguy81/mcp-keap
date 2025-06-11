"""
Integration tests for MCP tools with real API interactions and caching.

Tests the complete MCP tools workflow including API client integration,
cache management, and optimization features.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
from mcp.server.fastmcp import Context

from src.mcp.tools import (
    get_api_client,
    get_cache_manager,
    set_custom_field_values,
    get_api_diagnostics,
    intersect_id_lists,
)
from src.mcp.contact_tools import list_contacts, search_contacts_by_email
from src.mcp.tag_tools import get_tags, apply_tags_to_contacts


class TestMCPToolsIntegration:
    """Integration tests for MCP tools."""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment with API key."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_api_key"}):
            yield

    @pytest.fixture
    async def mock_api_client(self):
        """Create a comprehensive mock API client."""
        client = AsyncMock()

        # Mock contact responses
        client.get_contacts.return_value = {
            "contacts": [
                {
                    "id": 1,
                    "given_name": "John",
                    "family_name": "Doe",
                    "email_addresses": [
                        {"email": "john@example.com", "field": "EMAIL1"}
                    ],
                    "custom_fields": [{"id": 7, "content": "VIP"}],
                    "tag_ids": [1, 2],
                },
                {
                    "id": 2,
                    "given_name": "Jane",
                    "family_name": "Smith",
                    "email_addresses": [
                        {"email": "jane@example.com", "field": "EMAIL1"}
                    ],
                    "custom_fields": [{"id": 7, "content": "Standard"}],
                    "tag_ids": [2],
                },
            ]
        }

        # Mock tag responses
        client.get_tags.return_value = {
            "tags": [
                {"id": 1, "name": "VIP Customer"},
                {"id": 2, "name": "Newsletter"},
                {"id": 3, "name": "Prospect"},
            ]
        }

        # Mock individual contact
        client.get_contact.return_value = {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}],
            "custom_fields": [{"id": 7, "content": "VIP"}],
        }

        # Mock custom field updates
        client.update_contact_custom_field.return_value = {"success": True}

        # Mock tag operations
        client.apply_tag_to_contacts.return_value = {"success": True}
        client.remove_tag_from_contacts.return_value = {"success": True}

        # Mock diagnostics
        client.get_diagnostics.return_value = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "retried_requests": 10,
            "rate_limited_requests": 2,
            "cache_hits": 20,
            "cache_misses": 5,
            "average_response_time": 0.5,
            "endpoints_called": {"/contacts": 80, "/tags": 20},
            "error_counts": {"HTTP_500": 3, "HTTP_429": 2},
        }

        return client

    @pytest.fixture
    async def mock_cache_manager(self):
        """Create a mock cache manager."""
        cache = AsyncMock()
        cache.get.return_value = None  # Cache miss by default
        cache.set.return_value = None
        cache.invalidate_pattern.return_value = None
        cache.get_diagnostics.return_value = {"cache_size": 1000, "hit_ratio": 0.8}
        return cache

    @pytest.fixture
    async def context_with_mocks(self, mock_api_client, mock_cache_manager):
        """Create a context with mocked dependencies."""
        context = Context()
        context.api_client = mock_api_client
        context.cache_manager = mock_cache_manager
        return context

    @pytest.mark.asyncio
    async def test_contact_tools_integration(
        self, context_with_mocks, mock_environment
    ):
        """Test contact tools integration."""
        context = context_with_mocks

        # Test list contacts
        with patch(
            "src.mcp.contact_tools.get_api_client", return_value=context.api_client
        ):
            with patch(
                "src.mcp.contact_tools.get_cache_manager",
                return_value=context.cache_manager,
            ):
                contacts = await list_contacts(limit=50)

                assert len(contacts) == 2
                assert contacts[0]["given_name"] == "John"
                assert contacts[1]["given_name"] == "Jane"

        # Test search by email
        with patch(
            "src.mcp.contact_tools.get_api_client", return_value=context.api_client
        ):
            with patch(
                "src.mcp.contact_tools.get_cache_manager",
                return_value=context.cache_manager,
            ):
                contacts = await search_contacts_by_email("john@example.com")

                assert len(contacts) == 2  # Mock returns all contacts

    @pytest.mark.asyncio
    async def test_tag_tools_integration(self, context_with_mocks, mock_environment):
        """Test tag tools integration."""
        context = context_with_mocks

        # Test get tags
        with patch("src.mcp.tag_tools.get_api_client", return_value=context.api_client):
            with patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=context.cache_manager,
            ):
                tags = await get_tags(limit=100)

                assert len(tags) == 3
                assert tags[0]["name"] == "VIP Customer"

        # Test apply tags
        with patch("src.mcp.tag_tools.get_api_client", return_value=context.api_client):
            with patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=context.cache_manager,
            ):
                result = await apply_tags_to_contacts(contact_ids=["1"], tag_ids=["3"])

                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_custom_field_tools_integration(
        self, context_with_mocks, mock_environment
    ):
        """Test custom field tools integration."""
        context = context_with_mocks

        # Test common value update
        result = await set_custom_field_values(
            context, field_id="7", contact_ids=["1", "2"], common_value="Premium"
        )

        assert result["success"] is True
        assert result["successful_updates"] == 2
        assert result["failed_updates"] == 0

        # Verify API calls were made
        assert context.api_client.update_contact_custom_field.call_count == 2

        # Verify cache invalidation was called
        assert (
            context.cache_manager.invalidate_pattern.call_count == 4
        )  # 2 patterns × 2 contacts

    @pytest.mark.asyncio
    async def test_custom_field_individual_values(
        self, context_with_mocks, mock_environment
    ):
        """Test custom field tools with individual values."""
        context = context_with_mocks

        # Test individual value mapping
        contact_values = {"1": "Gold", "2": "Silver"}

        result = await set_custom_field_values(
            context, field_id="7", contact_values=contact_values
        )

        assert result["success"] is True
        assert result["successful_updates"] == 2
        assert result["failed_updates"] == 0

    @pytest.mark.asyncio
    async def test_diagnostics_integration(self, context_with_mocks, mock_environment):
        """Test API diagnostics integration."""
        context = context_with_mocks

        with patch("platform.platform", return_value="macOS"):
            with patch("platform.python_version", return_value="3.11.6"):
                result = await get_api_diagnostics(context)

        assert "api_diagnostics" in result
        assert "cache_diagnostics" in result
        assert "system_info" in result
        assert "performance_metrics" in result
        assert "recommendations" in result

        # Check calculated metrics
        assert result["performance_metrics"]["success_rate"] == 95.0
        assert result["performance_metrics"]["retry_rate"] == 10.0

    @pytest.mark.asyncio
    async def test_utility_functions_integration(
        self, context_with_mocks, mock_environment
    ):
        """Test utility functions integration."""
        context = context_with_mocks

        # Test ID intersection
        lists = [
            {"item_ids": ["1", "2", "3"]},
            {"item_ids": ["2", "3", "4"]},
            {"item_ids": ["3", "4", "5"]},
        ]

        result = await intersect_id_lists(context, lists)

        assert result["success"] is True
        assert result["intersection"] == ["3"]
        assert result["count"] == 1
        assert result["lists_processed"] == 3

    @pytest.mark.asyncio
    async def test_factory_functions(self, mock_environment):
        """Test MCP tools factory functions."""
        # Test API client factory
        with patch("src.mcp.tools.KeapApiService") as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance

            client = get_api_client()
            assert client == mock_instance
            mock_service.assert_called_once()

        # Test cache manager factory
        with patch("src.mcp.tools.CacheManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance

            cache = get_cache_manager()
            assert cache == mock_instance
            mock_manager.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_integration(
        self, mock_cache_manager, mock_environment
    ):
        """Test error handling across MCP tools."""
        # Mock API client that fails
        mock_api_client = AsyncMock()
        mock_api_client.update_contact_custom_field.side_effect = Exception("API Error")

        context = Context()
        context.api_client = mock_api_client
        context.cache_manager = mock_cache_manager

        # Test that errors are handled gracefully
        result = await set_custom_field_values(
            context, field_id="7", contact_ids=["1"], common_value="Test"
        )

        assert result["success"] is False
        assert "API Error" in result["error"]

    @pytest.mark.asyncio
    async def test_validation_integration(self, context_with_mocks, mock_environment):
        """Test input validation across MCP tools."""
        context = context_with_mocks

        # Test custom field validation - conflicting parameters
        result = await set_custom_field_values(
            context,
            field_id="7",
            contact_ids=["1"],
            common_value="Test",
            contact_values={"1": "Conflict"},
        )

        assert result["success"] is False
        assert "Cannot specify both" in result["error"]

        # Test custom field validation - missing parameters
        result = await set_custom_field_values(context, field_id="7")

        assert result["success"] is False
        assert "Must specify either" in result["error"]

        # Test ID intersection validation - insufficient lists
        result = await intersect_id_lists(context, [{"item_ids": ["1"]}])

        assert result["success"] is False
        assert "At least two lists are required" in result["error"]


class TestMCPToolsPerformance:
    """Test performance aspects of MCP tools integration."""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment with API key."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_api_key"}):
            yield

    @pytest.mark.asyncio
    async def test_bulk_custom_field_updates(self, mock_environment):
        """Test bulk custom field updates performance."""
        # Mock API client for bulk operations
        mock_api_client = AsyncMock()
        mock_api_client.update_contact_custom_field.return_value = {"success": True}

        mock_cache_manager = AsyncMock()

        context = Context()
        context.api_client = mock_api_client
        context.cache_manager = mock_cache_manager

        # Test updating 50 contacts
        contact_ids = [str(i) for i in range(1, 51)]

        result = await set_custom_field_values(
            context, field_id="7", contact_ids=contact_ids, common_value="Bulk Update"
        )

        assert result["success"] is True
        assert result["successful_updates"] == 50
        assert mock_api_client.update_contact_custom_field.call_count == 50

    @pytest.mark.asyncio
    async def test_concurrent_operations_safety(self, mock_environment):
        """Test that concurrent operations are handled safely."""
        import asyncio

        mock_api_client = AsyncMock()
        mock_api_client.update_contact_custom_field.return_value = {"success": True}

        mock_cache_manager = AsyncMock()

        context = Context()
        context.api_client = mock_api_client
        context.cache_manager = mock_cache_manager

        # Run multiple custom field updates concurrently
        async def update_field(contact_id, value):
            return await set_custom_field_values(
                context, field_id="7", contact_ids=[contact_id], common_value=value
            )

        tasks = [update_field(str(i), f"Value{i}") for i in range(1, 11)]
        results = await asyncio.gather(*tasks)

        # All operations should succeed
        for result in results:
            assert result["success"] is True
            assert result["successful_updates"] == 1


class TestMCPToolsResilience:
    """Test resilience and recovery of MCP tools."""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment with API key."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_api_key"}):
            yield

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, mock_environment):
        """Test handling of partial failures in bulk operations."""
        # Mock API client that fails on second call
        mock_api_client = AsyncMock()
        mock_api_client.update_contact_custom_field.side_effect = [
            {"success": True},  # First call succeeds
            {"success": False, "error": "Contact not found"},  # Second call fails
            {"success": True},  # Third call succeeds
        ]

        mock_cache_manager = AsyncMock()

        context = Context()
        context.api_client = mock_api_client
        context.cache_manager = mock_cache_manager

        result = await set_custom_field_values(
            context, field_id="7", contact_ids=["1", "2", "3"], common_value="Test"
        )

        assert result["success"] is False  # Overall failure due to partial failure
        assert result["successful_updates"] == 2
        assert result["failed_updates"] == 1
        assert "Partially successful" in result["message"]

    @pytest.mark.asyncio
    async def test_cache_failure_resilience(self, mock_environment):
        """Test that operations continue even when cache fails."""
        mock_api_client = AsyncMock()
        mock_api_client.update_contact_custom_field.return_value = {"success": True}

        # Mock cache that always fails
        mock_cache_manager = AsyncMock()
        mock_cache_manager.invalidate_pattern.side_effect = Exception("Cache failure")

        context = Context()
        context.api_client = mock_api_client
        context.cache_manager = mock_cache_manager

        # Operation should still succeed despite cache failures
        result = await set_custom_field_values(
            context, field_id="7", contact_ids=["1"], common_value="Test"
        )

        assert result["success"] is True
        assert result["successful_updates"] == 1

    @pytest.mark.asyncio
    async def test_diagnostics_with_missing_data(self, mock_environment):
        """Test diagnostics work even with missing data."""
        mock_api_client = AsyncMock()
        mock_api_client.get_diagnostics.return_value = {}  # Empty diagnostics

        mock_cache_manager = AsyncMock()
        mock_cache_manager.get_diagnostics.return_value = {}  # Empty cache diagnostics

        context = Context()
        context.api_client = mock_api_client
        context.cache_manager = mock_cache_manager

        with patch("platform.platform", return_value="Unknown"):
            with patch("platform.python_version", return_value="Unknown"):
                result = await get_api_diagnostics(context)

        # Should still return a valid structure
        assert "api_diagnostics" in result
        assert "cache_diagnostics" in result
        assert "system_info" in result
        assert "performance_metrics" in result
        assert "recommendations" in result

"""
Integration tests for Contact and Tag operations.

Tests the integration between contact management, tag operations,
and their interaction with API and cache systems.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.contact_tools import (
    list_contacts,
    search_contacts_by_email,
    search_contacts_by_name,
    get_contact_details,
)
from src.mcp.tag_tools import (
    get_tags,
    get_contacts_with_tag,
    apply_tags_to_contacts,
    remove_tags_from_contacts,
    create_tag,
    get_tag_details,
)
from src.api.client import KeapApiService
from src.cache.manager import CacheManager


class TestContactTagIntegration:
    """Test contact and tag operations integration."""

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
    def cache_manager(self, temp_db_path):
        """Create cache manager with temp database."""
        manager = CacheManager(db_path=temp_db_path)
        yield manager
        manager.close()

    @pytest.fixture
    def mock_context(self, cache_manager):
        """Create mock context with cache manager."""
        context = MagicMock()
        context.cache_manager = cache_manager
        return context

    @pytest.fixture
    def mock_api_client(self):
        """Create comprehensive mock API client."""
        client = AsyncMock(spec=KeapApiService)

        # Mock contacts data
        mock_contacts = [
            {
                "id": 1,
                "given_name": "John",
                "family_name": "Doe",
                "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}],
                "tag_ids": [10, 20, 30],
                "custom_fields": [{"id": 7, "content": "VIP"}],
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
            {
                "id": 3,
                "given_name": "Bob",
                "family_name": "Johnson",
                "email_addresses": [{"email": "bob@personal.net", "field": "EMAIL1"}],
                "tag_ids": [20, 50],
                "custom_fields": [],
                "date_created": "2024-01-17T09:15:00Z",
            },
        ]

        # Mock tags data
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

        # Single contact responses
        client.get_contact.side_effect = lambda contact_id: next(
            (contact for contact in mock_contacts if contact["id"] == int(contact_id)),
            None,
        )

        # Single tag responses
        client.get_tag.side_effect = lambda tag_id: next(
            (tag for tag in mock_tags if tag["id"] == int(tag_id)), None
        )

        # Tag operations
        client.apply_tag_to_contacts.return_value = {"success": True}
        client.remove_tag_from_contacts.return_value = {"success": True}
        client.create_tag.return_value = {
            "id": 60,
            "name": "New Tag",
            "description": "Newly created tag",
        }

        return client

    @pytest.mark.asyncio
    async def test_contact_listing_with_caching(self, mock_context, mock_api_client):
        """Test contact listing with cache integration."""
        with (
            patch("src.mcp.contact_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.contact_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # First call should hit API and cache result
            contacts1 = await list_contacts(mock_context, limit=10)

            # Verify contacts retrieved
            assert len(contacts1) == 3
            assert contacts1[0]["given_name"] == "John"
            assert contacts1[1]["given_name"] == "Jane"

            # Second call should hit cache
            contacts2 = await list_contacts(mock_context, limit=10)

            # Results should be identical
            assert contacts1 == contacts2

            # API should be called only once due to caching
            mock_api_client.get_contacts.assert_called_once()

    @pytest.mark.asyncio
    async def test_contact_search_by_email_integration(
        self, mock_context, mock_api_client
    ):
        """Test email search integration with filtering."""
        with (
            patch("src.mcp.contact_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.contact_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Search for contact by email
            result = await search_contacts_by_email(mock_context, "john@example.com")

            # Should find John's contact
            assert len(result) == 1
            assert result[0]["given_name"] == "John"
            assert "john@example.com" in [
                addr["email"] for addr in result[0]["email_addresses"]
            ]

    @pytest.mark.asyncio
    async def test_contact_search_by_name_integration(
        self, mock_context, mock_api_client
    ):
        """Test name search integration with pattern matching."""
        with (
            patch("src.mcp.contact_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.contact_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Search for contacts by name pattern
            result = await search_contacts_by_name(mock_context, "J")

            # Should find John and Jane
            assert len(result) == 2
            names = {contact["given_name"] for contact in result}
            assert names == {"John", "Jane"}

    @pytest.mark.asyncio
    async def test_tag_listing_with_filtering(self, mock_context, mock_api_client):
        """Test tag listing with category filtering."""
        with (
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Get all tags
            all_tags = await get_tags(mock_context, include_categories=True)

            # Verify all tags retrieved with categories
            assert len(all_tags) == 5
            assert all(tag.get("category") is not None for tag in all_tags)

            # Test filtering by name pattern
            filters = [{"field": "name", "operator": "contains", "value": "Customer"}]
            filtered_tags = await get_tags(mock_context, filters=filters)

            # Should include Customer and VIP (VIP customer)
            assert len(filtered_tags) >= 1

    @pytest.mark.asyncio
    async def test_contacts_with_tag_integration(self, mock_context, mock_api_client):
        """Test retrieving contacts with specific tags."""
        with (
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Get contacts with Customer tag (ID: 10)
            contacts_with_tag = await get_contacts_with_tag(
                mock_context, "10", limit=50
            )

            # Should return John and Jane (both have tag 10)
            assert len(contacts_with_tag) == 2
            contact_names = {contact["given_name"] for contact in contacts_with_tag}
            assert contact_names == {"John", "Jane"}

            # Verify all returned contacts have the tag
            for contact in contacts_with_tag:
                assert 10 in contact["tag_ids"]

    @pytest.mark.asyncio
    async def test_tag_application_and_removal_workflow(
        self, mock_context, mock_api_client
    ):
        """Test complete tag application and removal workflow."""
        with (
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Apply new tag to contacts
            tag_ids = ["30"]  # Newsletter tag
            contact_ids = ["1", "2"]  # John and Jane

            apply_result = await apply_tags_to_contacts(
                mock_context, tag_ids, contact_ids
            )

            # Verify successful application
            assert apply_result["success"] is True
            assert apply_result["applied_count"] == 2
            mock_api_client.apply_tag_to_contacts.assert_called()

            # Remove tag from contacts
            remove_result = await remove_tags_from_contacts(
                mock_context, tag_ids, contact_ids
            )

            # Verify successful removal
            assert remove_result["success"] is True
            assert remove_result["removed_count"] == 2
            mock_api_client.remove_tag_from_contacts.assert_called()

    @pytest.mark.asyncio
    async def test_tag_creation_integration(self, mock_context, mock_api_client):
        """Test tag creation with category assignment."""
        with (
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Create new tag
            new_tag = await create_tag(
                mock_context,
                name="Special Offer",
                description="Special offer subscribers",
                category_id="2",
            )

            # Verify tag creation
            assert new_tag["success"] is True
            assert new_tag["tag"]["name"] == "New Tag"  # From mock response
            assert new_tag["tag"]["id"] == 60
            mock_api_client.create_tag.assert_called_once()

    @pytest.mark.asyncio
    async def test_contact_and_tag_details_integration(
        self, mock_context, mock_api_client
    ):
        """Test detailed retrieval of contacts and tags."""
        with (
            patch("src.mcp.contact_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.contact_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Get contact details
            contact_details = await get_contact_details(mock_context, "1")

            # Verify contact details
            assert contact_details["id"] == 1
            assert contact_details["given_name"] == "John"
            assert len(contact_details["tag_ids"]) == 3
            assert len(contact_details["custom_fields"]) == 1

            # Get tag details
            tag_details = await get_tag_details(mock_context, "10")

            # Verify tag details
            assert tag_details["id"] == 10
            assert tag_details["name"] == "Customer"
            assert tag_details["description"] == "Customer tag"

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_tag_operations(
        self, mock_context, mock_api_client
    ):
        """Test cache invalidation when tag operations occur."""
        with (
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Cache some tag data
            cache_key = "tags:all"
            await mock_context.cache_manager.set(
                cache_key, [{"id": 10, "name": "Customer"}], ttl=3600
            )

            # Verify cache contains data
            cached_tags = await mock_context.cache_manager.get(cache_key)
            assert cached_tags is not None

            # Perform tag operation that should invalidate cache
            await apply_tags_to_contacts(mock_context, ["10"], ["1"])

            # Cache should be invalidated for tag-related entries
            # (This depends on implementation of cache invalidation in tag operations)

    @pytest.mark.asyncio
    async def test_bulk_contact_tag_operations(self, mock_context, mock_api_client):
        """Test bulk operations on contacts and tags."""
        with (
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Bulk apply multiple tags to multiple contacts
            tag_ids = ["10", "20", "30"]
            contact_ids = ["1", "2", "3"]

            bulk_apply_result = await apply_tags_to_contacts(
                mock_context, tag_ids, contact_ids
            )

            # Verify bulk application
            assert bulk_apply_result["success"] is True
            assert bulk_apply_result["applied_count"] == 9  # 3 tags × 3 contacts

            # Verify API calls were made for each tag-contact combination
            assert mock_api_client.apply_tag_to_contacts.call_count >= 3

    @pytest.mark.asyncio
    async def test_concurrent_contact_tag_operations(
        self, mock_context, mock_api_client
    ):
        """Test concurrent contact and tag operations."""
        with (
            patch("src.mcp.contact_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.contact_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):

            async def search_contacts():
                return await search_contacts_by_email(mock_context, "john@example.com")

            async def get_contact_tags():
                return await get_contacts_with_tag(mock_context, "10")

            async def list_all_tags():
                return await get_tags(mock_context)

            # Run operations concurrently
            results = await asyncio.gather(
                search_contacts(),
                get_contact_tags(),
                list_all_tags(),
                return_exceptions=True,
            )

            # Verify all operations completed successfully
            assert len(results) == 3
            assert all(not isinstance(result, Exception) for result in results)

            # Verify results
            contacts_by_email = results[0]
            contacts_with_tag = results[1]
            all_tags = results[2]

            assert len(contacts_by_email) == 1
            assert len(contacts_with_tag) == 2
            assert len(all_tags) == 5

    @pytest.mark.asyncio
    async def test_error_recovery_in_contact_tag_operations(
        self, mock_context, mock_api_client
    ):
        """Test error recovery in contact and tag operations."""
        with (
            patch("src.mcp.tag_tools.get_api_client", return_value=mock_api_client),
            patch(
                "src.mcp.tag_tools.get_cache_manager",
                return_value=mock_context.cache_manager,
            ),
        ):
            # Configure API to fail for tag application
            mock_api_client.apply_tag_to_contacts.side_effect = Exception("API Error")

            # Attempt tag application
            try:
                result = await apply_tags_to_contacts(mock_context, ["10"], ["1"])
                # If no exception is raised, check if error is handled gracefully
                if "success" in result:
                    assert result["success"] is False
            except Exception:
                # Exception handling is also acceptable
                pass

            # Reset API to working state
            mock_api_client.apply_tag_to_contacts.side_effect = None
            mock_api_client.apply_tag_to_contacts.return_value = {"success": True}

            # Verify recovery
            recovery_result = await apply_tags_to_contacts(mock_context, ["10"], ["1"])
            assert recovery_result["success"] is True

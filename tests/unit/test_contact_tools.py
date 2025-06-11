"""
Tests for contact-specific MCP tools.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.mcp.contact_tools import (
    list_contacts,
    search_contacts_by_email,
    search_contacts_by_name,
    get_contact_details,
)


class MockContext:
    def __init__(self):
        self.api_client = AsyncMock()
        self.cache_manager = AsyncMock()


@pytest.fixture
def mock_context():
    return MockContext()


@pytest.fixture
def sample_contacts():
    return [
        {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [
                {"field": "EMAIL", "email": "john.doe@example.com", "is_primary": True}
            ],
            "custom_fields": [{"id": 7, "content": "VIP"}],
            "tag_ids": [1, 2],
            "phone_numbers": [],
            "addresses": [],
        },
        {
            "id": 2,
            "given_name": "Jane",
            "family_name": "Smith",
            "email_addresses": [
                {
                    "field": "EMAIL",
                    "email": "jane.smith@example.com",
                    "is_primary": True,
                }
            ],
            "custom_fields": [{"id": 7, "content": "Regular"}],
            "tag_ids": [2],
            "phone_numbers": [],
            "addresses": [],
        },
    ]


@pytest.fixture
def expected_formatted_contacts():
    return [
        {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "full_name": "John Doe",
            "email": "john.doe@example.com",
            "email_addresses": [
                {"field": "EMAIL", "email": "john.doe@example.com", "is_primary": True}
            ],
            "phone_numbers": [],
            "addresses": [],
            "custom_fields": [{"id": 7, "content": "VIP"}],
            "tag_ids": [1, 2],
            "date_created": None,
            "last_updated": None,
        },
        {
            "id": 2,
            "given_name": "Jane",
            "family_name": "Smith",
            "full_name": "Jane Smith",
            "email": "jane.smith@example.com",
            "email_addresses": [
                {
                    "field": "EMAIL",
                    "email": "jane.smith@example.com",
                    "is_primary": True,
                }
            ],
            "phone_numbers": [],
            "addresses": [],
            "custom_fields": [{"id": 7, "content": "Regular"}],
            "tag_ids": [2],
            "date_created": None,
            "last_updated": None,
        },
    ]


class TestListContacts:
    @pytest.mark.asyncio
    async def test_list_contacts_basic(
        self, mock_context, sample_contacts, expected_formatted_contacts
    ):
        """Test basic contact listing."""
        mock_context.api_client.get_contacts.return_value = {
            "contacts": sample_contacts
        }
        mock_context.cache_manager.get.return_value = None

        result = await list_contacts(mock_context)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["email"] == "john.doe@example.com"
        assert result[1]["id"] == 2
        assert result[1]["email"] == "jane.smith@example.com"
        mock_context.api_client.get_contacts.assert_called_once()
        mock_context.cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_contacts_with_filters(self, mock_context, sample_contacts):
        """Test contact listing with filters."""
        mock_context.api_client.get_contacts.return_value = {
            "contacts": sample_contacts
        }
        mock_context.cache_manager.get.return_value = None

        filters = [{"field": "email", "operator": "contains", "value": "@example.com"}]

        with patch("src.mcp.contact_tools.validate_filter_conditions") as mock_validate:
            with patch(
                "src.mcp.contact_tools.optimize_filters_for_api",
                return_value=({}, filters),
            ):
                with patch(
                    "src.mcp.contact_tools.apply_complex_filters",
                    return_value=sample_contacts,
                ):
                    result = await list_contacts(mock_context, filters=filters)

        assert len(result) == 2
        mock_validate.assert_called_once_with(filters)
        mock_context.api_client.get_contacts.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_contacts_with_pagination(self, mock_context, sample_contacts):
        """Test contact listing with pagination."""
        mock_context.api_client.get_contacts.return_value = {
            "contacts": sample_contacts[:1]
        }
        mock_context.cache_manager.get.return_value = None

        result = await list_contacts(mock_context, limit=1, offset=0)

        mock_context.api_client.get_contacts.assert_called_once_with(limit=1, offset=0)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_contacts_with_order(self, mock_context, sample_contacts):
        """Test contact listing with ordering."""
        mock_context.api_client.get_contacts.return_value = {
            "contacts": sample_contacts
        }
        mock_context.cache_manager.get.return_value = None

        await list_contacts(mock_context, order_by="given_name", order_direction="DESC")

        mock_context.api_client.get_contacts.assert_called_once_with(
            limit=200, offset=0, order="given_name.DESC"
        )

    @pytest.mark.asyncio
    async def test_list_contacts_with_include(self, mock_context, sample_contacts):
        """Test contact listing with include fields."""
        mock_context.api_client.get_contacts.return_value = {
            "contacts": sample_contacts
        }
        mock_context.cache_manager.get.return_value = None

        include_fields = ["id", "given_name", "email"]

        with patch(
            "src.utils.contact_utils.process_contact_include_fields",
            side_effect=lambda x, y: x,
        ):
            result = await list_contacts(mock_context, include=include_fields)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_contacts_cache_hit(self, mock_context):
        """Test contact listing with cache hit."""
        cached_data = [{"id": 1, "cached": True}]
        mock_context.cache_manager.get.return_value = cached_data

        result = await list_contacts(mock_context)

        assert result == cached_data
        mock_context.api_client.get_contacts.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_contacts_error_handling(self, mock_context):
        """Test contact listing error handling."""
        mock_context.cache_manager.get.return_value = None
        mock_context.api_client.get_contacts.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await list_contacts(mock_context)


class TestSearchContactsByEmail:
    @pytest.mark.asyncio
    async def test_search_by_email_basic(self, mock_context, sample_contacts):
        """Test basic email search."""
        email = "john.doe@example.com"
        mock_context.api_client.get_contacts.return_value = {
            "contacts": [sample_contacts[0]]
        }
        mock_context.cache_manager.get.return_value = None

        result = await search_contacts_by_email(mock_context, email)

        assert len(result) == 1
        assert result[0]["email"] == email
        mock_context.api_client.get_contacts.assert_called_once_with(email=email)

    @pytest.mark.asyncio
    async def test_search_by_email_with_include(self, mock_context, sample_contacts):
        """Test email search with include fields."""
        email = "john.doe@example.com"
        include_fields = ["id", "given_name", "email"]
        mock_context.api_client.get_contacts.return_value = {
            "contacts": [sample_contacts[0]]
        }
        mock_context.cache_manager.get.return_value = None

        with patch(
            "src.utils.contact_utils.process_contact_include_fields",
            side_effect=lambda x, y: x,
        ):
            result = await search_contacts_by_email(
                mock_context, email, include=include_fields
            )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_email_cache_hit(self, mock_context):
        """Test email search with cache hit."""
        email = "test@example.com"
        cached_data = [{"id": 1, "email": email, "cached": True}]
        mock_context.cache_manager.get.return_value = cached_data

        result = await search_contacts_by_email(mock_context, email)

        assert result == cached_data
        mock_context.api_client.get_contacts.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_by_email_no_results(self, mock_context):
        """Test email search with no results."""
        email = "nonexistent@example.com"
        mock_context.api_client.get_contacts.return_value = {"contacts": []}
        mock_context.cache_manager.get.return_value = None

        result = await search_contacts_by_email(mock_context, email)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_by_email_error_handling(self, mock_context):
        """Test email search error handling."""
        mock_context.cache_manager.get.return_value = None
        mock_context.api_client.get_contacts.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await search_contacts_by_email(mock_context, "test@example.com")


class TestSearchContactsByName:
    @pytest.mark.asyncio
    async def test_search_by_name_basic(self, mock_context, sample_contacts):
        """Test basic name search."""
        name = "John"
        # Mock both given_name and family_name searches
        mock_context.api_client.get_contacts.side_effect = [
            {"contacts": [sample_contacts[0]]},  # given_name search
            {"contacts": []},  # family_name search
        ]
        mock_context.cache_manager.get.return_value = None

        result = await search_contacts_by_name(mock_context, name)

        assert len(result) == 1
        assert result[0]["given_name"] == name
        assert mock_context.api_client.get_contacts.call_count == 2

    @pytest.mark.asyncio
    async def test_search_by_name_duplicate_removal(
        self, mock_context, sample_contacts
    ):
        """Test name search removes duplicates."""
        name = "John"
        # Return the same contact from both searches
        mock_context.api_client.get_contacts.side_effect = [
            {"contacts": [sample_contacts[0]]},  # given_name search
            {"contacts": [sample_contacts[0]]},  # family_name search (same contact)
        ]
        mock_context.cache_manager.get.return_value = None

        result = await search_contacts_by_name(mock_context, name)

        assert len(result) == 1  # Should deduplicate
        assert result[0]["given_name"] == name

    @pytest.mark.asyncio
    async def test_search_by_name_with_include(self, mock_context, sample_contacts):
        """Test name search with include fields."""
        name = "John"
        include_fields = ["id", "given_name", "family_name"]
        mock_context.api_client.get_contacts.side_effect = [
            {"contacts": [sample_contacts[0]]},
            {"contacts": []},
        ]
        mock_context.cache_manager.get.return_value = None

        with patch(
            "src.utils.contact_utils.process_contact_include_fields",
            side_effect=lambda x, y: x,
        ):
            result = await search_contacts_by_name(
                mock_context, name, include=include_fields
            )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_by_name_cache_hit(self, mock_context):
        """Test name search with cache hit."""
        name = "John"
        cached_data = [{"id": 1, "given_name": name, "cached": True}]
        mock_context.cache_manager.get.return_value = cached_data

        result = await search_contacts_by_name(mock_context, name)

        assert result == cached_data
        mock_context.api_client.get_contacts.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_by_name_error_handling(self, mock_context):
        """Test name search error handling."""
        mock_context.cache_manager.get.return_value = None
        mock_context.api_client.get_contacts.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await search_contacts_by_name(mock_context, "John")


class TestGetContactDetails:
    @pytest.mark.asyncio
    async def test_get_contact_details_basic(self, mock_context, sample_contacts):
        """Test basic contact details retrieval."""
        contact_id = "123"
        contact_data = sample_contacts[0]
        mock_context.api_client.get_contact.return_value = contact_data
        mock_context.cache_manager.get.return_value = None

        result = await get_contact_details(mock_context, contact_id)

        assert result["id"] == contact_data["id"]
        assert result["email"] == "john.doe@example.com"
        assert result["given_name"] == "John"
        mock_context.api_client.get_contact.assert_called_once_with(contact_id)

    @pytest.mark.asyncio
    async def test_get_contact_details_with_include(
        self, mock_context, sample_contacts
    ):
        """Test contact details with include fields."""
        contact_id = "123"
        include_fields = ["id", "given_name", "email"]
        contact_data = sample_contacts[0]
        mock_context.api_client.get_contact.return_value = contact_data
        mock_context.cache_manager.get.return_value = None

        with patch(
            "src.utils.contact_utils.process_contact_include_fields",
            side_effect=lambda x, y: x,
        ):
            result = await get_contact_details(
                mock_context, contact_id, include=include_fields
            )

        assert result["id"] == contact_data["id"]
        assert result["given_name"] == "John"

    @pytest.mark.asyncio
    async def test_get_contact_details_cache_hit(self, mock_context):
        """Test contact details with cache hit."""
        contact_id = "123"
        cached_data = {"id": contact_id, "cached": True}
        mock_context.cache_manager.get.return_value = cached_data

        result = await get_contact_details(mock_context, contact_id)

        assert result == cached_data
        mock_context.api_client.get_contact.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_contact_details_error_handling(self, mock_context):
        """Test contact details error handling."""
        contact_id = "123"
        mock_context.cache_manager.get.return_value = None
        mock_context.api_client.get_contact.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await get_contact_details(mock_context, contact_id)

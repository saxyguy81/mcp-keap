"""
Unit tests for collection-based MCP tools.

Tests the consolidated collection-based tools including:
- list_contacts
- get_contact_schema  
- Collection operations (union, intersect, diff)
- Collection data access (get_collection_details with enhanced options)
- Field management (get_collection_fields, set_collection_fields, modify_contact_fields)
- Tag operations on collections (modify_collection_tags)
- API diagnostics
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_contact_schema,
    collection_union,
    collection_intersect,
    collection_diff,
    get_collection_details,
    get_tags,
    modify_collection_tags,
    get_api_diagnostics,
    _apply_filters,
    _contact_matches_filters,
    _field_matches_condition
)


@pytest.fixture
def mock_context():
    """Create a mock MCP context"""
    return Context()


@pytest.fixture
def mock_api_client():
    """Create a mock API client"""
    client = AsyncMock()
    client.get_contacts.return_value = {
        "contacts": [
            {"id": 1, "given_name": "John", "family_name": "Doe", "email": "john@example.com"},
            {"id": 2, "given_name": "Jane", "family_name": "Smith", "email": "jane@example.com"},
            {"id": 3, "given_name": "Bob", "family_name": "Johnson", "email": "bob@company.com"}
        ]
    }
    client.get_contact.return_value = {"id": 1, "given_name": "John", "family_name": "Doe"}
    client.get_tags.return_value = [
        {"id": 1, "name": "VIP", "category_id": 1},
        {"id": 2, "name": "Customer", "category_id": 1}
    ]
    client.apply_tag_to_contact = AsyncMock()
    client.remove_tag_from_contact = AsyncMock()
    client.get_diagnostics.return_value = {"total_requests": 10, "successful_requests": 9}
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_collection_manager():
    """Create a mock collection manager"""
    manager = MagicMock()
    manager.create_collection.return_value = "test_collection_123"
    manager.get_collection_ids.return_value = [1, 2, 3]
    manager.count.return_value = 3
    manager.union.return_value = "union_collection_456"
    manager.intersect.return_value = "intersect_collection_789"
    manager.diff.return_value = "diff_collection_012"
    manager.get_collection.return_value = MagicMock(
        id="test_collection_123",
        contact_ids={1, 2, 3},
        created_at=1234567890.0,
        name="Test Collection",
        description="A test collection"
    )
    manager.get_diagnostics.return_value = {
        "active_collections": 5,
        "total_contacts_across_collections": 100
    }
    return manager


class TestListContacts:
    """Test list_contacts function"""

    @patch('src.mcp.tools_collections.get_api_client')
    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_list_contacts_basic(self, mock_get_cm, mock_get_api, mock_context):
        """Test basic list_contacts functionality"""
        # Create mock API client
        mock_api_client = AsyncMock()
        mock_api_client.get_contacts.return_value = {
            "contacts": [
                {"id": 1, "given_name": "John", "email": "john@example.com"},
                {"id": 2, "given_name": "Jane", "email": "jane@example.com"},
                {"id": 3, "given_name": "Bob", "email": "bob@example.com"}
            ]
        }
        mock_api_client.close = AsyncMock()
        mock_get_api.return_value = mock_api_client
        
        # Create mock collection manager
        mock_collection_manager = MagicMock()
        mock_collection_manager.create_collection.return_value = "test_collection_123"
        mock_get_cm.return_value = mock_collection_manager
        
        result = await list_contacts(mock_context)
        
        assert result["collection_id"] == "test_collection_123"
        assert result["count"] == 3
        assert "description" in result
        
        mock_api_client.get_contacts.assert_called_once()
        mock_collection_manager.create_collection.assert_called_once()
        mock_api_client.close.assert_called_once()

    @patch('src.mcp.tools_collections.get_api_client')
    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_list_contacts_with_filters(self, mock_get_cm, mock_get_api, mock_context,
                                             mock_api_client, mock_collection_manager):
        """Test list_contacts with filters"""
        mock_get_api.return_value = mock_api_client
        mock_get_cm.return_value = mock_collection_manager
        
        filters = [{"field": "email", "operator": "contains", "value": "@company.com"}]
        
        result = await list_contacts(mock_context, filters=filters)
        
        assert result["collection_id"] == "test_collection_123"
        mock_collection_manager.create_collection.assert_called_once()
        
        # Check that the description mentions filters
        call_args = mock_collection_manager.create_collection.call_args
        assert "filters" in call_args.kwargs["description"].lower()

    @patch('src.mcp.tools_collections.get_api_client')
    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_list_contacts_with_parameters(self, mock_get_cm, mock_get_api, mock_context,
                                                mock_api_client, mock_collection_manager):
        """Test list_contacts with various parameters"""
        mock_get_api.return_value = mock_api_client
        mock_get_cm.return_value = mock_collection_manager
        
        await list_contacts(
            mock_context,
            limit=50,
            offset=10,
            order_by="given_name",
            order_direction="DESC"
        )
        
        mock_api_client.get_contacts.assert_called_once_with(
            limit=50,
            offset=10,
            order_by="given_name",
            order_direction="DESC",
            include_custom_fields=True,
            include_tags=True
        )

    @patch('src.mcp.tools_collections.get_api_client')
    async def test_list_contacts_api_error(self, mock_get_api, mock_context, mock_api_client):
        """Test list_contacts with API error"""
        mock_get_api.return_value = mock_api_client
        mock_api_client.get_contacts.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await list_contacts(mock_context)
        
        mock_api_client.close.assert_called_once()


class TestGetContactSchema:
    """Test get_contact_schema function"""

    @patch('src.mcp.tools_collections.get_api_client')
    async def test_get_contact_schema(self, mock_get_api, mock_context, mock_api_client):
        """Test get_contact_schema functionality"""
        mock_get_api.return_value = mock_api_client
        
        result = await get_contact_schema(mock_context)
        
        assert "standard_fields" in result
        assert "custom_fields" in result
        assert "supported_operators" in result
        assert "filter_examples" in result
        
        # Check that we have expected operators
        operators = result["supported_operators"]
        assert "equals" in operators
        assert "contains" in operators
        assert "not_equals" in operators
        
        # Check that we have filter examples
        examples = result["filter_examples"]
        assert len(examples) > 0
        assert all("description" in ex and "filter" in ex for ex in examples[:3])
        
        mock_api_client.close.assert_called_once()

    @patch('src.mcp.tools_collections.get_api_client')
    async def test_get_contact_schema_no_contacts(self, mock_get_api, mock_context, mock_api_client):
        """Test get_contact_schema when no contacts available"""
        mock_get_api.return_value = mock_api_client
        mock_api_client.get_contacts.return_value = {"contacts": []}
        
        result = await get_contact_schema(mock_context)
        
        assert result["standard_fields"] == []
        assert "supported_operators" in result


class TestCollectionOperations:
    """Test collection set operations"""

    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_collection_union(self, mock_get_cm, mock_context, mock_collection_manager):
        """Test collection_union function"""
        mock_get_cm.return_value = mock_collection_manager
        
        result = await collection_union(mock_context, ["collection_a", "collection_b"])
        
        assert result["collection_id"] == "union_collection_456"
        assert result["count"] == 3
        assert "union" in result["operation"].lower()
        
        mock_collection_manager.union.assert_called_once_with("collection_a", "collection_b")

    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_collection_intersect(self, mock_get_cm, mock_context, mock_collection_manager):
        """Test collection_intersect function"""
        mock_get_cm.return_value = mock_collection_manager
        
        result = await collection_intersect(mock_context, ["collection_a", "collection_b"])
        
        assert result["collection_id"] == "intersect_collection_789"
        assert "intersection" in result["operation"].lower()
        
        mock_collection_manager.intersect.assert_called_once_with("collection_a", "collection_b")

    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_collection_diff(self, mock_get_cm, mock_context, mock_collection_manager):
        """Test collection_diff function"""
        mock_get_cm.return_value = mock_collection_manager
        
        result = await collection_diff(mock_context, "collection_a", ["collection_b"])
        
        assert result["collection_id"] == "diff_collection_012"
        assert "difference" in result["operation"].lower()
        
        mock_collection_manager.diff.assert_called_once_with("collection_a", "collection_b")

    # REMOVED: test_collection_count - Use get_collection_details(count_only=True) instead

    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_collection_operations_error(self, mock_get_cm, mock_context, mock_collection_manager):
        """Test collection operations with errors"""
        mock_get_cm.return_value = mock_collection_manager
        mock_collection_manager.union.side_effect = ValueError("Collection not found")
        
        with pytest.raises(ValueError, match="Collection not found"):
            await collection_union(mock_context, ["invalid_a", "invalid_b"])


class TestCollectionDataAccess:
    """Test collection data access functions"""

    @patch('src.mcp.tools_collections.get_collection_manager')
    @patch('src.mcp.tools_collections.get_api_client')
    async def test_get_collection_details(self, mock_get_api, mock_get_cm, mock_context):
        """Test get_collection_details function"""
        # Create mock collection manager
        mock_collection_manager = MagicMock()
        mock_collection_manager.get_contact_ids.return_value = [1, 2, 3]
        mock_get_cm.return_value = mock_collection_manager
        
        # Create mock API client
        mock_api_client = AsyncMock()
        mock_api_client.get_contact.return_value = {"id": 1, "given_name": "John", "family_name": "Doe"}
        mock_api_client.close = AsyncMock()
        mock_get_api.return_value = mock_api_client
        
        result = await get_collection_details(mock_context, "test_collection")
        
        assert result["collection_id"] == "test_collection"
        assert result["count"] == 3
        assert "contacts" in result
        
        # Should fetch details for each contact ID
        assert mock_api_client.get_contact.call_count == 3
        mock_api_client.close.assert_called_once()

    @patch('src.mcp.tools_collections.get_collection_manager')
    @patch('src.mcp.tools_collections.get_api_client')
    async def test_get_collection_details_with_fields(self, mock_get_api, mock_get_cm, mock_context):
        """Test get_collection_details with field filtering"""
        # Create mock collection manager
        mock_collection_manager = MagicMock()
        mock_collection_manager.get_contact_ids.return_value = [1, 2, 3]
        mock_get_cm.return_value = mock_collection_manager
        
        # Create mock API client
        mock_api_client = AsyncMock()
        mock_api_client.get_contact.return_value = {
            "id": 1, "given_name": "John", "family_name": "Doe", "email": "john@example.com"
        }
        mock_api_client.close = AsyncMock()
        mock_get_api.return_value = mock_api_client
        
        await get_collection_details(mock_context, "test_collection", fields=["id", "given_name"])
        
        mock_api_client.get_contact.assert_called()

    @patch('src.mcp.tools_collections.get_collection_manager')
    @patch('src.mcp.tools_collections.get_api_client')
    async def test_get_collection_details_api_error(self, mock_get_api, mock_get_cm, mock_context,
                                                   mock_api_client, mock_collection_manager):
        """Test get_collection_details with API errors"""
        mock_get_cm.return_value = mock_collection_manager
        mock_get_api.return_value = mock_api_client
        mock_api_client.get_contact.side_effect = Exception("Contact not found")
        
        # Should continue processing despite individual contact errors
        result = await get_collection_details(mock_context, "test_collection")
        assert result["count"] == 0  # No contacts returned due to errors

    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_get_collection_details_ids_only(self, mock_get_cm, mock_context, mock_collection_manager):
        """Test get_collection_details with fields=['id'] (replaces get_collection_ids)"""
        mock_get_cm.return_value = mock_collection_manager
        mock_collection_manager.get_contact_ids.return_value = [1, 2, 3]
        
        result = await get_collection_details(mock_context, "test_collection", fields=["id"])
        
        assert result["collection_id"] == "test_collection"
        assert result["contact_ids"] == [1, 2, 3]
        assert result["count"] == 3

    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_get_collection_details_nonexistent(self, mock_get_cm, mock_context, mock_collection_manager):
        """Test get_collection_details with non-existent collection"""
        mock_get_cm.return_value = mock_collection_manager
        mock_collection_manager.get_contact_ids.return_value = []
        mock_collection_manager.get_collection.return_value = None
        
        with pytest.raises(ValueError, match="Collection test_collection not found"):
            await get_collection_details(mock_context, "test_collection")


class TestTagOperations:
    """Test tag-related operations"""

    @patch('src.mcp.tools_collections.get_api_client')
    async def test_get_tags(self, mock_get_api, mock_context, mock_api_client):
        """Test get_tags function"""
        mock_get_api.return_value = mock_api_client
        
        result = await get_tags(mock_context)
        
        assert len(result) == 2
        assert result[0]["name"] == "VIP"
        assert result[1]["name"] == "Customer"
        
        mock_api_client.get_tags.assert_called_once_with(limit=200)
        mock_api_client.close.assert_called_once()

    @patch('src.mcp.tools_collections.get_api_client')
    async def test_get_tags_with_category(self, mock_get_api, mock_context, mock_api_client):
        """Test get_tags with category filter"""
        mock_get_api.return_value = mock_api_client
        
        await get_tags(mock_context, category_id=1, limit=50)
        
        mock_api_client.get_tags.assert_called_once_with(limit=50)

    @patch('src.mcp.tools_collections.get_collection_manager')
    @patch('src.mcp.tools_collections.get_api_client')
    async def test_modify_collection_tags(self, mock_get_api, mock_get_cm, mock_context):
        """Test modify_collection_tags function"""
        # Create mock collection manager
        mock_collection_manager = MagicMock()
        mock_collection_manager.get_contact_ids.return_value = [1, 2, 3]
        mock_get_cm.return_value = mock_collection_manager
        
        # Create mock API client
        mock_api_client = AsyncMock()
        mock_api_client.apply_tag_to_contact = AsyncMock()
        mock_api_client.close = AsyncMock()
        mock_get_api.return_value = mock_api_client
        
        result = await modify_collection_tags(
            mock_context, "test_collection", [1, 2], operation="add"
        )
        
        assert result["collection_id"] == "test_collection"
        assert result["operation"] == "add"
        assert result["tag_ids"] == [1, 2]
        assert result["total_operations"] == 6  # 3 contacts × 2 tags
        assert result["successful"] == 6
        assert result["failed"] == 0
        
        # Should call apply_tag_to_contact for each contact-tag combination
        assert mock_api_client.apply_tag_to_contact.call_count == 6
        mock_api_client.close.assert_called_once()

    @patch('src.mcp.tools_collections.get_collection_manager')
    @patch('src.mcp.tools_collections.get_api_client')
    async def test_modify_collection_tags_remove_operation(self, mock_get_api, mock_get_cm, mock_context):
        """Test modify_collection_tags with remove operation"""
        # Create mock collection manager
        mock_collection_manager = MagicMock()
        mock_collection_manager.get_contact_ids.return_value = [1, 2, 3]
        mock_get_cm.return_value = mock_collection_manager
        
        # Create mock API client
        mock_api_client = AsyncMock()
        mock_api_client.remove_tag_from_contact = AsyncMock()
        mock_api_client.close = AsyncMock()
        mock_get_api.return_value = mock_api_client
        
        await modify_collection_tags(
            mock_context, "test_collection", [1], operation="remove"
        )
        
        # Should call remove_tag_from_contact for each contact
        assert mock_api_client.remove_tag_from_contact.call_count == 3

    @patch('src.mcp.tools_collections.get_collection_manager')
    @patch('src.mcp.tools_collections.get_api_client')
    async def test_modify_collection_tags_invalid_operation(self, mock_get_api, mock_get_cm, mock_context):
        """Test modify_collection_tags with invalid operation"""
        # Create mock collection manager
        mock_collection_manager = MagicMock()
        mock_collection_manager.get_contact_ids.return_value = [1, 2, 3]
        mock_get_cm.return_value = mock_collection_manager
        
        # Create mock API client
        mock_api_client = AsyncMock()
        mock_api_client.close = AsyncMock()
        mock_get_api.return_value = mock_api_client
        
        result = await modify_collection_tags(
            mock_context, "test_collection", [1], operation="invalid"
        )
        
        # Should have failed operations
        assert result["successful"] == 0
        assert result["failed"] == 3

    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_modify_collection_tags_nonexistent_collection(self, mock_get_cm, mock_context, mock_collection_manager):
        """Test modify_collection_tags with non-existent collection"""
        mock_get_cm.return_value = mock_collection_manager
        mock_collection_manager.get_contact_ids.return_value = []
        
        with pytest.raises(ValueError, match="Collection test_collection not found"):
            await modify_collection_tags(mock_context, "test_collection", [1])


class TestSystemOperations:
    """Test system diagnostic operations"""

    @patch('src.mcp.tools_collections.get_api_client')
    @patch('src.mcp.tools_collections.get_cache_manager')
    @patch('src.mcp.tools_collections.get_collection_manager')
    async def test_get_api_diagnostics(self, mock_get_cm, mock_get_cache, mock_get_api, mock_context):
        """Test get_api_diagnostics function"""
        # Setup mocks
        mock_api_client = MagicMock()
        mock_api_client.get_diagnostics.return_value = {
            "total_requests": 100,
            "successful_requests": 95,
            "average_response_time": 0.5,
            "endpoints_called": {"get_contacts": 50, "get_tags": 30},
            "error_counts": {"timeout": 3, "404": 2}
        }
        mock_get_api.return_value = mock_api_client
        
        mock_cache_manager = MagicMock()
        mock_cache_manager.get_diagnostics.return_value = {
            "cache_hits": 200,
            "total_requests": 300
        }
        mock_get_cache.return_value = mock_cache_manager
        
        mock_collection_manager = MagicMock()
        mock_collection_manager.get_diagnostics.return_value = {
            "active_collections": 10,
            "total_contacts_across_collections": 500
        }
        mock_get_cm.return_value = mock_collection_manager
        
        result = await get_api_diagnostics(mock_context)
        
        assert "api_diagnostics" in result
        assert "cache_diagnostics" in result
        assert "collection_diagnostics" in result
        assert "system_info" in result
        assert "performance_metrics" in result
        assert "recommendations" in result
        
        # Check performance metrics calculation
        perf = result["performance_metrics"]
        assert perf["total_requests"] == 100
        assert perf["success_rate"] == 95.0  # 95/100 * 100
        assert perf["average_response_time"] == 0.5
        assert abs(perf["cache_hit_rate"] - 66.66666666666667) < 0.000001  # 200/300 * 100 (floating point tolerance)


class TestHelperFunctions:
    """Test helper functions for filtering"""

    def test_apply_filters_no_filters(self):
        """Test _apply_filters with no filters"""
        contacts = [{"id": 1}, {"id": 2}]
        result = _apply_filters(contacts, None)
        assert result == contacts
        
        result = _apply_filters(contacts, [])
        assert result == contacts

    def test_apply_filters_with_matches(self):
        """Test _apply_filters with matching contacts"""
        contacts = [
            {
                "id": 1, 
                "email_addresses": [{"email": "john@company.com", "field": "EMAIL1"}]
            },
            {
                "id": 2, 
                "email_addresses": [{"email": "jane@example.com", "field": "EMAIL1"}]
            },
            {
                "id": 3, 
                "email_addresses": [{"email": "bob@company.com", "field": "EMAIL1"}]
            }
        ]
        filters = [{"field": "email", "operator": "contains", "value": "@company.com"}]
        
        result = _apply_filters(contacts, filters)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 3

    def test_contact_matches_filters_all_match(self):
        """Test _contact_matches_filters when all filters match"""
        contact = {
            "id": 1, 
            "email_addresses": [{"email": "john@company.com", "field": "EMAIL1"}],
            "given_name": "John"
        }
        filters = [
            {"field": "email", "operator": "contains", "value": "@company.com"},
            {"field": "given_name", "operator": "equals", "value": "John"}
        ]
        
        assert _contact_matches_filters(contact, filters) is True

    def test_contact_matches_filters_partial_match(self):
        """Test _contact_matches_filters when only some filters match"""
        contact = {
            "id": 1, 
            "email_addresses": [{"email": "john@company.com", "field": "EMAIL1"}],
            "given_name": "John"
        }
        filters = [
            {"field": "email", "operator": "contains", "value": "@company.com"},
            {"field": "given_name", "operator": "equals", "value": "Jane"}
        ]
        
        assert _contact_matches_filters(contact, filters) is False

    def test_field_matches_condition_equals(self):
        """Test _field_matches_condition with equals operator"""
        contact = {"given_name": "John"}
        
        assert _field_matches_condition(contact, "given_name", "equals", "John") is True
        assert _field_matches_condition(contact, "given_name", "equals", "john") is True  # Case insensitive
        assert _field_matches_condition(contact, "given_name", "equals", "Jane") is False

    def test_field_matches_condition_contains(self):
        """Test _field_matches_condition with contains operator"""
        # Test with regular field
        contact = {"description": "john.doe@company.com"}
        
        assert _field_matches_condition(contact, "description", "contains", "@company") is True
        assert _field_matches_condition(contact, "description", "contains", "john") is True
        assert _field_matches_condition(contact, "description", "contains", "@example") is False
        
        # Test with email field (uses email_addresses array)
        contact_with_email = {
            "email_addresses": [
                {"email": "john.doe@company.com", "field": "EMAIL1"}
            ]
        }
        assert _field_matches_condition(contact_with_email, "email", "contains", "@company") is True
        assert _field_matches_condition(contact_with_email, "email", "contains", "john") is True
        assert _field_matches_condition(contact_with_email, "email", "contains", "@example") is False

    def test_field_matches_condition_starts_with(self):
        """Test _field_matches_condition with starts_with operator"""
        contact = {"given_name": "John"}
        
        assert _field_matches_condition(contact, "given_name", "starts_with", "Jo") is True
        assert _field_matches_condition(contact, "given_name", "starts_with", "ja") is False

    def test_field_matches_condition_ends_with(self):
        """Test _field_matches_condition with ends_with operator"""
        # Test with regular field
        contact = {"website": "john@company.com"}
        
        assert _field_matches_condition(contact, "website", "ends_with", ".com") is True
        assert _field_matches_condition(contact, "website", "ends_with", ".org") is False
        
        # Test with email field (uses email_addresses array)
        contact_with_email = {
            "email_addresses": [
                {"email": "john@company.com", "field": "EMAIL1"}
            ]
        }
        assert _field_matches_condition(contact_with_email, "email", "ends_with", ".com") is True
        assert _field_matches_condition(contact_with_email, "email", "ends_with", ".org") is False

    def test_field_matches_condition_null_checks(self):
        """Test _field_matches_condition with null checks"""
        contact = {"given_name": "John", "middle_name": None}
        
        assert _field_matches_condition(contact, "middle_name", "is_null", None) is True
        assert _field_matches_condition(contact, "given_name", "is_null", None) is False
        assert _field_matches_condition(contact, "given_name", "is_not_null", None) is True
        assert _field_matches_condition(contact, "middle_name", "is_not_null", None) is False

    def test_field_matches_condition_not_operators(self):
        """Test _field_matches_condition with not operators"""
        # Test with regular field
        contact = {"website": "john@company.com"}
        
        assert _field_matches_condition(contact, "website", "not_equals", "jane@company.com") is True
        assert _field_matches_condition(contact, "website", "not_equals", "john@company.com") is False
        assert _field_matches_condition(contact, "website", "not_contains", "@example") is True
        assert _field_matches_condition(contact, "website", "not_contains", "@company") is False
        
        # Test with email field (uses email_addresses array)
        contact_with_email = {
            "email_addresses": [
                {"email": "john@company.com", "field": "EMAIL1"}
            ]
        }
        assert _field_matches_condition(contact_with_email, "email", "not_equals", "jane@company.com") is True
        assert _field_matches_condition(contact_with_email, "email", "not_equals", "john@company.com") is False
        assert _field_matches_condition(contact_with_email, "email", "not_contains", "@example") is True
        assert _field_matches_condition(contact_with_email, "email", "not_contains", "@company") is False

    def test_field_matches_condition_missing_field(self):
        """Test _field_matches_condition with missing field"""
        contact = {"given_name": "John"}
        
        assert _field_matches_condition(contact, "missing_field", "is_null", None) is True
        assert _field_matches_condition(contact, "missing_field", "not_equals", "anything") is True
        assert _field_matches_condition(contact, "missing_field", "equals", "anything") is False
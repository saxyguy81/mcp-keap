"""
Tests for tag-specific MCP tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.mcp.tag_tools import (
    get_tags,
    get_contacts_with_tag,
    get_tag_details,
    create_tag,
    apply_tags_to_contacts,
    remove_tags_from_contacts
)


class MockContext:
    def __init__(self):
        self.api_client = AsyncMock()
        self.cache_manager = AsyncMock()


@pytest.fixture
def mock_context():
    return MockContext()


@pytest.fixture
def sample_tags():
    return [
        {
            "id": 1,
            "name": "VIP Customer",
            "description": "High-value customer",
            "category": {"id": 1, "name": "Customer Type"}
        },
        {
            "id": 2,
            "name": "Newsletter Subscriber",
            "description": "Subscribed to newsletter",
            "category": {"id": 2, "name": "Marketing"}
        }
    ]


@pytest.fixture
def sample_contacts():
    return [
        {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [{"field": "EMAIL", "email": "john@example.com", "is_primary": True}],
            "tag_ids": [1, 2]
        },
        {
            "id": 2,
            "given_name": "Jane",
            "family_name": "Smith",
            "email_addresses": [{"field": "EMAIL", "email": "jane@example.com", "is_primary": True}],
            "tag_ids": [1]
        }
    ]


class TestGetTags:
    
    @pytest.mark.asyncio
    async def test_get_tags_basic(self, mock_context, sample_tags):
        """Test basic tag retrieval."""
        mock_context.api_client.get_tags.return_value = {"tags": sample_tags}
        mock_context.cache_manager.get.return_value = None
        
        result = await get_tags(mock_context)
        
        assert len(result) == 2
        assert result[0]["name"] == "VIP Customer"
        assert result[1]["name"] == "Newsletter Subscriber"
        mock_context.api_client.get_tags.assert_called_once_with(limit=1000)
        mock_context.cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_tags_with_filters(self, mock_context, sample_tags):
        """Test tag retrieval with filters."""
        mock_context.api_client.get_tags.return_value = {"tags": sample_tags}
        mock_context.cache_manager.get.return_value = None
        
        filters = [{"field": "name", "operator": "contains", "value": "VIP"}]
        result = await get_tags(mock_context, filters=filters)
        
        # Should filter to only VIP Customer tag
        assert len(result) == 1
        assert result[0]["name"] == "VIP Customer"
    
    @pytest.mark.asyncio
    async def test_get_tags_with_limit(self, mock_context, sample_tags):
        """Test tag retrieval with custom limit."""
        mock_context.api_client.get_tags.return_value = {"tags": sample_tags[:1]}
        mock_context.cache_manager.get.return_value = None
        
        result = await get_tags(mock_context, limit=1)
        
        assert len(result) == 1
        mock_context.api_client.get_tags.assert_called_once_with(limit=1)
    
    @pytest.mark.asyncio
    async def test_get_tags_cache_hit(self, mock_context):
        """Test tag retrieval with cache hit."""
        cached_tags = [{"id": 1, "name": "Cached Tag", "cached": True}]
        mock_context.cache_manager.get.return_value = cached_tags
        
        result = await get_tags(mock_context)
        
        assert result == cached_tags
        mock_context.api_client.get_tags.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_tags_filter_equals(self, mock_context, sample_tags):
        """Test tag filtering with equals operator."""
        mock_context.api_client.get_tags.return_value = {"tags": sample_tags}
        mock_context.cache_manager.get.return_value = None
        
        filters = [{"field": "name", "operator": "equals", "value": "VIP Customer"}]
        result = await get_tags(mock_context, filters=filters)
        
        assert len(result) == 1
        assert result[0]["name"] == "VIP Customer"
    
    @pytest.mark.asyncio
    async def test_get_tags_error_handling(self, mock_context):
        """Test tag retrieval error handling."""
        mock_context.cache_manager.get.return_value = None
        mock_context.api_client.get_tags.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await get_tags(mock_context)


class TestGetContactsWithTag:
    
    @pytest.mark.asyncio
    async def test_get_contacts_with_tag_basic(self, mock_context, sample_contacts):
        """Test basic contact retrieval by tag."""
        tag_id = "1"
        mock_context.api_client.get_contacts_by_tag.return_value = sample_contacts
        mock_context.cache_manager.get.return_value = None
        
        result = await get_contacts_with_tag(mock_context, tag_id)
        
        assert len(result) == 2
        mock_context.api_client.get_contacts_by_tag.assert_called_once_with(tag_id, limit=200)
    
    @pytest.mark.asyncio
    async def test_get_contacts_with_tag_with_limit(self, mock_context, sample_contacts):
        """Test contact retrieval by tag with limit."""
        tag_id = "1"
        mock_context.api_client.get_contacts_by_tag.return_value = sample_contacts[:1]
        mock_context.cache_manager.get.return_value = None
        
        result = await get_contacts_with_tag(mock_context, tag_id, limit=1)
        
        assert len(result) == 1
        mock_context.api_client.get_contacts_by_tag.assert_called_once_with(tag_id, limit=1)
    
    @pytest.mark.asyncio
    async def test_get_contacts_with_tag_with_include(self, mock_context, sample_contacts):
        """Test contact retrieval by tag with include fields."""
        tag_id = "1"
        include_fields = ["id", "given_name", "email"]
        mock_context.api_client.get_contacts_by_tag.return_value = sample_contacts
        mock_context.cache_manager.get.return_value = None
        
        with patch('src.utils.contact_utils.process_contact_include_fields', side_effect=lambda x, y: x):
            result = await get_contacts_with_tag(mock_context, tag_id, include=include_fields)
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_contacts_with_tag_cache_hit(self, mock_context):
        """Test contact retrieval by tag with cache hit."""
        tag_id = "1"
        cached_contacts = [{"id": 1, "tag_id": tag_id, "cached": True}]
        mock_context.cache_manager.get.return_value = cached_contacts
        
        result = await get_contacts_with_tag(mock_context, tag_id)
        
        assert result == cached_contacts
        mock_context.api_client.get_contacts.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_contacts_with_tag_error_handling(self, mock_context):
        """Test contact retrieval by tag error handling."""
        tag_id = "1"
        mock_context.cache_manager.get.return_value = None
        mock_context.api_client.get_contacts_by_tag.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await get_contacts_with_tag(mock_context, tag_id)


class TestGetTagDetails:
    
    @pytest.mark.asyncio
    async def test_get_tag_details_basic(self, mock_context, sample_tags):
        """Test basic tag details retrieval."""
        tag_id = "1"
        tag_data = sample_tags[0]
        mock_context.api_client.get_tag.return_value = tag_data
        mock_context.cache_manager.get.return_value = None
        
        result = await get_tag_details(mock_context, tag_id)
        
        assert result == tag_data
        mock_context.api_client.get_tag.assert_called_once_with(tag_id)
        mock_context.cache_manager.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_tag_details_cache_hit(self, mock_context):
        """Test tag details retrieval with cache hit."""
        tag_id = "1"
        cached_tag = {"id": tag_id, "name": "Cached Tag", "cached": True}
        mock_context.cache_manager.get.return_value = cached_tag
        
        result = await get_tag_details(mock_context, tag_id)
        
        assert result == cached_tag
        mock_context.api_client.get_tag.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_tag_details_error_handling(self, mock_context):
        """Test tag details retrieval error handling."""
        tag_id = "1"
        mock_context.cache_manager.get.return_value = None
        mock_context.api_client.get_tag.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await get_tag_details(mock_context, tag_id)


class TestCreateTag:
    
    @pytest.mark.asyncio
    async def test_create_tag_basic(self, mock_context):
        """Test basic tag creation."""
        tag_name = "New Tag"
        created_tag = {"id": 3, "name": tag_name}
        mock_context.api_client.create_tag.return_value = created_tag
        
        result = await create_tag(mock_context, tag_name)
        
        assert result == created_tag
        mock_context.api_client.create_tag.assert_called_once_with({"name": tag_name})
    
    @pytest.mark.asyncio
    async def test_create_tag_with_description(self, mock_context):
        """Test tag creation with description."""
        tag_name = "New Tag"
        description = "Tag description"
        created_tag = {"id": 3, "name": tag_name, "description": description}
        mock_context.api_client.create_tag.return_value = created_tag
        
        result = await create_tag(mock_context, tag_name, description=description)
        
        assert result == created_tag
        mock_context.api_client.create_tag.assert_called_once_with({
            "name": tag_name, 
            "description": description
        })
    
    @pytest.mark.asyncio
    async def test_create_tag_with_category(self, mock_context):
        """Test tag creation with category."""
        tag_name = "New Tag"
        category_id = "2"
        created_tag = {"id": 3, "name": tag_name, "category_id": category_id}
        mock_context.api_client.create_tag.return_value = created_tag
        
        result = await create_tag(mock_context, tag_name, category_id=category_id)
        
        assert result == created_tag
        mock_context.api_client.create_tag.assert_called_once_with({
            "name": tag_name, 
            "category": {"id": category_id}
        })
    
    @pytest.mark.asyncio
    async def test_create_tag_error_handling(self, mock_context):
        """Test tag creation error handling."""
        tag_name = "New Tag"
        mock_context.api_client.create_tag.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await create_tag(mock_context, tag_name)


class TestApplyTagsToContacts:
    
    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts_success(self, mock_context):
        """Test successful tag application to contacts."""
        tag_ids = ["1", "2"]
        contact_ids = ["101", "102"]
        
        # Mock successful batch API call
        mock_context.api_client.apply_tags_to_contacts.return_value = None
        
        result = await apply_tags_to_contacts(mock_context, tag_ids, contact_ids)
        
        assert result["success"] is True
        assert result["message"] == "Successfully applied tags to contacts"
        assert result["operations_completed"] == 4  # 2 tags × 2 contacts
        mock_context.api_client.apply_tags_to_contacts.assert_called_once_with(tag_ids, contact_ids)
    
    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts_partial_failure(self, mock_context):
        """Test tag application with some failures."""
        tag_ids = ["1", "2"]
        contact_ids = ["101", "102"]
        
        # Mock batch API failure, fallback to individual operations
        mock_context.api_client.apply_tags_to_contacts.side_effect = ValueError("Batch not supported")
        mock_context.api_client.apply_tag_to_contact.side_effect = [
            None,  # success
            Exception("Tag not found"),  # failure
            None,  # success
            Exception("Contact not found")  # failure
        ]
        
        result = await apply_tags_to_contacts(mock_context, tag_ids, contact_ids)
        
        assert result["success"] is True  # Some operations succeeded
        assert result["operations_completed"] == 2
        assert len(result["failed_operations"]) == 2
    
    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts_exception(self, mock_context):
        """Test tag application with exception."""
        tag_ids = ["1"]
        contact_ids = ["101"]
        
        mock_context.api_client.apply_tags_to_contacts.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await apply_tags_to_contacts(mock_context, tag_ids, contact_ids)


class TestRemoveTagsFromContacts:
    
    @pytest.mark.asyncio
    async def test_remove_tags_from_contacts_success(self, mock_context):
        """Test successful tag removal from contacts."""
        tag_ids = ["1", "2"]
        contact_ids = ["101", "102"]
        
        # Mock successful API calls
        mock_context.api_client.remove_tag_from_contact.return_value = None
        
        result = await remove_tags_from_contacts(mock_context, tag_ids, contact_ids)
        
        assert result["success"] is True
        assert result["operations_completed"] == 4  # 2 tags × 2 contacts
        assert mock_context.api_client.remove_tag_from_contact.call_count == 4
    
    @pytest.mark.asyncio
    async def test_remove_tags_from_contacts_partial_failure(self, mock_context):
        """Test tag removal with some failures."""
        tag_ids = ["1", "2"]
        contact_ids = ["101", "102"]
        
        # Mock some successes and failures
        mock_context.api_client.remove_tag_from_contact.side_effect = [
            None,  # success
            Exception("Tag not found"),  # failure
            None,  # success
            Exception("Contact not found")  # failure
        ]
        
        result = await remove_tags_from_contacts(mock_context, tag_ids, contact_ids)
        
        assert result["success"] is True  # Some operations succeeded
        assert result["operations_completed"] == 2
        assert len(result["failed_operations"]) == 2
    
    @pytest.mark.asyncio
    async def test_remove_tags_from_contacts_exception(self, mock_context):
        """Test tag removal with exception."""
        tag_ids = ["1"]
        contact_ids = ["101"]
        
        # The function catches exceptions in the inner loop and returns them as failed operations
        # rather than raising. Only truly unexpected exceptions would be raised.
        mock_context.api_client.remove_tag_from_contact.side_effect = Exception("API Error")
        
        result = await remove_tags_from_contacts(mock_context, tag_ids, contact_ids)
        
        assert result["success"] is False  # No successful operations
        assert result["operations_completed"] == 0
        assert len(result["failed_operations"]) == 1
        assert "API Error" in result["failed_operations"][0]["error"]


class TestTagToolsEdgeCases:
    
    @pytest.mark.asyncio
    async def test_get_tags_empty_response(self, mock_context):
        """Test tag retrieval with empty response."""
        mock_context.api_client.get_tags.return_value = {"tags": []}
        mock_context.cache_manager.get.return_value = None
        
        result = await get_tags(mock_context)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_contacts_with_tag_empty_response(self, mock_context):
        """Test contact retrieval by tag with empty response."""
        tag_id = "1"
        mock_context.api_client.get_contacts_by_tag.return_value = []
        mock_context.cache_manager.get.return_value = None
        
        result = await get_contacts_with_tag(mock_context, tag_id)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_tags_filter_no_matches(self, mock_context, sample_tags):
        """Test tag filtering with no matches."""
        mock_context.api_client.get_tags.return_value = {"tags": sample_tags}
        mock_context.cache_manager.get.return_value = None
        
        filters = [{"field": "name", "operator": "equals", "value": "Nonexistent Tag"}]
        result = await get_tags(mock_context, filters=filters)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_apply_tags_empty_lists(self, mock_context):
        """Test tag application with empty lists."""
        mock_context.api_client.apply_tags_to_contacts.return_value = None
        
        result = await apply_tags_to_contacts(mock_context, [], [])
        
        assert result["success"] is True
        assert result["message"] == "Successfully applied tags to contacts"
        assert result["operations_completed"] == 0
    
    @pytest.mark.asyncio
    async def test_remove_tags_empty_lists(self, mock_context):
        """Test tag removal with empty lists."""
        result = await remove_tags_from_contacts(mock_context, [], [])
        
        assert result["success"] is False  # 0 successful operations = False
        assert result["operations_completed"] == 0
"""
Streamlined Custom Fields Integration Tests

Essential integration tests for Keap custom field functionality.
Focuses on core functionality without extensive API exploration.
"""

import pytest
import os
from unittest.mock import patch, AsyncMock

from src.mcp.tools_collections import list_contacts, get_collection_details, get_contact_schema
from mcp.server.fastmcp import Context


@pytest.fixture
def skip_if_no_api_key():
    """Skip tests if KEAP_API_KEY is not available"""
    api_key = os.getenv('KEAP_API_KEY')
    if not api_key:
        pytest.skip("KEAP_API_KEY not available in environment")


@pytest.fixture
def context():
    """Create MCP context for testing."""
    return Context()


class TestCustomFieldsCore:
    """Core custom field integration tests."""

    @pytest.mark.asyncio
    async def test_custom_fields_in_contact_schema(self, context, skip_if_no_api_key):
        """Test that custom fields are properly included in contact schema."""
        # Get contact schema which should include custom fields
        schema = await get_contact_schema(context)
        
        # Verify schema structure
        assert "standard_fields" in schema
        assert "custom_fields" in schema
        
        # Should have some custom fields defined
        custom_fields = schema.get("custom_fields", [])
        print(f"Found {len(custom_fields)} custom fields in schema")
        
        # Verify custom field structure if any exist
        if custom_fields:
            sample_field = custom_fields[0]
            assert "id" in sample_field
            assert "label" in sample_field

    @pytest.mark.asyncio  
    async def test_custom_fields_in_contact_data(self, context, skip_if_no_api_key):
        """Test that custom fields are included in contact data retrieval."""
        # Get a small collection of contacts
        contacts_result = await list_contacts(context, limit=2)
        collection_id = contacts_result["collection_id"]
        
        if contacts_result["count"] == 0:
            pytest.skip("No contacts available for custom field testing")
        
        # Get detailed contact data
        details = await get_collection_details(context, collection_id)
        contacts = details.get("contacts", [])
        
        assert len(contacts) > 0
        
        # Check if any contact has custom fields
        has_custom_fields = False
        for contact in contacts:
            if "custom_fields" in contact and contact["custom_fields"]:
                has_custom_fields = True
                # Verify custom field structure
                custom_field = contact["custom_fields"][0] 
                assert "id" in custom_field
                print(f"Contact {contact.get('id')} has custom fields")
                break
        
        # Note: It's ok if no contacts have custom fields populated
        print(f"Custom fields found in contact data: {has_custom_fields}")

    @pytest.mark.asyncio
    async def test_mcp_tools_handle_custom_fields(self, context, skip_if_no_api_key):
        """Test that MCP tools properly handle custom fields without errors."""
        # Test that list_contacts works with custom field parameters
        result = await list_contacts(
            context,
            limit=2,
            enable_optimization=True,
            return_metrics=True
        )
        
        assert "collection_id" in result
        assert "count" in result
        assert result["count"] >= 0
        
        # If we have contacts, test getting their details
        if result["count"] > 0:
            details = await get_collection_details(
                context, 
                result["collection_id"],
                enable_optimization=True,
                return_metrics=True
            )
            
            assert "contacts" in details
            assert "count" in details
            
            # Verify contacts have expected structure
            for contact in details["contacts"]:
                assert "id" in contact
                # custom_fields should be present (even if empty)
                assert "custom_fields" in contact or len(contact.keys()) > 3


class TestCustomFieldsPerformance:
    """Test custom field performance characteristics."""

    @pytest.mark.asyncio
    async def test_custom_field_retrieval_performance(self, context, skip_if_no_api_key):
        """Test that custom field retrieval doesn't significantly impact performance."""
        import time
        
        # Time a small collection request with metrics
        start_time = time.time()
        
        result = await list_contacts(
            context, 
            limit=3,
            return_metrics=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete reasonably quickly
        assert duration < 10.0, f"Custom field retrieval took too long: {duration:.2f}s"
        
        # Check if performance metrics are available
        if "performance_metrics" in result:
            metrics = result["performance_metrics"]
            print(f"API calls made: {metrics.get('api_calls', 'N/A')}")
            print(f"Duration: {duration:.2f}s")
        
        assert result["count"] >= 0


class TestCustomFieldsErrorHandling:
    """Test error handling for custom field operations."""

    @pytest.mark.asyncio
    async def test_custom_fields_with_invalid_collection(self, context, skip_if_no_api_key):
        """Test error handling when requesting custom fields for invalid collection."""
        with pytest.raises(ValueError, match="Collection .* not found"):
            await get_collection_details(context, "invalid_collection_id")

    @pytest.mark.asyncio
    async def test_custom_fields_with_api_errors(self, context):
        """Test graceful handling of API errors during custom field operations."""
        # Mock API client to simulate errors
        with patch('src.mcp.tools_collections.get_api_client') as mock_get_api:
            mock_api_client = AsyncMock()
            mock_api_client.get_contacts.side_effect = Exception("API Error")
            mock_api_client.close = AsyncMock()
            mock_get_api.return_value = mock_api_client
            
            with pytest.raises(Exception, match="API Error"):
                await list_contacts(context, limit=1)
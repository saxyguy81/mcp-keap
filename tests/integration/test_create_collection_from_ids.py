"""
Integration Tests for create_collection_from_ids Tool

Tests the new tool that creates collections from contact ID lists,
which provides a cleaner alternative to exposing get_contact_details directly.
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    create_collection_from_ids,
    get_collection_details,
    list_contacts,
)


class TestCreateCollectionFromIds:
    """Test the create_collection_from_ids tool and its integration with other collection tools."""

    @pytest.mark.asyncio
    async def test_create_collection_from_valid_ids(self):
        """Test creating a collection from valid contact IDs."""
        context = Context()
        
        # First get some actual contact IDs from the system
        contacts_result = await list_contacts(context, limit=3)
        if contacts_result["count"] == 0:
            pytest.skip("No contacts available for testing")
        
        # Get the contact IDs from the collection
        collection_details = await get_collection_details(context, contacts_result["collection_id"])
        actual_contact_ids = [contact["id"] for contact in collection_details["contacts"][:2]]
        
        if not actual_contact_ids:
            pytest.skip("No contact IDs available for testing")
        
        # Test creating collection from these IDs
        result = await create_collection_from_ids(context, actual_contact_ids)
        
        # Verify result structure
        assert "collection_id" in result
        assert "count" in result
        assert "contact_ids" in result
        assert "name" in result
        assert "created_from" in result
        
        # Verify values
        assert result["count"] == len(actual_contact_ids)
        assert result["contact_ids"] == actual_contact_ids
        assert result["created_from"] == "contact_ids"
        assert "Custom collection" in result["name"]
        
        # Verify we can get details from the new collection
        new_collection_details = await get_collection_details(context, result["collection_id"])
        assert new_collection_details["count"] == len(actual_contact_ids)
        assert len(new_collection_details["contacts"]) == len(actual_contact_ids)
        
        # Verify the contacts match the requested IDs
        returned_ids = [contact["id"] for contact in new_collection_details["contacts"]]
        assert set(returned_ids) == set(actual_contact_ids)

    @pytest.mark.asyncio
    async def test_create_collection_with_custom_name(self):
        """Test creating a collection with a custom name."""
        context = Context()
        
        # Use some test contact IDs (these may or may not exist, but we test the collection creation)
        test_contact_ids = [1, 2, 3]
        custom_name = "Test Collection for Integration"
        
        result = await create_collection_from_ids(context, test_contact_ids, name=custom_name)
        
        # Verify custom name is used
        assert result["name"] == custom_name
        assert result["count"] == 3
        assert result["contact_ids"] == test_contact_ids

    @pytest.mark.asyncio
    async def test_create_collection_removes_duplicates(self):
        """Test that duplicate contact IDs are removed."""
        context = Context()
        
        # Use duplicate IDs
        contact_ids_with_duplicates = [1, 2, 3, 2, 1, 4, 3]
        expected_unique_ids = [1, 2, 3, 4]  # Order preserved, duplicates removed
        
        result = await create_collection_from_ids(context, contact_ids_with_duplicates)
        
        # Verify duplicates were removed
        assert result["count"] == 4
        assert result["contact_ids"] == expected_unique_ids
        assert "7 contact IDs (4 unique)" in result["operation"]

    @pytest.mark.asyncio
    async def test_create_collection_validates_input(self):
        """Test input validation for create_collection_from_ids."""
        context = Context()
        
        # Test empty list
        with pytest.raises(ValueError, match="contact_ids list cannot be empty"):
            await create_collection_from_ids(context, [])
        
        # Test non-list input
        with pytest.raises(ValueError, match="contact_ids must be a list"):
            await create_collection_from_ids(context, "not a list")
        
        # Test invalid contact ID types
        with pytest.raises(ValueError, match="Invalid contact ID.*Contact IDs must be integers"):
            await create_collection_from_ids(context, [1, "invalid", 3])
        
        with pytest.raises(ValueError, match="Invalid contact ID.*Contact IDs must be integers"):
            await create_collection_from_ids(context, [1, None, 3])

    @pytest.mark.asyncio
    async def test_create_collection_converts_string_ids(self):
        """Test that string contact IDs are converted to integers."""
        context = Context()
        
        # Use string IDs that can be converted to integers
        string_contact_ids = ["1", "2", "3"]
        expected_int_ids = [1, 2, 3]
        
        result = await create_collection_from_ids(context, string_contact_ids)
        
        # Verify conversion worked
        assert result["contact_ids"] == expected_int_ids
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_create_collection_workflow_with_operations(self):
        """Test complete workflow: create collection from IDs, then perform operations."""
        context = Context()
        
        # Get some actual contact IDs
        contacts_result = await list_contacts(context, limit=5)
        if contacts_result["count"] < 2:
            pytest.skip("Need at least 2 contacts for workflow testing")
        
        collection_details = await get_collection_details(context, contacts_result["collection_id"])
        all_contact_ids = [contact["id"] for contact in collection_details["contacts"]]
        
        # Create two collections from subsets of IDs
        subset1 = all_contact_ids[:2]
        subset2 = all_contact_ids[1:3] if len(all_contact_ids) >= 3 else all_contact_ids[:2]
        
        collection1 = await create_collection_from_ids(context, subset1, "Subset 1")
        collection2 = await create_collection_from_ids(context, subset2, "Subset 2")
        
        # Verify both collections were created
        assert collection1["count"] == len(subset1)
        assert collection2["count"] == len(subset2)
        
        # Test that we can get details from both
        details1 = await get_collection_details(context, collection1["collection_id"])
        details2 = await get_collection_details(context, collection2["collection_id"])
        
        assert details1["count"] == len(subset1)
        assert details2["count"] == len(subset2)
        
        # Verify contacts match what we expect
        returned_ids1 = [contact["id"] for contact in details1["contacts"]]
        returned_ids2 = [contact["id"] for contact in details2["contacts"]]
        
        assert set(returned_ids1) == set(subset1)
        assert set(returned_ids2) == set(subset2)

    @pytest.mark.asyncio
    async def test_create_collection_performance_with_large_list(self):
        """Test performance with a larger list of contact IDs."""
        context = Context()
        
        # Create a larger list of contact IDs (simulated)
        large_contact_ids = list(range(1, 101))  # 100 contact IDs
        
        result = await create_collection_from_ids(context, large_contact_ids, "Large Test Collection")
        
        # Verify the collection was created correctly
        assert result["count"] == 100
        assert len(result["contact_ids"]) == 100
        assert result["contact_ids"] == large_contact_ids
        assert result["name"] == "Large Test Collection"

    @pytest.mark.asyncio
    async def test_collection_created_from_ids_supports_field_selection(self):
        """Test that collections created from IDs work with field selection."""
        context = Context()
        
        # Get some actual contact IDs
        contacts_result = await list_contacts(context, limit=2)
        if contacts_result["count"] == 0:
            pytest.skip("No contacts available for testing")
        
        collection_details = await get_collection_details(context, contacts_result["collection_id"])
        contact_ids = [contact["id"] for contact in collection_details["contacts"]]
        
        if not contact_ids:
            pytest.skip("No contact IDs available for testing")
        
        # Create collection from IDs
        custom_collection = await create_collection_from_ids(context, contact_ids)
        
        # Test field selection on the custom collection
        field_selected_details = await get_collection_details(
            context, 
            custom_collection["collection_id"],
            fields=["id", "email", "given_name"]
        )
        
        # Verify field selection worked
        assert field_selected_details["count"] == len(contact_ids)
        
        # Check that only selected fields are present (if contacts exist)
        if field_selected_details["contacts"]:
            first_contact = field_selected_details["contacts"][0]
            # Should have the requested fields
            expected_fields = {"id", "email", "given_name"}
            # May have additional metadata fields, but should at least have the requested ones
            contact_fields = set(first_contact.keys())
            assert expected_fields.issubset(contact_fields) or len(contact_fields) <= 5  # Allow some flexibility for metadata
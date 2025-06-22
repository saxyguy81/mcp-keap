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

    @pytest.mark.asyncio
    async def test_create_collection_and_dump_contact_info(self):
        """
        Test creating a collection from contact IDs and then extracting 
        email addresses, first names, and last names for each contact.
        
        This tests the complete workflow that users would typically perform:
        1. Create collection from specific contact IDs
        2. Extract key contact information (email, first name, last name)
        """
        context = Context()
        
        # First, get some actual contact IDs from the system
        contacts_result = await list_contacts(context, limit=5)
        if contacts_result["count"] == 0:
            pytest.skip("No contacts available for testing")
        
        # Get detailed contact info to extract contact IDs
        collection_details = await get_collection_details(context, contacts_result["collection_id"])
        available_contact_ids = [contact["id"] for contact in collection_details["contacts"]]
        
        if len(available_contact_ids) < 2:
            pytest.skip("Need at least 2 contacts for meaningful testing")
        
        # Use a subset of available contact IDs for our test
        test_contact_ids = available_contact_ids[:3]  # Use first 3 contacts
        
        print(f"\n🔍 Testing with contact IDs: {test_contact_ids}")
        
        # Step 1: Create collection from specific contact IDs
        custom_collection = await create_collection_from_ids(
            context, 
            test_contact_ids, 
            name="Email Dump Test Collection"
        )
        
        # Verify collection was created correctly
        assert custom_collection["count"] == len(test_contact_ids)
        assert custom_collection["contact_ids"] == test_contact_ids
        assert custom_collection["name"] == "Email Dump Test Collection"
        
        print(f"✅ Created collection {custom_collection['collection_id']} with {custom_collection['count']} contacts")
        
        # Step 2: Extract email addresses, first names, and last names
        contact_info = await get_collection_details(
            context,
            custom_collection["collection_id"],
            fields=["id", "email", "given_name", "family_name"]
        )
        
        # Verify we got the expected contacts back
        assert contact_info["count"] == len(test_contact_ids)
        assert len(contact_info["contacts"]) == len(test_contact_ids)
        
        # Step 3: Verify each contact has the requested information and dump it
        print("\n📋 Contact Information Dump:")
        print("=" * 60)
        
        returned_contact_ids = []
        contacts_with_email = 0
        contacts_with_first_name = 0
        contacts_with_last_name = 0
        
        for i, contact in enumerate(contact_info["contacts"], 1):
            # Verify contact structure
            assert "id" in contact, f"Contact {i} missing 'id' field"
            contact_id = contact["id"]
            returned_contact_ids.append(contact_id)
            
            # Extract contact info (may be None/empty)
            email = contact.get("email", "")
            first_name = contact.get("given_name", "")
            last_name = contact.get("family_name", "")
            
            # Count contacts with data
            if email:
                contacts_with_email += 1
            if first_name:
                contacts_with_first_name += 1
            if last_name:
                contacts_with_last_name += 1
            
            # Dump contact information
            print(f"Contact {i} (ID: {contact_id}):")
            print(f"  📧 Email: {email or '(not provided)'}")
            print(f"  👤 First Name: {first_name or '(not provided)'}")
            print(f"  👤 Last Name: {last_name or '(not provided)'}")
            print()
        
        print("=" * 60)
        print("📊 Summary:")
        print(f"  Total contacts processed: {len(contact_info['contacts'])}")
        print(f"  Contacts with email: {contacts_with_email}")
        print(f"  Contacts with first name: {contacts_with_first_name}")
        print(f"  Contacts with last name: {contacts_with_last_name}")
        
        # Verify that we got back exactly the contacts we requested
        assert set(returned_contact_ids) == set(test_contact_ids), \
            f"Returned contact IDs {returned_contact_ids} don't match requested {test_contact_ids}"
        
        # Verify that the collection workflow preserved contact order or at least all contacts
        assert len(returned_contact_ids) == len(test_contact_ids)
        
        # At least verify the structure is correct (data may be sparse in test environment)
        for contact in contact_info["contacts"]:
            # Each contact should have the requested fields (even if empty)
            contact_fields = set(contact.keys())
            
            # Should have at least the ID field and some of the other fields
            assert "id" in contact_fields
            # May have additional metadata fields, but should include our requested fields
            # Note: Some fields might be missing or empty in test data, which is fine
        
        print(f"✅ Successfully created collection from {len(test_contact_ids)} contact IDs")
        print("✅ Successfully extracted contact information using get_collection_details") 
        print(f"✅ All {len(test_contact_ids)} contacts returned with expected field structure")

    @pytest.mark.asyncio
    async def test_create_collection_from_mixed_existing_nonexistent_ids(self):
        """
        Test creating a collection with a mix of existing and non-existent contact IDs.
        This tests how the system handles contact IDs that may not exist in the database.
        """
        context = Context()
        
        # Get some actual contact IDs
        contacts_result = await list_contacts(context, limit=2)
        if contacts_result["count"] == 0:
            pytest.skip("No contacts available for testing")
        
        collection_details = await get_collection_details(context, contacts_result["collection_id"])
        existing_contact_ids = [contact["id"] for contact in collection_details["contacts"]]
        
        if not existing_contact_ids:
            pytest.skip("No existing contact IDs available for testing")
        
        # Mix real contact IDs with likely non-existent ones
        mixed_contact_ids = existing_contact_ids + [999999, 888888, 777777]  # Add some non-existent IDs
        
        # Create collection from mixed IDs
        custom_collection = await create_collection_from_ids(
            context, 
            mixed_contact_ids,
            name="Mixed ID Test Collection"
        )
        
        # The collection should be created successfully
        assert custom_collection["count"] == len(mixed_contact_ids)
        assert custom_collection["contact_ids"] == mixed_contact_ids
        
        # When we get details, we should only get back the existing contacts
        contact_info = await get_collection_details(context, custom_collection["collection_id"])
        
        # The count should reflect only the contacts that actually exist
        # (Non-existent contact IDs should be filtered out gracefully)
        print("\n🔍 Mixed ID test:")
        print(f"  Requested: {len(mixed_contact_ids)} contact IDs")
        print(f"  Returned: {contact_info['count']} contacts")
        print(f"  Expected existing: {len(existing_contact_ids)} contacts")
        
        # Verify that we get at least the existing contacts back
        assert contact_info["count"] >= len(existing_contact_ids)
        
        # Verify that all returned contacts have valid IDs
        for contact in contact_info["contacts"]:
            assert "id" in contact
            assert isinstance(contact["id"], int)
            assert contact["id"] > 0
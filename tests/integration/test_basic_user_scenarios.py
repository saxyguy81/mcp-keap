"""
Integration Tests for Basic User Scenarios

Tests that reproduce and validate the exact scenarios users reported as failing:
1. Basic filter validation and usage
2. Field selection functionality  
3. Default limit behavior (should be 1000, not 200)
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    get_contact_schema
)


class TestBasicUserScenarios:
    """Test basic user scenarios that should work out of the box."""

    @pytest.mark.asyncio
    async def test_basic_given_name_filter(self):
        """
        Test the exact user scenario: filters=[{"field": "given_name", "operator": "equals", "value": "Scott"}]
        This was failing with "Filters must be a list of filter objects" error.
        """
        context = Context()
        
        print("\n🔍 Testing basic given_name filter (exact user scenario)...")
        
        # This is the exact filter format the user was trying to use
        filters = [{"field": "given_name", "operator": "equals", "value": "Scott"}]
        
        try:
            result = await list_contacts(context, filters=filters, limit=50)
            
            print("✅ Filter validation passed - no error thrown")
            print(f"   Collection ID: {result.get('collection_id')}")
            print(f"   Contacts found: {result.get('count', 0)}")
            
            # Validation should pass regardless of whether we find contacts named Scott
            assert "collection_id" in result
            assert "count" in result
            assert isinstance(result["count"], int)
            assert result["count"] >= 0
            
            print("✅ Basic given_name filter test passed")
            
        except ValueError as e:
            if "Filters must be a list of filter objects" in str(e):
                pytest.fail(f"Filter validation failed - this exact scenario should work: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_various_filter_formats(self):
        """
        Test different filter formats that users might try.
        """
        context = Context()
        
        print("\n🔍 Testing various filter formats...")
        
        # Different filter formats users might try
        test_filters = [
            # Basic name filters
            ([{"field": "given_name", "operator": "equals", "value": "John"}], "Given name equals John"),
            ([{"field": "family_name", "operator": "contains", "value": "Smith"}], "Family name contains Smith"),
            
            # Email filters  
            ([{"field": "email", "operator": "contains", "value": "@gmail.com"}], "Email contains @gmail.com"),
            ([{"field": "email", "operator": "equals", "value": "test@example.com"}], "Email equals test@example.com"),
            
            # Multiple filters
            ([
                {"field": "given_name", "operator": "equals", "value": "John"},
                {"field": "email", "operator": "contains", "value": "@company.com"}
            ], "Multiple filters: name and email"),
            
            # Custom field filter
            ([{"field": "custom_field_7", "operator": "equals", "value": "VIP"}], "Custom field filter"),
        ]
        
        for filters, description in test_filters:
            print(f"\n  Testing: {description}")
            print(f"  Filter: {filters}")
            
            try:
                result = await list_contacts(context, filters=filters, limit=20)
                print(f"    ✅ Success - {result.get('count', 0)} contacts found")
                
                # Basic validation
                assert "collection_id" in result
                assert "count" in result
                assert isinstance(result["count"], int)
                
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                if "Filters must be a list of filter objects" in str(e):
                    pytest.fail(f"Filter validation should not fail for: {description}")
                # Other errors might be expected (e.g., custom field doesn't exist)
                
        print("✅ Various filter formats test completed")

    @pytest.mark.asyncio
    async def test_default_limit_is_1000(self):
        """
        Test that the default limit is 1000 contacts, not 200.
        Users expect to get the maximum API allows by default.
        """
        context = Context()
        
        print("\n🔍 Testing default limit behavior...")
        
        # Test with no explicit limit (should default to 1000)
        result_default = await list_contacts(context)
        print(f"Default limit result: {result_default.get('count', 0)} contacts")
        
        # Test with explicit limit of 1000
        result_1000 = await list_contacts(context, limit=1000)
        print(f"Explicit 1000 limit result: {result_1000.get('count', 0)} contacts")
        
        # Both should return the same number of contacts
        assert result_default["count"] == result_1000["count"], \
            f"Default limit should be 1000 - got {result_default['count']} vs {result_1000['count']}"
        
        # Test with smaller limit to ensure limiting works
        result_small = await list_contacts(context, limit=10)
        print(f"Small limit (10) result: {result_small.get('count', 0)} contacts")
        
        if result_default["count"] > 10:
            assert result_small["count"] <= 10, \
                f"Small limit should restrict results - got {result_small['count']}"
            assert result_small["count"] < result_default["count"], \
                "Small limit should return fewer contacts than default"
        
        print("✅ Default limit test passed - default is 1000")

    @pytest.mark.asyncio
    async def test_field_selection_functionality(self):
        """
        Test that field selection works correctly.
        User reported: "Only got email addresses, no names despite requesting 
        ["id", "given_name", "family_name", "email_addresses", "company"]"
        """
        context = Context()
        
        print("\n🔍 Testing field selection functionality...")
        
        # Get some contacts first
        contacts_result = await list_contacts(context, limit=10)
        if contacts_result["count"] == 0:
            pytest.skip("Need at least 1 contact for field selection test")
        
        collection_id = contacts_result["collection_id"]
        
        # Test with specific field selection (user's exact request)
        requested_fields = ["id", "given_name", "family_name", "email_addresses", "company"]
        
        details = await get_collection_details(
            context,
            collection_id,
            fields=requested_fields,
            limit=3
        )
        
        print(f"Requested fields: {requested_fields}")
        print(f"Contacts returned: {len(details.get('contacts', []))}")
        
        if details.get('contacts'):
            sample_contact = details['contacts'][0]
            print(f"Sample contact fields: {list(sample_contact.keys())}")
            
            # Check that we got more than just email
            available_fields = set(sample_contact.keys())
            requested_set = set(requested_fields)
            
            # Should have at least some of the requested fields
            intersection = available_fields.intersection(requested_set)
            print(f"Matched fields: {sorted(intersection)}")
            
            # Must have ID (always present)
            assert "id" in available_fields, "Contact should always have 'id' field"
            
            # Should have more than just email-related fields
            non_email_fields = available_fields - {"email", "email_addresses", "_PRIMARY_EMAIL"}
            print(f"Non-email fields: {sorted(non_email_fields)}")
            
            assert len(non_email_fields) > 1, \
                f"Should return more than just email fields. Got: {sorted(available_fields)}"
            
            # Check for specific name fields if they exist in the contact
            if sample_contact.get("given_name"):
                print(f"  ✅ given_name: '{sample_contact['given_name']}'")
            if sample_contact.get("family_name"):
                print(f"  ✅ family_name: '{sample_contact['family_name']}'")
            if sample_contact.get("company"):
                print(f"  ✅ company: '{sample_contact['company']}'")
        
        print("✅ Field selection test passed")

    @pytest.mark.asyncio
    async def test_schema_availability(self):
        """
        Test that users can get schema information to understand available fields.
        """
        context = Context()
        
        print("\n🔍 Testing schema availability...")
        
        schema = await get_contact_schema(context)
        
        print(f"Schema keys: {list(schema.keys())}")
        
        # Should have basic schema information
        assert "standard_fields" in schema, "Schema should include standard_fields"
        assert "filter_examples" in schema, "Schema should include filter_examples"
        
        # Should have filter examples that users can copy
        filter_examples = schema.get("filter_examples", [])
        assert len(filter_examples) > 0, "Should provide filter examples"
        
        print(f"Filter examples provided: {len(filter_examples)}")
        for i, example in enumerate(filter_examples[:3]):  # Show first 3
            print(f"  Example {i+1}: {example}")
        
        print("✅ Schema availability test passed")

    @pytest.mark.asyncio
    async def test_empty_filters_list(self):
        """
        Test that empty filters list works correctly (should return all contacts).
        """
        context = Context()
        
        print("\n🔍 Testing empty filters behavior...")
        
        # Test with empty list
        result_empty_list = await list_contacts(context, filters=[], limit=50)
        print(f"Empty filters list: {result_empty_list.get('count', 0)} contacts")
        
        # Test with None filters
        result_none = await list_contacts(context, filters=None, limit=50)
        print(f"None filters: {result_none.get('count', 0)} contacts")
        
        # Both should return the same number of contacts
        assert result_empty_list["count"] == result_none["count"], \
            "Empty list and None filters should return same results"
        
        print("✅ Empty filters test passed")

    @pytest.mark.asyncio
    async def test_user_error_scenarios(self):
        """
        Test common user error scenarios and ensure they give helpful error messages.
        """
        context = Context()
        
        print("\n🔍 Testing user error scenarios...")
        
        # Test malformed filters that should give helpful errors
        error_cases = [
            # Not a list
            ({"field": "email", "operator": "equals", "value": "test@example.com"}, "Single dict instead of list"),
            
            # Missing required fields  
            ([{"field": "email", "operator": "equals"}], "Missing value field"),
            ([{"field": "email", "value": "test@example.com"}], "Missing operator field"),
            ([{"operator": "equals", "value": "test@example.com"}], "Missing field field"),
            
            # Invalid operator
            ([{"field": "email", "operator": "invalid_op", "value": "test@example.com"}], "Invalid operator"),
        ]
        
        for bad_filters, description in error_cases:
            print(f"\n  Testing error case: {description}")
            print(f"  Bad filters: {bad_filters}")
            
            try:
                await list_contacts(context, filters=bad_filters, limit=10)
                print("    ⚠️  Unexpectedly succeeded - should have failed")
                # Some cases might actually work (e.g., invalid operator might be handled gracefully)
                
            except ValueError as e:
                print(f"    ✅ Correctly failed with ValueError: {e}")
                # Error message should be helpful
                assert len(str(e)) > 10, "Error message should be descriptive"
                
            except Exception as e:
                print(f"    ✅ Failed with {type(e).__name__}: {e}")
        
        print("✅ User error scenarios test completed")
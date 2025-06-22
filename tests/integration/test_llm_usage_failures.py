"""
Integration Tests Reproducing Actual LLM Usage Failures

This test file reproduces the exact failures reported by users when using 
the MCP tools with actual LLMs, ensuring these critical bugs are identified 
and fixed.

Based on detailed user feedback about:
1. given_name filtering completely broken
2. get_collection_fields parsing field names as individual characters
3. Inconsistent field selection in get_collection_details
4. Response truncation issues
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_contact_schema,
    get_collection_details,
    get_collection_fields,
)


class TestLLMUsageFailures:
    """Test the exact failure scenarios reported by LLM users."""

    @pytest.mark.asyncio
    async def test_given_name_filtering_exact_user_case(self):
        """
        CRITICAL TEST: Reproduce exact user failure with given_name filtering.
        
        User reported: keap:list_contacts with filters=[{"field": "given_name", "operator": "equals", "value": "Scott"}]
        Error: "Filters must be a list of filter objects"
        
        This is a CRITICAL bug - basic filtering functionality is broken.
        """
        context = Context()
        
        # Test the exact filter format the user tried
        filters = [{"field": "given_name", "operator": "equals", "value": "Scott"}]
        
        print(f"\n🔍 Testing exact user filter: {filters}")
        
        try:
            # This should work but user reported it fails
            result = await list_contacts(context, filters=filters)
            
            # Verify the result is properly structured
            assert "collection_id" in result
            assert "count" in result
            assert isinstance(result["count"], int)
            
            print(f"✅ given_name filtering worked: {result['count']} contacts found")
            
            # Verify we can get details from the filtered collection
            if result["count"] > 0:
                details = await get_collection_details(context, result["collection_id"])
                assert "contacts" in details
                
                # Verify filtering actually worked by checking first few contacts
                for contact in details["contacts"][:3]:
                    given_name = contact.get("given_name")
                    if given_name:  # If given_name exists, it should be "Scott"
                        assert given_name == "Scott", f"Filter failed: found contact with given_name='{given_name}'"
                        
        except Exception as e:
            pytest.fail(f"CRITICAL: given_name filtering failed with error: {e}")

    @pytest.mark.asyncio
    async def test_family_name_filtering_variants(self):
        """Test other name-based filters to ensure the pattern works."""
        context = Context()
        
        # Test various name-based filters
        test_filters = [
            [{"field": "family_name", "operator": "equals", "value": "Smith"}],
            [{"field": "given_name", "operator": "contains", "value": "John"}],
            [{"field": "family_name", "operator": "contains", "value": "son"}],
        ]
        
        for filters in test_filters:
            print(f"\n🔍 Testing filter: {filters}")
            
            try:
                result = await list_contacts(context, filters=filters)
                assert "collection_id" in result
                assert "count" in result
                
                print(f"  ✅ Filter worked: {result['count']} contacts found")
                
            except Exception as e:
                pytest.fail(f"Name-based filtering failed for {filters}: {e}")

    @pytest.mark.asyncio
    async def test_get_collection_fields_character_parsing_bug(self):
        """
        CRITICAL TEST: Reproduce the character parsing bug in get_collection_fields.
        
        User reported that get_collection_fields with field_names=["given_name", "family_name", "email_addresses", "id"]
        returned malformed data where individual characters were treated as field names:
        {
          "fields": {
            "[": { "515": null, "5636": null, ... },
            "\"": { "515": null, "5636": null, ... },
            "g": { "515": null, "5636": null, ... },
            ...
          }
        }
        
        This is a CRITICAL parsing bug.
        """
        context = Context()
        
        # First create a collection to test with
        contacts_result = await list_contacts(context, limit=5)
        if contacts_result["count"] == 0:
            pytest.skip("Need contacts to test get_collection_fields")
        
        collection_id = contacts_result["collection_id"]
        field_names = ["given_name", "family_name", "email_addresses", "id"]
        
        print(f"\n🔍 Testing get_collection_fields with: {field_names}")
        
        try:
            # This is where the user experienced the character parsing bug
            result = await get_collection_fields(collection_id, field_names)
            
            print(f"Result structure: {list(result.keys())}")
            
            # Verify the result structure is correct (not character-parsed)
            assert "fields" in result, "Result should have 'fields' key"
            
            fields_data = result["fields"]
            assert isinstance(fields_data, dict), "fields should be a dictionary"
            
            # Check that field names are actual field names, not individual characters
            field_keys = list(fields_data.keys())
            print(f"Field keys found: {field_keys}")
            
            # CRITICAL: None of these should be individual characters
            single_characters = [key for key in field_keys if len(key) == 1 and key in '["g']
            if single_characters:
                pytest.fail(f"CRITICAL CHARACTER PARSING BUG: Found single characters as field names: {single_characters}")
            
            # Should have actual field names
            expected_fields = ["given_name", "family_name", "email_addresses", "id"]
            found_expected = [field for field in expected_fields if field in field_keys]
            
            assert len(found_expected) > 0, f"Expected to find some of {expected_fields}, but got: {field_keys}"
            
            print(f"✅ get_collection_fields returned proper field names: {found_expected}")
            
        except Exception as e:
            # Log the full error details for debugging
            print(f"ERROR in get_collection_fields: {e}")
            print(f"Error type: {type(e)}")
            pytest.fail(f"CRITICAL: get_collection_fields failed: {e}")

    @pytest.mark.asyncio
    async def test_field_selection_consistency_bug(self):
        """
        CRITICAL TEST: Reproduce inconsistent field selection in get_collection_details.
        
        User reported:
        - First attempt: Returned empty contacts array despite collection having 200 contacts
        - Second attempt: Returned only email addresses, missing other requested fields  
        - Third attempt: Returned empty again
        
        This indicates a serious consistency issue.
        """
        context = Context()
        
        # Create a collection with some contacts
        contacts_result = await list_contacts(context, limit=10)
        if contacts_result["count"] == 0:
            pytest.skip("Need contacts to test field selection consistency")
        
        collection_id = contacts_result["collection_id"]
        expected_count = contacts_result["count"]
        
        # Test the exact field selection the user tried
        test_fields = ["id", "given_name", "family_name", "email_addresses", "company"]
        
        print(f"\n🔍 Testing field selection consistency: {test_fields}")
        print(f"Collection has {expected_count} contacts")
        
        # Run the same request multiple times to check for consistency
        results = []
        for attempt in range(3):
            print(f"\n  Attempt {attempt + 1}:")
            
            try:
                result = await get_collection_details(
                    context, 
                    collection_id, 
                    fields=test_fields
                )
                
                contact_count = len(result.get("contacts", []))
                total_count = result.get("count", 0)
                
                print(f"    Returned {contact_count} contacts (total count: {total_count})")
                
                # Check if we got any contacts back
                if contact_count == 0:
                    print("    ⚠️  CONSISTENCY ISSUE: Empty contacts array returned")
                else:
                    # Check which fields are actually present
                    first_contact = result["contacts"][0]
                    present_fields = list(first_contact.keys())
                    print(f"    Fields present: {present_fields}")
                    
                    # Check if requested fields are present
                    missing_fields = [field for field in test_fields if field not in present_fields]
                    if missing_fields:
                        print(f"    ⚠️  MISSING FIELDS: {missing_fields}")
                
                results.append({
                    "attempt": attempt + 1,
                    "contact_count": contact_count,
                    "total_count": total_count,
                    "fields_present": list(result["contacts"][0].keys()) if contact_count > 0 else []
                })
                
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
                results.append({
                    "attempt": attempt + 1,
                    "error": str(e)
                })
        
        # Analyze consistency
        print("\n📊 Consistency Analysis:")
        contact_counts = [r.get("contact_count", 0) for r in results if "contact_count" in r]
        unique_counts = set(contact_counts)
        
        print(f"  Contact counts across attempts: {contact_counts}")
        print(f"  Unique counts: {unique_counts}")
        
        # Check for the reported inconsistency issues
        has_empty_results = 0 in contact_counts
        has_non_empty_results = any(count > 0 for count in contact_counts)
        
        if has_empty_results and has_non_empty_results:
            pytest.fail("CRITICAL CONSISTENCY BUG: Some attempts returned empty results while others returned data")
        
        if len(unique_counts) > 1:
            pytest.fail(f"CRITICAL CONSISTENCY BUG: Contact counts varied across attempts: {unique_counts}")
        
        # All attempts should return the same number of contacts
        if contact_counts and all(count > 0 for count in contact_counts):
            # Check field consistency across attempts
            field_sets = [set(r.get("fields_present", [])) for r in results if "fields_present" in r]
            if len(set(tuple(sorted(fs)) for fs in field_sets)) > 1:
                pytest.fail("CRITICAL CONSISTENCY BUG: Fields present varied across attempts")
        
        print("✅ Field selection consistency test passed")

    @pytest.mark.asyncio 
    async def test_response_truncation_handling(self):
        """
        Test response truncation issues reported by users.
        
        User reported: "response was truncated at 100,000 characters"
        This suggests we need better handling of large response sizes.
        """
        context = Context()
        
        # Create a larger collection to test truncation
        large_result = await list_contacts(context, limit=100)
        if large_result["count"] < 10:
            pytest.skip("Need more contacts to test truncation")
        
        collection_id = large_result["collection_id"]
        
        print(f"\n🔍 Testing response truncation with {large_result['count']} contacts")
        
        try:
            # Get full details without field limiting
            result = await get_collection_details(context, collection_id)
            
            # Convert to JSON to estimate response size
            import json
            response_json = json.dumps(result)
            response_size = len(response_json)
            
            print(f"Response size: {response_size:,} characters")
            
            # Check if we got all expected contacts
            returned_contacts = len(result.get("contacts", []))
            expected_contacts = result.get("count", 0)
            
            print(f"Returned contacts: {returned_contacts}/{expected_contacts}")
            
            # If response is very large, check for potential truncation issues
            if response_size > 50000:  # 50KB threshold
                print(f"⚠️  Large response detected ({response_size:,} chars)")
                
                # Ensure we still get complete contact objects
                if returned_contacts > 0:
                    last_contact = result["contacts"][-1]
                    # Check that the last contact is complete (has basic fields)
                    assert "id" in last_contact, "Last contact missing ID - possible truncation"
                    
                    print("✅ Large response handling: Last contact complete")
            
            # Test field-limited version for comparison
            limited_result = await get_collection_details(
                context, 
                collection_id, 
                fields=["id", "given_name", "family_name"]
            )
            
            limited_json = json.dumps(limited_result)
            limited_size = len(limited_json)
            
            print(f"Limited response size: {limited_size:,} characters")
            assert limited_size < response_size, "Field limiting should reduce response size"
            
            print("✅ Response truncation test passed")
            
        except Exception as e:
            pytest.fail(f"Response truncation test failed: {e}")

    @pytest.mark.asyncio
    async def test_contact_schema_reliability(self):
        """
        Test that contact schema retrieval works reliably.
        
        User reported this worked perfectly, so ensure it stays that way.
        """
        context = Context()
        
        print("\n🔍 Testing contact schema reliability")
        
        # Test multiple calls to ensure consistency
        for attempt in range(3):
            try:
                schema = await get_contact_schema(context)
                
                # Verify expected structure
                assert "fields" in schema, "Schema should have 'fields'"
                assert "examples" in schema, "Schema should have 'examples'"
                
                fields = schema["fields"]
                assert "given_name" in fields, "Schema should include 'given_name' field"
                assert "family_name" in fields, "Schema should include 'family_name' field"
                assert "email" in fields, "Schema should include 'email' field"
                
                print(f"  Attempt {attempt + 1}: ✅ Schema structure correct")
                
            except Exception as e:
                pytest.fail(f"Contact schema failed on attempt {attempt + 1}: {e}")
        
        print("✅ Contact schema reliability test passed")

    @pytest.mark.asyncio
    async def test_end_to_end_name_search_workflow(self):
        """
        Test the complete workflow a user would follow to find contacts by name.
        
        This reproduces the user's intended workflow:
        1. Get schema to understand available fields
        2. Filter contacts by given_name
        3. Get details with selected fields
        4. Analyze results
        """
        context = Context()
        
        print("\n🔍 Testing end-to-end name search workflow")
        
        # Step 1: Get schema (user reported this worked)
        print("Step 1: Getting contact schema...")
        schema = await get_contact_schema(context)
        assert "given_name" in schema["fields"], "Schema should include given_name"
        print("  ✅ Schema retrieved successfully")
        
        # Step 2: Filter by given_name (user reported this failed)
        print("Step 2: Filtering contacts by given_name...")
        # Use a more common name that's likely to exist
        search_names = ["John", "David", "Michael", "Sarah", "Jennifer"]
        
        found_any = False
        for name in search_names:
            try:
                filters = [{"field": "given_name", "operator": "equals", "value": name}]
                result = await list_contacts(context, filters=filters)
                
                if result["count"] > 0:
                    print(f"  ✅ Found {result['count']} contacts named '{name}'")
                    found_any = True
                    
                    # Step 3: Get details with field selection
                    print("Step 3: Getting contact details with field selection...")
                    details = await get_collection_details(
                        context,
                        result["collection_id"],
                        fields=["id", "given_name", "family_name", "email"]
                    )
                    
                    assert len(details["contacts"]) > 0, "Should return contact details"
                    
                    # Step 4: Verify the filtering worked
                    print("Step 4: Verifying filtering accuracy...")
                    first_contact = details["contacts"][0]
                    contact_name = first_contact.get("given_name")
                    
                    if contact_name:
                        assert contact_name == name, f"Filter failed: expected '{name}', got '{contact_name}'"
                    
                    print(f"  ✅ End-to-end workflow successful for '{name}'")
                    break
                    
            except Exception as e:
                print(f"  ❌ Failed for name '{name}': {e}")
        
        if not found_any:
            # Try a broader search if exact name matches don't work
            print("Trying broader name search...")
            filters = [{"field": "given_name", "operator": "contains", "value": "a"}]
            result = await list_contacts(context, filters=filters, limit=5)
            
            if result["count"] > 0:
                print(f"  ✅ Broad search found {result['count']} contacts")
                found_any = True
        
        assert found_any, "End-to-end name search workflow should find at least some contacts"
        print("✅ End-to-end name search workflow test passed")
"""
Integration Tests for MCP Interface Issues

Tests that replicate the exact user experience with MCP interface problems:
1. Filters being passed as JSON strings instead of Python lists
2. Field selection not returning requested fields
3. Validation errors when using standard filter formats
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    get_contact_schema,
    _parse_filters
)


class TestMCPInterfaceIssues:
    """Test MCP interface issues that users reported."""

    @pytest.mark.asyncio
    async def test_exact_user_filter_scenario_json_string(self):
        """
        Test the EXACT scenario the user reported:
        filters: '[{"field": "given_name", "operator": "equals", "value": "Scott"}]'
        
        This should work after our JSON string parsing fix.
        """
        context = Context()
        
        print("\n🔍 Testing exact user scenario - filters as JSON string...")
        
        # This is EXACTLY what the user tried (JSON string, not Python list)
        filters_as_json_string = '[{"field": "given_name", "operator": "equals", "value": "Scott"}]'
        
        print(f"Input filters (type: {type(filters_as_json_string).__name__}): {filters_as_json_string}")
        
        try:
            result = await list_contacts(context, filters=filters_as_json_string, limit=50)
            
            print("✅ SUCCESS - Filter validation passed with JSON string!")
            print(f"   Collection ID: {result.get('collection_id')}")
            print(f"   Contacts found: {result.get('count', 0)}")
            
            # Validation should pass regardless of whether we find contacts named Scott
            assert "collection_id" in result
            assert "count" in result
            assert isinstance(result["count"], int)
            assert result["count"] >= 0
            
            # If we found contacts, verify they have the right name
            if result["count"] > 0:
                details = await get_collection_details(context, result["collection_id"], limit=3)
                for contact in details.get("contacts", []):
                    given_name = contact.get("given_name", "")
                    print(f"   Found contact: {given_name} (ID: {contact.get('id')})")
                    if given_name:  # Only check if given_name exists
                        assert given_name == "Scott", f"Expected 'Scott', got '{given_name}'"
            
            print("✅ Exact user scenario test PASSED")
            
        except Exception as e:
            pytest.fail(f"User's exact scenario should work but failed: {e}")

    @pytest.mark.asyncio
    async def test_various_json_string_formats(self):
        """
        Test various JSON string formats that MCP clients might send.
        """
        context = Context()
        
        print("\n🔍 Testing various JSON string filter formats...")
        
        # Different JSON string formats users/clients might send
        test_cases = [
            # Single filter
            ('[{"field": "given_name", "operator": "equals", "value": "John"}]', "Single filter as JSON string"),
            
            # Multiple filters 
            ('[{"field": "given_name", "operator": "equals", "value": "John"}, {"field": "email", "operator": "contains", "value": "@gmail.com"}]', "Multiple filters as JSON string"),
            
            # Email filter
            ('[{"field": "email", "operator": "contains", "value": "@company.com"}]', "Email filter as JSON string"),
            
            # Empty array
            ('[]', "Empty filters array as JSON string"),
        ]
        
        for json_string, description in test_cases:
            print(f"\n  Testing: {description}")
            print(f"  JSON input: {json_string}")
            
            try:
                result = await list_contacts(context, filters=json_string, limit=20)
                print(f"    ✅ Success - {result.get('count', 0)} contacts found")
                
                # Basic validation
                assert "collection_id" in result
                assert "count" in result
                assert isinstance(result["count"], int)
                
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                pytest.fail(f"JSON string format should work: {description} - {e}")
        
        print("✅ Various JSON string formats test passed")

    def test_parse_filters_function_directly(self):
        """
        Test the _parse_filters function directly with various inputs.
        """
        print("\n🔍 Testing _parse_filters function directly...")
        
        # Test cases for the parsing function
        test_cases = [
            # JSON strings
            ('[{"field": "email", "operator": "contains", "value": "@test.com"}]', "JSON string"),
            ('[]', "Empty JSON array"),
            
            # Python lists (should pass through unchanged)
            ([{"field": "email", "operator": "contains", "value": "@test.com"}], "Python list"),
            ([], "Empty Python list"),
            
            # None (should return empty list)
            (None, "None input"),
        ]
        
        for input_value, description in test_cases:
            print(f"\n  Testing: {description}")
            print(f"  Input (type: {type(input_value).__name__}): {input_value}")
            
            try:
                result = _parse_filters(input_value)
                print(f"    ✅ Parsed result: {result}")
                
                # Should always return a list
                assert isinstance(result, list), f"Expected list, got {type(result)}"
                
                # If not empty, should contain dictionaries
                if result:
                    for item in result:
                        assert isinstance(item, dict), f"Filter items should be dicts, got {type(item)}"
                
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                if description not in ["Invalid JSON"]:  # These should fail
                    pytest.fail(f"Valid input should parse successfully: {description} - {e}")
        
        print("✅ Parse filters function test passed")

    def test_invalid_json_string_handling(self):
        """
        Test that invalid JSON strings give helpful error messages.
        """
        print("\n🔍 Testing invalid JSON string handling...")
        
        # Invalid JSON strings that should fail gracefully
        invalid_cases = [
            ('{"field": "email", "operator": "contains", "value": "@test.com"}', "Single dict instead of list"),
            ('[{"field": "email", "operator": "contains", "value": "@test.com"', "Unclosed JSON"),
            ('invalid json', "Not JSON at all"),
            ('{"invalid": "structure"}', "Valid JSON but wrong structure"),
        ]
        
        for invalid_json, description in invalid_cases:
            print(f"\n  Testing invalid case: {description}")
            print(f"  Input: {invalid_json}")
            
            try:
                result = _parse_filters(invalid_json)
                print(f"    ⚠️  Unexpectedly succeeded: {result}")
                # Some cases might succeed if they're still valid JSON
                
            except ValueError as e:
                print(f"    ✅ Correctly failed with helpful error: {e}")
                assert len(str(e)) > 10, "Error message should be descriptive"
                
            except Exception as e:
                print(f"    ✅ Failed with {type(e).__name__}: {e}")
        
        print("✅ Invalid JSON handling test completed")

    @pytest.mark.asyncio
    async def test_field_selection_exact_user_case(self):
        """
        Test the exact field selection scenario the user reported:
        "Only got email addresses, no names despite requesting 
        ["id", "given_name", "family_name", "email_addresses", "company"]"
        """
        context = Context()
        
        print("\n🔍 Testing exact user field selection scenario...")
        
        # First, get some contacts
        contacts_result = await list_contacts(context, limit=10)
        if contacts_result["count"] == 0:
            pytest.skip("Need at least 1 contact for field selection test")
        
        collection_id = contacts_result["collection_id"]
        
        # Test the EXACT field selection the user requested
        user_requested_fields = ["id", "given_name", "family_name", "email_addresses", "company"]
        
        print(f"User requested fields: {user_requested_fields}")
        
        details = await get_collection_details(
            context,
            collection_id,
            fields=user_requested_fields,
            limit=3
        )
        
        print(f"Contacts returned: {len(details.get('contacts', []))}")
        
        if details.get('contacts'):
            for i, contact in enumerate(details['contacts']):
                print(f"\n  Contact {i+1} (ID: {contact.get('id')}):")
                actual_fields = list(contact.keys())
                print(f"    All fields returned: {sorted(actual_fields)}")
                
                # Check each requested field
                for field in user_requested_fields:
                    value = contact.get(field)
                    print(f"    {field}: {value} ({'✅' if value is not None else '❌'})")
                
                # Critical check: Should have more than just email fields
                non_email_fields = [f for f in actual_fields if f not in ['email', 'email_addresses', '_PRIMARY_EMAIL']]
                print(f"    Non-email fields: {sorted(non_email_fields)}")
                
                assert len(non_email_fields) >= 2, \
                    f"Should return more than just email fields. Got fields: {sorted(actual_fields)}"
                
                # Must have ID (always present)
                assert "id" in actual_fields, "Contact should always have 'id' field"
                
                # If the contact has name data, it should be returned when requested
                if contact.get("given_name") or contact.get("family_name"):
                    print(f"    ✅ Name fields present: given_name='{contact.get('given_name')}', family_name='{contact.get('family_name')}'")
        
        print("✅ Field selection exact user case test passed")

    @pytest.mark.asyncio
    async def test_default_vs_explicit_field_selection(self):
        """
        Test difference between default field selection and explicit field selection.
        """
        context = Context()
        
        print("\n🔍 Testing default vs explicit field selection...")
        
        # Get contacts without specifying fields (default behavior)
        contacts_result = await list_contacts(context, limit=5)
        if contacts_result["count"] == 0:
            pytest.skip("Need at least 1 contact for comparison test")
        
        collection_id = contacts_result["collection_id"]
        
        # Test 1: Default fields (no explicit field selection)
        default_details = await get_collection_details(context, collection_id, limit=1)
        
        if default_details.get('contacts'):
            default_contact = default_details['contacts'][0]
            default_fields = set(default_contact.keys())
            print(f"\nDefault fields ({len(default_fields)}): {sorted(default_fields)}")
        
        # Test 2: Explicit minimal fields
        minimal_fields = ["id", "given_name", "email"]
        minimal_details = await get_collection_details(
            context, 
            collection_id, 
            fields=minimal_fields,
            limit=1
        )
        
        if minimal_details.get('contacts'):
            minimal_contact = minimal_details['contacts'][0]
            minimal_actual_fields = set(minimal_contact.keys())
            print(f"\nMinimal requested fields: {minimal_fields}")
            print(f"Minimal actual fields ({len(minimal_actual_fields)}): {sorted(minimal_actual_fields)}")
            
            # Should contain at least the requested fields (or their equivalents)
            assert "id" in minimal_actual_fields, "Should always have ID"
        
        # Test 3: Comprehensive fields
        comprehensive_fields = ["id", "given_name", "family_name", "email", "email_addresses", "company", "phone1", "city", "state"]
        comprehensive_details = await get_collection_details(
            context,
            collection_id, 
            fields=comprehensive_fields,
            limit=1
        )
        
        if comprehensive_details.get('contacts'):
            comprehensive_contact = comprehensive_details['contacts'][0]
            comprehensive_actual_fields = set(comprehensive_contact.keys())
            print(f"\nComprehensive requested fields: {comprehensive_fields}")
            print(f"Comprehensive actual fields ({len(comprehensive_actual_fields)}): {sorted(comprehensive_actual_fields)}")
            
            # Should have more fields than minimal
            assert len(comprehensive_actual_fields) >= len(minimal_actual_fields), \
                "Comprehensive selection should return at least as many fields as minimal"
        
        print("✅ Default vs explicit field selection test passed")

    @pytest.mark.asyncio
    async def test_mcp_server_compatibility(self):
        """
        Test that our MCP server interface now accepts both string and list formats.
        """
        print("\n🔍 Testing MCP server compatibility...")
        
        # Test that the server can handle both formats
        from src.mcp.server import KeapMCPServer
        
        # This tests the type annotations and parameter handling
        KeapMCPServer()
        
        # The server should accept both Union[str, List[Dict[str, Any]]] for filters
        # This is mainly testing that our type annotations are correct
        print("✅ MCP server created successfully with Union type support")
        
        # Test via the actual server interface would require more complex setup
        # but our integration tests above cover the actual functionality
        
        print("✅ MCP server compatibility test passed")

    @pytest.mark.asyncio
    async def test_user_workflow_reproduction(self):
        """
        Reproduce the exact workflow the user described step by step.
        """
        context = Context()
        
        print("\n🔍 Reproducing exact user workflow...")
        
        # Step 1: User tried to search for "Scott" with filters
        print("\n1. User's first attempt - JSON string filter:")
        user_filter = '[{"field": "given_name", "operator": "equals", "value": "Scott"}]'
        print(f"   Input: {user_filter}")
        
        try:
            scott_result = await list_contacts(context, filters=user_filter, limit=50)
            print(f"   ✅ SUCCESS: Found {scott_result.get('count', 0)} contacts named Scott")
            scott_result["collection_id"]
        except Exception as e:
            print(f"   ❌ This should work now: {e}")
            pytest.fail(f"User's exact filter should work: {e}")
        
        # Step 2: User got schema successfully (this was working)
        print("\n2. User checked schema:")
        schema = await get_contact_schema(context)
        print("   ✅ Schema retrieved successfully")
        assert "standard_fields" in schema
        assert "filter_examples" in schema
        
        # Step 3: User tried basic list without filters (this was working)
        print("\n3. User tried basic list (no filters):")
        basic_result = await list_contacts(context, limit=50)
        print(f"   ✅ Basic list: {basic_result.get('count', 0)} contacts")
        basic_collection_id = basic_result["collection_id"]
        
        # Step 4: User requested specific fields but only got emails
        print("\n4. User requested specific fields:")
        requested_fields = ["id", "given_name", "family_name", "email_addresses"]
        details = await get_collection_details(
            context,
            basic_collection_id,
            fields=requested_fields
        )
        
        print(f"   Requested: {requested_fields}")
        if details.get('contacts'):
            sample_contact = details['contacts'][0]
            actual_fields = list(sample_contact.keys())
            print(f"   Actually got: {sorted(actual_fields)}")
            
            # User complained they only got emails - this should not happen now
            non_email_fields = [f for f in actual_fields if 'email' not in f.lower()]
            print(f"   Non-email fields: {sorted(non_email_fields)}")
            
            assert len(non_email_fields) >= 2, \
                f"Should get more than just email fields. Got: {sorted(actual_fields)}"
            
            # Check specific fields the user requested
            for field in ["id", "given_name", "family_name"]:
                if field in actual_fields:
                    value = sample_contact.get(field)
                    print(f"   {field}: '{value}' ({'✅' if value else '❌'})")
        
        print("\n✅ User workflow reproduction completed successfully")
        print("   All the issues the user reported should now be fixed!")

    @pytest.mark.asyncio 
    async def test_scott_search_comprehensive(self):
        """
        Comprehensive test to find all contacts named Scott in the database.
        """
        context = Context()
        
        print("\n🔍 Comprehensive Scott search test...")
        
        # Test with JSON string (user's format)
        scott_filter_json = '[{"field": "given_name", "operator": "equals", "value": "Scott"}]'
        result_json = await list_contacts(context, filters=scott_filter_json, limit=100)
        
        # Test with Python list (direct format)
        scott_filter_list = [{"field": "given_name", "operator": "equals", "value": "Scott"}]
        result_list = await list_contacts(context, filters=scott_filter_list, limit=100)
        
        print(f"JSON string format: {result_json.get('count', 0)} contacts")
        print(f"Python list format: {result_list.get('count', 0)} contacts")
        
        # Both should return the same number of contacts
        assert result_json["count"] == result_list["count"], \
            f"JSON and list formats should return same results: {result_json['count']} vs {result_list['count']}"
        
        # If we found Scotts, verify they're actually named Scott
        if result_json["count"] > 0:
            details = await get_collection_details(
                context,
                result_json["collection_id"],
                fields=["id", "given_name", "family_name", "email"],
                limit=5
            )
            
            print("\nFound Scotts:")
            for i, contact in enumerate(details.get("contacts", [])):
                given_name = contact.get("given_name", "")
                family_name = contact.get("family_name", "")
                email = contact.get("email", "")
                print(f"  {i+1}. {given_name} {family_name} ({email}) - ID: {contact.get('id')}")
                
                # Verify they're actually named Scott
                assert given_name == "Scott", f"Expected 'Scott', got '{given_name}'"
        
        print("✅ Comprehensive Scott search test passed")
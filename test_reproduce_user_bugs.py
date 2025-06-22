#!/usr/bin/env python3
"""
Test script to reproduce the exact MCP server bugs reported by the user.

This script directly tests the problematic scenarios:
1. get_collection_fields character-by-character parsing bug
2. get_collection_details field selection not working
3. Complex field name handling issues

Usage: python test_reproduce_user_bugs.py
"""

import asyncio
import json
from mcp.server.fastmcp import Context
from src.mcp.tools_collections import list_contacts, get_collection_fields, get_collection_details, get_contact_schema


async def test_user_reported_bugs():
    """Reproduce the exact bugs the user reported."""
    print("🔍 Testing MCP Server Bugs - Reproducing User Issues")
    print("=" * 60)
    
    context = Context()
    
    # Step 1: Find Scott contacts (this worked for user)
    print("\n1. Finding Scott contacts...")
    try:
        scott_filters = [{"field": "given_name", "operator": "equals", "value": "Scott"}]
        scott_result = await list_contacts(context, filters=scott_filters)
        print(f"   ✅ Found {scott_result['count']} Scott contacts in collection '{scott_result['collection_id']}'")
        collection_id = scott_result['collection_id']
    except Exception as e:
        print(f"   ❌ Failed to find Scott contacts: {e}")
        return
    
    # Step 2: Test get_collection_fields character parsing bug
    print("\n2. Testing get_collection_fields with complex field names...")
    
    # First get the schema to find actual custom field names
    schema = await get_contact_schema(context)
    custom_fields = [name for name in schema['fields'].keys() if 'custom_field' in name or 'FN' in name]
    print(f"   Available custom fields: {custom_fields[:5]}...")
    
    # Test the exact field list the user tried
    problematic_fields = [
        "6FN Next Date/Time",  # This should NOT be parsed character by character
        "given_name", 
        "family_name", 
        "email_addresses"
    ]
    
    try:
        print(f"   Testing fields: {problematic_fields}")
        fields_result = await get_collection_fields(
            collection_id=collection_id,
            fields=problematic_fields
        )
        
        print(f"   Result structure: {list(fields_result.keys())}")
        if "fields" in fields_result:
            field_keys = list(fields_result["fields"].keys())
            print(f"   Returned field keys: {field_keys}")
            
            # Check for the character parsing bug
            single_char_fields = [key for key in field_keys if len(key) == 1]
            if single_char_fields:
                print(f"   🐛 BUG CONFIRMED: Character parsing detected! Single chars: {single_char_fields}")
            else:
                print("   ✅ No character parsing bug detected")
                
            # Check if actual field names are present
            expected_in_results = [field for field in problematic_fields if field in field_keys]
            print(f"   Expected fields found: {expected_in_results}")
            
    except Exception as e:
        print(f"   ❌ get_collection_fields failed: {e}")
    
    # Step 3: Test get_collection_details field selection bug
    print("\n3. Testing get_collection_details field selection...")
    
    try:
        # Test with specific field selection (user reported this only returned emails)
        specific_fields = ["id", "given_name", "family_name", "email_addresses", "custom_field_239"]
        print(f"   Requesting specific fields: {specific_fields}")
        
        details_result = await get_collection_details(
            context,
            collection_id=collection_id,
            fields=specific_fields
        )
        
        print(f"   Returned {len(details_result.get('contacts', []))} contacts")
        
        if details_result.get('contacts'):
            first_contact = details_result['contacts'][0]
            returned_fields = list(first_contact.keys())
            print(f"   Returned fields: {returned_fields}")
            
            # Check if we only got emails (the reported bug)
            if returned_fields == ['email'] or returned_fields == ['email_addresses']:
                print("   🐛 BUG CONFIRMED: Only email fields returned!")
            elif set(specific_fields).issubset(set(returned_fields)):
                print("   ✅ All requested fields returned correctly")
            else:
                missing_fields = set(specific_fields) - set(returned_fields)
                print(f"   🐛 BUG CONFIRMED: Missing requested fields: {missing_fields}")
        
        # Compare with no field selection (user reported this worked)
        print("\n   Testing with NO field selection...")
        all_details_result = await get_collection_details(
            context,
            collection_id=collection_id
        )
        
        if all_details_result.get('contacts'):
            all_fields = list(all_details_result['contacts'][0].keys())
            print(f"   All fields returned (first 10): {all_fields[:10]}...")
            print(f"   Total fields when no selection: {len(all_fields)}")
            
            # Check if custom fields are present when not filtered
            custom_fields_present = [f for f in all_fields if 'custom_field' in f or f.startswith('6')]
            print(f"   Custom fields present: {custom_fields_present[:5]}...")
            
    except Exception as e:
        print(f"   ❌ get_collection_details failed: {e}")
    
    # Step 4: Test complex field name scenarios
    print("\n4. Testing complex field name handling...")
    
    complex_field_names = [
        "6FN Next Date/Time",  # Contains slash and space
        "given_name",          # Simple field
        "email_addresses",     # Underscore field
        "custom_field_1"       # Numbered field
    ]
    
    for field_name in complex_field_names:
        try:
            print(f"   Testing field: '{field_name}'")
            single_field_result = await get_collection_fields(
                collection_id=collection_id,
                fields=[field_name]  # Test with single field in list
            )
            
            if "fields" in single_field_result:
                returned_keys = list(single_field_result["fields"].keys())
                if field_name in returned_keys:
                    print(f"     ✅ Field '{field_name}' handled correctly")
                else:
                    print(f"     🐛 Field '{field_name}' not in results: {returned_keys}")
            
        except Exception as e:
            print(f"     ❌ Field '{field_name}' failed: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Bug reproduction test completed")


if __name__ == "__main__":
    asyncio.run(test_user_reported_bugs())
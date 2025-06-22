#!/usr/bin/env python3
"""
Test the new field name-first approach in list_contacts.
"""

import asyncio
import os
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_contact_schema, _resolve_custom_field_names_in_filters


async def test_new_filter_resolution():
    """Test the new field name-first filter resolution"""
    print("🧪 Testing new field name-first filter resolution...")
    
    test_filters = [
        # Preferred approach - field names
        {"field": "6FN Next Date/Time", "operator": "equals", "value": "test"},
        {"field": "email", "operator": "contains", "value": "@example.com"},
        
        # Explicit field ID approach
        {"field_id": "239", "operator": "equals", "value": "test"},
        {"field_id": "custom_fields.239", "operator": "equals", "value": "test"},
        
        # Legacy approach (should warn)
        {"field": "custom_fields.239", "operator": "equals", "value": "test"},
        
        # Unknown field (should warn)
        {"field": "Nonexistent Field", "operator": "equals", "value": "test"}
    ]
    
    print(f"📋 Testing filter resolution:")
    resolved_filters = await _resolve_custom_field_names_in_filters(test_filters)
    
    for i, (original, resolved) in enumerate(zip(test_filters, resolved_filters), 1):
        print(f"\n   {i}. Original: {original}")
        print(f"      Resolved: {resolved}")
        
        # Check if field_id was properly converted
        if 'field_id' in original and 'field_id' not in resolved:
            print(f"      ✅ field_id properly converted to field")
        elif original.get('field') != resolved.get('field'):
            print(f"      ✅ Field name resolved")
        else:
            print(f"      ⚪ No changes needed")


async def test_schema_shows_preferred_usage():
    """Test that the schema shows the preferred usage patterns"""
    print(f"\n🧪 Testing schema shows preferred usage patterns...")
    
    context = Context()
    schema = await get_contact_schema(context)
    
    # Find a few 6FN-related fields to show usage patterns
    print(f"📋 Custom field usage patterns:")
    
    custom_fields = schema['custom_fields']
    for field in custom_fields[:3]:  # Show first 3 as examples
        print(f"\n   Field: '{field['name']}' (ID: {field['id']})")
        usage = field.get('usage', {})
        print(f"      Preferred:   {usage.get('preferred', 'N/A')}")
        print(f"      Explicit ID: {usage.get('explicit_id', 'N/A')}")
        print(f"      Legacy:      {usage.get('legacy', 'N/A')}")
    
    # Show 6FN fields specifically
    fn_fields = [f for f in custom_fields if '6fn' in f['name'].lower()]
    if fn_fields:
        print(f"\n🎯 6FN field usage examples:")
        for field in fn_fields:
            usage = field.get('usage', {})
            print(f"   '{field['name']}': {usage.get('preferred', 'N/A')}")


async def test_list_contacts_with_new_approach():
    """Test list_contacts with the new field name-first approach"""
    print(f"\n🧪 Testing list_contacts with new approach...")
    
    context = Context()
    
    test_cases = [
        {
            "name": "Field name (preferred)",
            "filter": {"field": "6FN Next Date/Time", "operator": "is_not_null", "value": ""}
        },
        {
            "name": "Explicit field ID",
            "filter": {"field_id": "239", "operator": "is_not_null", "value": ""}
        },
        {
            "name": "Standard field",
            "filter": {"field": "email", "operator": "contains", "value": "@"}
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Filter: {test_case['filter']}")
        
        try:
            result = await list_contacts(
                context,
                filters=[test_case['filter']],
                limit=5
            )
            
            count = result.get('count', 0)
            collection_id = result.get('collection_id', 'None')
            
            results.append({
                'name': test_case['name'],
                'success': True,
                'count': count,
                'collection_id': collection_id
            })
            
            print(f"   ✅ Success: Found {count} contacts")
            
        except Exception as e:
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': str(e)
            })
            print(f"   ❌ Failed: {e}")
    
    return results


async def main():
    """Main test function"""
    print("🚀 Testing Field Name-First Approach in list_contacts")
    print("=" * 60)
    
    # Test filter resolution
    await test_new_filter_resolution()
    
    # Test schema shows preferred usage
    await test_schema_shows_preferred_usage()
    
    # Test list_contacts with new approach
    results = await test_list_contacts_with_new_approach()
    
    print(f"\n" + "="*60)
    print(f"📊 SUMMARY")
    print(f"="*60)
    
    successful_tests = [r for r in results if r.get('success', False)]
    failed_tests = [r for r in results if not r.get('success', False)]
    
    print(f"✅ Successful tests: {len(successful_tests)}")
    for test in successful_tests:
        print(f"   - {test['name']}: {test['count']} contacts found")
    
    if failed_tests:
        print(f"❌ Failed tests: {len(failed_tests)}")
        for test in failed_tests:
            print(f"   - {test['name']}: {test.get('error', 'Unknown error')}")
    
    print(f"\n🎯 NEW APPROACH SUMMARY:")
    print(f"   ✅ Primary: Use field names in 'field' parameter")
    print(f"   ✅ Explicit: Use 'field_id' for direct field ID access")
    print(f"   ⚠️  Legacy: 'custom_fields.ID' format still works but discouraged")
    print(f"   📖 Schema: get_contact_schema() shows preferred usage for each field")


if __name__ == "__main__":
    asyncio.run(main())
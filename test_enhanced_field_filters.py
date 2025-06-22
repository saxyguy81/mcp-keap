#!/usr/bin/env python3
"""
Test the enhanced field name resolution in list_contacts filters.
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

from src.mcp.tools_collections import list_contacts, _resolve_custom_field_names_in_filters


async def test_field_name_resolution():
    """Test the field name resolution function directly"""
    print("🧪 Testing field name resolution function...")
    
    test_filters = [
        {"field": "6FN Next Date/Time", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000"},
        {"field": "custom_fields.6FN Next Date/Time", "operator": "equals", "value": "test"},
        {"field": "custom_fields.239", "operator": "equals", "value": "test"},
        {"field": "email", "operator": "contains", "value": "@example.com"},
        {"field": "Nonexistent Field", "operator": "equals", "value": "test"}
    ]
    
    resolved_filters = await _resolve_custom_field_names_in_filters(test_filters)
    
    print(f"📋 Filter resolution results:")
    for i, (original, resolved) in enumerate(zip(test_filters, resolved_filters), 1):
        original_field = original['field']
        resolved_field = resolved['field']
        
        if original_field != resolved_field:
            print(f"   {i}. '{original_field}' → '{resolved_field}' ✅")
        else:
            print(f"   {i}. '{original_field}' → unchanged ⚪")


async def test_list_contacts_with_field_names():
    """Test list_contacts with different field name formats"""
    print(f"\n🧪 Testing list_contacts with field name formats...")
    
    context = Context()
    
    # Test cases that should all resolve to the same search
    test_cases = [
        {
            "name": "Field ID format",
            "filter": {"field": "custom_fields.239", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000"}
        },
        {
            "name": "Field name directly", 
            "filter": {"field": "6FN Next Date/Time", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000"}
        },
        {
            "name": "Named format",
            "filter": {"field": "custom_fields.6FN Next Date/Time", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000"}
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
            
            print(f"   ✅ Success: Found {count} contacts (Collection: {collection_id})")
            
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
    print("🚀 Testing Enhanced Field Name Support in list_contacts")
    print("=" * 60)
    
    # Test field name resolution
    await test_field_name_resolution()
    
    # Test list_contacts with different formats
    results = await test_list_contacts_with_field_names()
    
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
    
    # Check if all successful tests found the same number of contacts
    if successful_tests:
        counts = [test['count'] for test in successful_tests]
        if len(set(counts)) == 1:
            print(f"\n✅ All formats returned the same result ({counts[0]} contacts)")
            print(f"✅ Field name resolution is working correctly!")
        else:
            print(f"\n⚠️ Different formats returned different counts: {counts}")
    
    print(f"\n🎯 SUPPORTED FORMATS:")
    print(f"   1. Field ID: 'custom_fields.239'")
    print(f"   2. Field name: '6FN Next Date/Time'")  
    print(f"   3. Named format: 'custom_fields.6FN Next Date/Time'")


if __name__ == "__main__":
    asyncio.run(main())
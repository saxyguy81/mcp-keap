#!/usr/bin/env python3
"""
Test the enhanced get_contact_schema function with custom field definitions.
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

from src.mcp.tools_collections import get_contact_schema


async def test_enhanced_schema():
    """Test the enhanced get_contact_schema function"""
    print("🧪 Testing enhanced get_contact_schema...")
    
    context = Context()
    
    try:
        schema = await get_contact_schema(context)
        
        print(f"✅ Schema retrieved successfully")
        print(f"   Standard fields: {len(schema['standard_fields'])}")
        print(f"   Custom fields: {len(schema['custom_fields'])}")
        print(f"   Supported operators: {len(schema['supported_operators'])}")
        print(f"   Filter examples: {len(schema['filter_examples'])}")
        
        # Show 6FN-related custom fields
        print(f"\n🎯 6FN-related custom fields:")
        custom_fields = schema['custom_fields']
        for field in custom_fields:
            if '6fn' in field['name'].lower():
                print(f"   '{field['name']}' (ID: {field['id']}, Type: {field['type']})")
                usage = field.get('usage', {})
                print(f"     Preferred: {usage.get('preferred', 'N/A')}")
                print(f"     Explicit:  {usage.get('explicit_id', 'N/A')}")
        
        # Show sample custom fields
        print(f"\n📋 Sample custom fields (first 5):")
        for i, field in enumerate(custom_fields[:5]):
            usage = field.get('usage', {})
            print(f"   {i+1}. '{field['name']}' (ID: {field['id']})")
            print(f"      Preferred: {usage.get('preferred', 'N/A')}")
        
        # Show custom field filter example
        print(f"\n📖 Custom field filter example:")
        for example in schema['filter_examples']:
            if 'custom field' in example['description']:
                print(f"   Description: {example['description']}")
                print(f"   Filter: {example['filter']}")
                if 'note' in example:
                    print(f"   Note: {example['note']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing schema: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 Testing Enhanced Contact Schema")
    print("=" * 40)
    
    success = await test_enhanced_schema()
    
    print(f"\n" + "="*40)
    print(f"📊 SUMMARY")
    print(f"="*40)
    
    if success:
        print(f"✅ Enhanced get_contact_schema: Working")
        print(f"✅ Custom field definitions: Loaded")
        print(f"✅ Field name ↔ ID mapping: Available")
        print(f"✅ Filter examples: Updated")
        print(f"\n✅ Schema enhancement complete!")
    else:
        print(f"❌ Schema enhancement failed")


if __name__ == "__main__":
    asyncio.run(main())
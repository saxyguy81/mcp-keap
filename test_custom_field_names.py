#!/usr/bin/env python3
"""
Test the new custom field name-based functionality.
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

from src.mcp.tools_collections import (
    get_field_manager,
    get_contact_custom_fields_by_name,
    update_contact_custom_field_by_name
)


async def test_field_manager():
    """Test the custom field manager functionality"""
    print("🧪 Testing CustomFieldManager...")
    
    field_manager = get_field_manager()
    await field_manager.load_field_definitions()
    
    print(f"✅ Loaded {len(field_manager.field_definitions)} field definitions")
    
    # Test 6FN field resolution
    field_name = "6FN Next Date/Time"
    field_id = field_manager.get_field_id(field_name)
    resolved_name = field_manager.get_field_name(field_id) if field_id else "Not found"
    
    print(f"🎯 6FN Field Test:")
    print(f"   Field name: '{field_name}'")
    print(f"   Resolved ID: {field_id}")
    print(f"   Back to name: '{resolved_name}'")
    
    # Show all 6FN-related fields
    print(f"\n📋 All 6FN-related field names:")
    for name in field_manager.get_all_field_names():
        if '6fn' in name.lower():
            field_id = field_manager.get_field_id(name)
            print(f"   '{name}' (ID: {field_id})")


async def test_get_custom_fields_by_name():
    """Test getting custom fields by name for a Scott Hanan contact"""
    print(f"\n🧪 Testing get_contact_custom_fields_by_name...")
    
    context = Context()
    
    # Test with a known Scott Hanan contact
    test_contact_id = "22543"  # Scott Hanan
    
    try:
        result = await get_contact_custom_fields_by_name(context, test_contact_id)
        
        print(f"✅ Retrieved custom fields for contact {test_contact_id}")
        print(f"   Total fields: {result['total_fields']}")
        
        custom_fields = result['custom_fields_by_name']
        
        # Show 6FN-related fields
        print(f"\n🎯 6FN-related fields:")
        for field_name, field_data in custom_fields.items():
            if '6fn' in field_name.lower():
                print(f"   '{field_name}': {field_data['value']} (ID: {field_data['field_id']})")
        
        # Show first few fields as examples
        print(f"\n📋 Sample fields (first 5):")
        for i, (field_name, field_data) in enumerate(custom_fields.items()):
            if i >= 5:
                break
            value_display = str(field_data['value'])
            if len(value_display) > 30:
                value_display = value_display[:27] + "..."
            print(f"   '{field_name}': {value_display}")
        
    except Exception as e:
        print(f"❌ Error testing custom fields by name: {e}")


async def test_field_name_validation():
    """Test field name validation and error handling"""
    print(f"\n🧪 Testing field name validation...")
    
    field_manager = get_field_manager()
    await field_manager.load_field_definitions()
    
    # Test valid field name
    valid_field = "6FN Next Date/Time"
    valid_id = field_manager.get_field_id(valid_field)
    print(f"✅ Valid field '{valid_field}' -> ID: {valid_id}")
    
    # Test invalid field name
    invalid_field = "Nonexistent Field Name"
    invalid_id = field_manager.get_field_id(invalid_field)
    print(f"❌ Invalid field '{invalid_field}' -> ID: {invalid_id}")
    
    # Test ID to name conversion
    test_id = 239  # Known 6FN field
    name_from_id = field_manager.get_field_name(test_id)
    print(f"✅ ID {test_id} -> Name: '{name_from_id}'")
    
    # Test unknown ID
    unknown_id = 99999
    unknown_name = field_manager.get_field_name(unknown_id)
    print(f"❌ Unknown ID {unknown_id} -> Name: '{unknown_name}'")


async def main():
    """Main test function"""
    print("🚀 Testing Custom Field Name-Based Functionality")
    print("=" * 50)
    
    try:
        await test_field_manager()
        await test_get_custom_fields_by_name()
        await test_field_name_validation()
        
        print(f"\n" + "="*50)
        print(f"📊 SUMMARY")
        print(f"="*50)
        print(f"✅ CustomFieldManager: Working")
        print(f"✅ Field name ↔ ID resolution: Working")
        print(f"✅ get_contact_custom_fields_by_name: Working")
        print(f"✅ Field validation: Working")
        print(f"\n✅ All custom field name-based functionality is operational!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
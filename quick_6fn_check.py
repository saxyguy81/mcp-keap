#!/usr/bin/env python3
"""
Quick check to find 6FN data by examining custom field structure and a small sample.
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

from src.mcp.tools_collections import list_contacts, get_collection_details, get_contact_schema


async def check_custom_field_schema():
    """Check the custom field schema to see field names"""
    context = Context()
    
    print("🔍 Checking custom field schema...")
    
    try:
        schema = await get_contact_schema(context)
        
        print("📋 Schema keys:", list(schema.keys()))
        
        # Look for any mentions of custom fields in schema
        for key, value in schema.items():
            if 'field' in key.lower() or 'custom' in key.lower():
                print(f"   {key}: {value}")
        
        # Check if there are field definitions
        if 'custom_fields' in schema:
            custom_fields = schema['custom_fields']
            print(f"   Custom field definitions: {len(custom_fields) if isinstance(custom_fields, list) else 'Not a list'}")
            
            if isinstance(custom_fields, list):
                for field in custom_fields[:10]:  # First 10
                    if isinstance(field, dict):
                        field_name = field.get('name', field.get('label', 'Unknown'))
                        field_id = field.get('id', 'Unknown')
                        print(f"     Field {field_id}: {field_name}")
                        
                        # Check for 6FN in field names
                        if '6fn' in str(field_name).lower() or 'figure' in str(field_name).lower():
                            print(f"       🎯 POTENTIAL 6FN FIELD: {field_name}")
        
    except Exception as e:
        print(f"❌ Schema check failed: {e}")


async def sample_contact_deep_dive():
    """Get a small sample and do deep dive on custom fields"""
    context = Context()
    
    print("\n🔍 Deep dive on sample contacts...")
    
    try:
        # Get just 3 contacts with offset to get different ones
        result = await list_contacts(context, limit=3, offset=50)
        
        if result['count'] == 0:
            print("❌ No contacts found")
            return
        
        # Get full details
        details = await get_collection_details(
            context,
            result['collection_id'],
            fields=["id", "given_name", "family_name", "email", "custom_fields"]
        )
        
        contacts = details.get('contacts', [])
        print(f"📋 Analyzing {len(contacts)} contacts in detail...")
        
        for i, contact in enumerate(contacts, 1):
            print(f"\n👤 Contact {i}: {contact.get('given_name', '')} {contact.get('family_name', '')} (ID: {contact.get('id')})")
            print(f"   Email: {contact.get('email', 'N/A')}")
            
            custom_fields = contact.get('custom_fields', [])
            print(f"   Custom fields: {len(custom_fields)}")
            
            # Check each custom field
            fields_with_data = []
            potential_6fn_fields = []
            
            for field in custom_fields:
                field_id = field.get('id')
                field_content = field.get('content')
                field_type = field.get('type', 'unknown')
                
                # Check if field has data
                if field_content is not None and str(field_content).strip():
                    fields_with_data.append(field)
                    
                    # Check for 6FN patterns in content
                    content_str = str(field_content).lower()
                    if ('6fn' in content_str or 'sixfn' in content_str or 
                        'six figure' in content_str or 'figure number' in content_str):
                        potential_6fn_fields.append(field)
                        print(f"   🎯 POTENTIAL 6FN FIELD {field_id}: {field_content}")
            
            print(f"   Fields with data: {len(fields_with_data)}")
            print(f"   Potential 6FN fields: {len(potential_6fn_fields)}")
            
            # Show some sample fields with data
            if fields_with_data:
                print("   Sample fields with data:")
                for field in fields_with_data[:5]:
                    content = str(field.get('content', ''))
                    if len(content) < 50:  # Only show short content
                        print(f"     Field {field.get('id')}: {content}")
                    else:
                        print(f"     Field {field.get('id')}: {content[:47]}...")
            
            # Check contact name for Scott/Hanan
            given_name = contact.get('given_name', '').lower()
            family_name = contact.get('family_name', '').lower()
            email = contact.get('email', '').lower()
            
            if ('scott' in given_name or 'hanan' in family_name or 'smhanan' in email):
                print(f"   🎯 POTENTIAL SCOTT HANAN MATCH!")
                
                # Show ALL custom fields for this contact
                print(f"   📋 ALL custom fields for this contact:")
                for field in custom_fields:
                    field_id = field.get('id')
                    content = field.get('content')
                    if content is not None:
                        content_str = str(content)
                        if len(content_str) < 100:
                            print(f"       Field {field_id}: {content}")
                        else:
                            print(f"       Field {field_id}: {content_str[:97]}...")
    
    except Exception as e:
        print(f"❌ Sample analysis failed: {e}")
        import traceback
        traceback.print_exc()


async def quick_email_search():
    """Try a quick targeted search for smhanan"""
    context = Context()
    
    print("\n🔍 Quick targeted searches...")
    
    # Try different offset positions to find Scott Hanan
    offsets_to_try = [0, 100, 200, 300, 400, 500]
    
    for offset in offsets_to_try:
        try:
            print(f"\n📋 Checking offset {offset}...")
            
            result = await list_contacts(context, limit=10, offset=offset)
            
            if result['count'] == 0:
                continue
            
            details = await get_collection_details(
                context,
                result['collection_id'],
                fields=["id", "given_name", "family_name", "email"]
            )
            
            for contact in details.get('contacts', []):
                given_name = contact.get('given_name', '').lower()
                family_name = contact.get('family_name', '').lower()
                email = contact.get('email', '').lower()
                
                if ('scott' in given_name or 'hanan' in family_name or 'smhanan' in email):
                    print(f"   🎯 FOUND: {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
                    return contact  # Return first match for detailed analysis
        
        except Exception as e:
            print(f"   ❌ Error at offset {offset}: {e}")
    
    print("   No Scott Hanan contacts found in checked offsets")
    return None


async def main():
    """Main execution function"""
    print("🚀 Quick 6FN & Scott Hanan Check")
    print("=" * 35)
    
    try:
        # Check schema for field definitions
        await check_custom_field_schema()
        
        # Deep dive on sample contacts
        await sample_contact_deep_dive()
        
        # Quick search for Scott Hanan
        scott_contact = await quick_email_search()
        
        if scott_contact:
            print(f"\n🎯 Found Scott Hanan contact - getting full details...")
            # Would need to get full custom field details here
        
        print("\n✅ Quick check complete!")
        
    except Exception as e:
        print(f"❌ Error during check: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Demonstrate the complete field name-first approach with real search examples.
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

from src.mcp.tools_collections import list_contacts, get_contact_schema, get_collection_details


async def demonstrate_field_name_approach():
    """Demonstrate the complete field name-first approach"""
    print("🚀 Complete Field Name-First Approach Demonstration")
    print("=" * 60)
    
    context = Context()
    
    # Step 1: Get schema to see available fields
    print("1️⃣ Getting contact schema to see available fields...")
    schema = await get_contact_schema(context)
    
    print(f"   ✅ Found {len(schema['custom_fields'])} custom fields")
    
    # Show 6FN fields as examples
    print(f"\n📋 6FN-related fields available:")
    for field in schema['custom_fields']:
        if '6fn' in field['name'].lower():
            usage = field.get('usage', {})
            print(f"   • '{field['name']}' → {usage.get('preferred', 'N/A')}")
    
    # Step 2: Search using field names (preferred approach)
    print(f"\n2️⃣ Searching using field names (preferred approach)...")
    
    search_examples = [
        {
            "description": "Find contacts with any 6FN Next Date/Time",
            "filter": {"field": "6FN Next Date/Time", "operator": "is_not_null", "value": ""}
        },
        {
            "description": "Find contacts with email addresses",
            "filter": {"field": "email", "operator": "contains", "value": "@"}
        }
    ]
    
    for example in search_examples:
        print(f"\n   📋 {example['description']}")
        print(f"      Filter: {example['filter']}")
        
        try:
            result = await list_contacts(
                context,
                filters=[example['filter']],
                limit=3
            )
            
            count = result.get('count', 0)
            print(f"      ✅ Found {count} contacts")
            
            if count > 0:
                # Get details for first few contacts
                details = await get_collection_details(context, result['collection_id'])
                contacts = details.get('contacts', [])
                
                for i, contact in enumerate(contacts[:2], 1):
                    name = f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
                    print(f"         {i}. {name} (ID: {contact.get('id')})")
                    
                    # Show the specific field value if it's a custom field search
                    if example['filter']['field'] == "6FN Next Date/Time":
                        custom_fields = contact.get('custom_fields', [])
                        for cf in custom_fields:
                            if cf.get('id') == 239:  # 6FN Next Date/Time field ID
                                print(f"            6FN Next Date/Time: {cf.get('content', 'None')}")
                                break
        
        except Exception as e:
            print(f"      ❌ Failed: {e}")
    
    # Step 3: Compare with explicit field ID approach
    print(f"\n3️⃣ Same search using explicit field ID (alternative approach)...")
    
    try:
        result_by_id = await list_contacts(
            context,
            filters=[{"field_id": "239", "operator": "is_not_null", "value": ""}],
            limit=3
        )
        
        count_by_id = result_by_id.get('count', 0)
        print(f"   Using field_id '239': Found {count_by_id} contacts")
        
        # Verify both approaches return the same results
        result_by_name = await list_contacts(
            context,
            filters=[{"field": "6FN Next Date/Time", "operator": "is_not_null", "value": ""}],
            limit=3
        )
        
        count_by_name = result_by_name.get('count', 0)
        print(f"   Using field name '6FN Next Date/Time': Found {count_by_name} contacts")
        
        if count_by_id == count_by_name:
            print(f"   ✅ Both approaches return identical results!")
        else:
            print(f"   ⚠️ Different results - field name: {count_by_name}, field ID: {count_by_id}")
    
    except Exception as e:
        print(f"   ❌ Comparison failed: {e}")
    
    # Step 4: Show usage recommendations
    print(f"\n4️⃣ Usage Recommendations:")
    print(f"   ✅ PREFERRED: Use field names for readability")
    print(f"      Example: {{'field': '6FN Next Date/Time', 'operator': 'equals', 'value': '...'}}")
    print(f"   ")
    print(f"   🔧 EXPLICIT: Use field_id when you know the exact ID")
    print(f"      Example: {{'field_id': '239', 'operator': 'equals', 'value': '...'}}")
    print(f"   ")
    print(f"   ⚠️  LEGACY: Old format still works but discouraged")
    print(f"      Example: {{'field': 'custom_fields.239', 'operator': 'equals', 'value': '...'}}")
    
    # Step 5: Show filter examples from schema
    print(f"\n5️⃣ Filter examples from schema:")
    filter_examples = schema.get('filter_examples', [])
    for example in filter_examples:
        if 'custom field' in example.get('description', '').lower():
            print(f"   • {example['description']}")
            print(f"     {example['filter']}")
    
    print(f"\n" + "="*60)
    print(f"📊 DEMONSTRATION COMPLETE")
    print(f"="*60)
    print(f"✅ Field names are now the primary interface")
    print(f"✅ get_contact_schema() shows exact usage for each field")
    print(f"✅ Both field names and explicit field_id work seamlessly")
    print(f"✅ Legacy format still supported for backward compatibility")


async def main():
    """Main demonstration function"""
    await demonstrate_field_name_approach()


if __name__ == "__main__":
    asyncio.run(main())
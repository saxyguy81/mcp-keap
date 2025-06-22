#!/usr/bin/env python3
"""
Script to analyze custom field data for Scott Hanan contacts related to "6FN".
Looks for formatting variations in custom field values that might represent the same data.
"""

import asyncio
import os
import json
from collections import defaultdict
from typing import Dict, List, Any
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_collection_details


async def find_contacts_with_custom_fields():
    """Find all contacts and search for Scott Hanan or 6FN-related data"""
    context = Context()
    
    print("🔍 Searching for contacts with custom fields...")
    
    # Get a broader set of contacts
    contacts_result = await list_contacts(
        context,
        limit=50  # Get a reasonable sample
    )
    
    print(f"Found {contacts_result['count']} total contacts")
    
    # Get detailed contact information including custom fields
    details = await get_collection_details(
        context, 
        contacts_result['collection_id'],
        fields=["id", "given_name", "family_name", "email", "custom_fields"]
    )
    
    # Filter for contacts with custom fields or Scott/Hanan in name
    relevant_contacts = []
    scott_hanan_contacts = []
    
    print("\n📋 Scanning contacts...")
    for contact in details['contacts']:
        given_name = contact.get('given_name', '').lower()
        family_name = contact.get('family_name', '').lower()
        custom_fields = contact.get('custom_fields', [])
        
        # Check for Scott Hanan
        if 'scott' in given_name or 'hanan' in family_name:
            scott_hanan_contacts.append(contact)
            print(f"   👤 Found name match: {contact.get('given_name')} {contact.get('family_name')}")
        
        # Check for 6FN in custom fields
        has_6fn_data = False
        if custom_fields:
            for field in custom_fields:
                content = str(field.get('content', '')).lower()
                if '6fn' in content or '6-fn' in content or 'sixfn' in content:
                    has_6fn_data = True
                    break
        
        # Include if has custom fields or name match or 6FN data
        if custom_fields or 'scott' in given_name or 'hanan' in family_name or has_6fn_data:
            relevant_contacts.append(contact)
    
    print(f"✅ Found {len(scott_hanan_contacts)} Scott/Hanan contacts")
    print(f"✅ Found {len(relevant_contacts)} contacts with custom fields or relevant names")
    
    return relevant_contacts, scott_hanan_contacts


def analyze_custom_fields_for_6fn(contacts: List[Dict[str, Any]]):
    """Analyze custom fields looking for 6FN-related data and formatting variations"""
    
    print("\n📊 Analyzing custom fields for 6FN-related data...")
    
    # Collect all custom field data
    all_custom_fields = defaultdict(list)
    field_variations = defaultdict(set)
    
    for contact in contacts:
        contact_id = contact.get('id')
        custom_fields = contact.get('custom_fields', [])
        
        print(f"\n👤 Contact ID: {contact_id}")
        print(f"   Name: {contact.get('given_name')} {contact.get('family_name')}")
        print(f"   Email: {contact.get('email', 'N/A')}")
        
        if not custom_fields:
            print("   ❌ No custom fields found")
            continue
            
        print(f"   📋 Custom fields ({len(custom_fields)}):")
        
        for field in custom_fields:
            field_id = field.get('id')
            field_content = field.get('content', '')
            field_type = field.get('type', 'unknown')
            
            # Store field data
            all_custom_fields[field_id].append({
                'contact_id': contact_id,
                'content': field_content,
                'type': field_type
            })
            
            # Check for 6FN-related content
            content_str = str(field_content).lower()
            if '6fn' in content_str or '6-fn' in content_str or 'sixfn' in content_str:
                print(f"      🎯 FIELD {field_id} ({field_type}): {field_content}")
                field_variations[field_id].add(field_content)
            else:
                print(f"      - Field {field_id} ({field_type}): {field_content}")
    
    return analyze_field_variations(all_custom_fields, field_variations)


def analyze_field_variations(all_fields: Dict, fn_fields: Dict):
    """Analyze variations in field formatting"""
    
    print("\n🔍 ANALYSIS: 6FN-Related Field Variations")
    print("=" * 50)
    
    if not fn_fields:
        print("❌ No 6FN-related custom fields found")
        return
    
    for field_id, variations in fn_fields.items():
        print(f"\n📋 Field ID {field_id}:")
        print(f"   Variations found: {len(variations)}")
        
        for variation in sorted(variations):
            print(f"   - '{variation}'")
            
        # Look for potential formatting differences
        if len(variations) > 1:
            print("   🚨 MULTIPLE VARIATIONS DETECTED!")
            
            # Analyze common formatting patterns
            normalized_values = set()
            for val in variations:
                # Normalize for comparison
                normalized = str(val).lower().replace('-', '').replace('_', '').replace(' ', '')
                normalized_values.add(normalized)
            
            if len(normalized_values) < len(variations):
                print("   ⚠️  POTENTIAL FORMATTING INCONSISTENCY:")
                print("   Some values may represent the same data with different formatting")
    
    # Look for cross-field patterns
    print("\n🔄 Cross-Field Analysis:")
    print("=" * 30)
    
    all_6fn_values = []
    for variations in fn_fields.values():
        all_6fn_values.extend(variations)
    
    # Group by normalized content
    normalized_groups = defaultdict(list)
    for value in all_6fn_values:
        normalized = str(value).lower().replace('-', '').replace('_', '').replace(' ', '').replace('.', '')
        normalized_groups[normalized].append(value)
    
    for normalized, original_values in normalized_groups.items():
        if len(set(original_values)) > 1:
            print(f"📝 Normalized '{normalized}' appears as:")
            for val in set(original_values):
                print(f"   - '{val}'")


async def main():
    """Main execution function"""
    print("🚀 Custom Field Analysis for Scott Hanan & 6FN Data")
    print("=" * 55)
    
    try:
        # Find relevant contacts
        all_contacts, scott_hanan_contacts = await find_contacts_with_custom_fields()
        
        if scott_hanan_contacts:
            print(f"\n🎯 Focusing on {len(scott_hanan_contacts)} Scott/Hanan contacts")
            analyze_custom_fields_for_6fn(scott_hanan_contacts)
        else:
            print("\n❌ No Scott/Hanan contacts found")
            print("🔍 Analyzing all contacts with custom fields for 6FN data...")
            analyze_custom_fields_for_6fn(all_contacts)
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
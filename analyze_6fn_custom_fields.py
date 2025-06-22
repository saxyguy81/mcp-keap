#!/usr/bin/env python3
"""
Analyze 6FN custom field data across all 10 Scott Hanan contacts for formatting variations.
"""

import asyncio
import os
import json
import re
from collections import defaultdict
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_collection_details


# Known Scott Hanan contact IDs from comprehensive search
SCOTT_HANAN_IDS = [22775, 22773, 22543, 23719, 23709, 23583, 23581, 23557, 23555, 23553]


async def get_scott_hanan_contacts_with_custom_fields():
    """Get all Scott Hanan contacts with their custom field data"""
    context = Context()
    
    print("🔍 Getting all 10 Scott Hanan contacts with custom fields...")
    
    scott_contacts = []
    
    # Search in batches around known contact ID ranges
    search_ranges = [
        (1900, 2100),   # Covers IDs 22543, 22773, 22775
        (2200, 2400),   # Covers IDs 23553, 23555, 23557, 23581, 23583, 23709, 23719
    ]
    
    for start_offset, end_offset in search_ranges:
        print(f"\n📋 Searching range {start_offset}-{end_offset}...")
        
        for offset in range(start_offset, end_offset, 100):
            try:
                result = await list_contacts(
                    context,
                    limit=100,
                    offset=offset
                )
                
                if result['count'] == 0:
                    continue
                
                # Get detailed information including custom fields
                details = await get_collection_details(
                    context,
                    result['collection_id'],
                    fields=["id", "given_name", "family_name", "email", "custom_fields", "date_created"]
                )
                
                contacts = details.get('contacts', [])
                
                for contact in contacts:
                    contact_id = contact.get('id')
                    if contact_id in SCOTT_HANAN_IDS:
                        scott_contacts.append(contact)
                        print(f"   ✅ Found: {contact.get('given_name')} {contact.get('family_name')} (ID: {contact_id})")
                
                # If we found all 10, we can stop
                if len(scott_contacts) >= 10:
                    break
            
            except Exception as e:
                print(f"   ❌ Error at offset {offset}: {e}")
                continue
        
        if len(scott_contacts) >= 10:
            break
    
    print(f"\n✅ Retrieved {len(scott_contacts)}/10 Scott Hanan contacts")
    return scott_contacts


def analyze_custom_fields_for_6fn(contacts):
    """Analyze custom fields for 6FN data and formatting variations"""
    print(f"\n📊 Analyzing custom fields for 6FN data across {len(contacts)} contacts...")
    
    all_6fn_data = []
    all_custom_fields = defaultdict(list)
    contacts_with_6fn = []
    
    for contact in contacts:
        contact_id = contact.get('id')
        given_name = contact.get('given_name', '')
        family_name = contact.get('family_name', '')
        email = contact.get('email', '')
        custom_fields = contact.get('custom_fields', [])
        
        print(f"\n👤 {given_name} {family_name} (ID: {contact_id})")
        print(f"   Email: {email}")
        print(f"   Custom fields: {len(custom_fields)}")
        
        if not custom_fields:
            print("   ❌ No custom fields")
            continue
        
        # Analyze each custom field
        fields_with_data = []
        fn_fields = []
        
        for field in custom_fields:
            field_id = field.get('id')
            field_content = field.get('content')
            field_type = field.get('type', 'unknown')
            
            # Track all fields with data
            if field_content is not None and str(field_content).strip():
                fields_with_data.append(field)
                all_custom_fields[field_id].append({
                    'contact_name': f"{given_name} {family_name}",
                    'contact_id': contact_id,
                    'content': field_content,
                    'type': field_type
                })
            
            # Check for 6FN patterns
            content_str = str(field_content).lower()
            if any(pattern in content_str for pattern in ['6fn', 'sixfn', 'six figure', 'figure number', '6-fn', 'six-figure']):
                fn_fields.append(field)
                all_6fn_data.append({
                    'contact_name': f"{given_name} {family_name}",
                    'contact_id': contact_id,
                    'email': email,
                    'field_id': field_id,
                    'field_type': field_type,
                    'content': field_content
                })
                print(f"   🎯 6FN FIELD {field_id} ({field_type}): {field_content}")
        
        print(f"   📋 Fields with data: {len(fields_with_data)}")
        print(f"   🔢 6FN fields: {len(fn_fields)}")
        
        if fn_fields:
            contacts_with_6fn.append({
                'contact': contact,
                '6fn_fields': fn_fields
            })
        
        # Show sample of non-empty fields (first 5)
        if fields_with_data:
            print("   📝 Sample fields with data:")
            for field in fields_with_data[:5]:
                content = str(field.get('content', ''))
                if len(content) < 100:
                    print(f"      Field {field.get('id')}: {content}")
                else:
                    print(f"      Field {field.get('id')}: {content[:97]}...")
    
    return all_6fn_data, all_custom_fields, contacts_with_6fn


def analyze_6fn_formatting_variations(fn_data):
    """Analyze 6FN data for formatting variations"""
    print(f"\n🔍 6FN FORMATTING VARIATION ANALYSIS")
    print("=" * 50)
    
    if not fn_data:
        print("❌ No 6FN data found to analyze")
        return
    
    print(f"✅ Found {len(fn_data)} 6FN field instances across contacts")
    
    # Group by field content to find variations
    content_groups = defaultdict(list)
    field_groups = defaultdict(list)
    
    for item in fn_data:
        content = str(item['content']).strip()
        field_id = item['field_id']
        
        content_groups[content].append(item)
        field_groups[field_id].append(item)
    
    print(f"\n📋 6FN Content Analysis:")
    print("-" * 30)
    
    for content, instances in content_groups.items():
        print(f"\n   Content: '{content}'")
        print(f"   Type: {instances[0]['field_type']}")
        print(f"   Found in {len(instances)} contacts:")
        
        for instance in instances:
            print(f"     - {instance['contact_name']} (Field {instance['field_id']})")
    
    print(f"\n📋 6FN Field Distribution:")
    print("-" * 30)
    
    for field_id, instances in field_groups.items():
        print(f"\n   Field {field_id}:")
        print(f"   Used by {len(instances)} contacts")
        
        # Show unique values for this field
        unique_values = list(set(str(item['content']) for item in instances))
        for value in unique_values:
            contacts_with_value = [item['contact_name'] for item in instances if str(item['content']) == value]
            print(f"     Value '{value}': {', '.join(contacts_with_value)}")
    
    # Look for formatting variations
    print(f"\n🔍 Formatting Variation Detection:")
    print("-" * 40)
    
    normalized_groups = defaultdict(list)
    
    for content in content_groups.keys():
        # Multiple normalization approaches
        normalizations = [
            content.lower().replace('-', '').replace('_', '').replace(' ', ''),
            content.lower().replace('-', ' ').replace('_', ' ').strip(),
            ''.join(c for c in content.lower() if c.isalnum()),
            re.sub(r'[^a-z0-9]', '', content.lower())
        ]
        
        for norm in normalizations:
            if '6fn' in norm or 'sixfn' in norm or 'figure' in norm:
                normalized_groups[norm].append(content)
    
    variations_found = False
    for normalized, originals in normalized_groups.items():
        unique_originals = list(set(originals))
        if len(unique_originals) > 1:
            variations_found = True
            print(f"\n   📝 Normalized '{normalized}' appears as:")
            for original in unique_originals:
                print(f"     - '{original}'")
                # Show which contacts use this variation
                contacts_using = [item['contact_name'] for item in fn_data if str(item['content']).strip() == original]
                print(f"       Used by: {', '.join(set(contacts_using))}")
    
    if not variations_found:
        print("   ✅ No formatting variations detected in 6FN data")
        print("   All 6FN fields use consistent formatting")
    
    return variations_found


def analyze_field_patterns(custom_fields):
    """Analyze patterns in custom field usage across contacts"""
    print(f"\n📊 Custom Field Patterns Analysis")
    print("=" * 40)
    
    # Fields that appear in multiple contacts
    multi_contact_fields = {fid: data for fid, data in custom_fields.items() if len(data) > 1}
    
    if multi_contact_fields:
        print(f"\n📋 Fields used by multiple contacts ({len(multi_contact_fields)} fields):")
        for field_id, instances in sorted(multi_contact_fields.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n   Field {field_id} (used by {len(instances)} contacts):")
            
            # Group by unique values
            value_groups = defaultdict(list)
            for instance in instances:
                value = str(instance['content'])
                value_groups[value].append(instance['contact_name'])
            
            for value, contacts in value_groups.items():
                if len(value) < 50:
                    print(f"     '{value}': {', '.join(contacts)}")
                else:
                    print(f"     '{value[:47]}...': {', '.join(contacts)}")
    
    # Look for potential business-related fields
    print(f"\n🔍 Potential Business/Network-Related Fields:")
    print("-" * 45)
    
    business_keywords = ['network', 'business', 'income', 'revenue', 'figure', 'amount', 'value', 'level', 'status', 'type', 'category']
    
    potential_fields = []
    for field_id, instances in custom_fields.items():
        for instance in instances:
            content = str(instance['content']).lower()
            if any(keyword in content for keyword in business_keywords):
                potential_fields.append((field_id, instance))
    
    if potential_fields:
        for field_id, instance in potential_fields[:20]:  # Show first 20
            print(f"   Field {field_id}: {instance['content']} ({instance['contact_name']})")
    else:
        print("   No obvious business-related fields found")


async def main():
    """Main execution function"""
    print("🚀 6FN Custom Field Analysis - Scott Hanan Contacts")
    print("=" * 60)
    
    try:
        # Get all Scott Hanan contacts with custom fields
        scott_contacts = await get_scott_hanan_contacts_with_custom_fields()
        
        if not scott_contacts:
            print("❌ Could not retrieve Scott Hanan contacts")
            return
        
        # Analyze custom fields for 6FN data
        fn_data, custom_fields, contacts_with_6fn = analyze_custom_fields_for_6fn(scott_contacts)
        
        # Analyze formatting variations
        variations_found = analyze_6fn_formatting_variations(fn_data)
        
        # Analyze field patterns
        analyze_field_patterns(custom_fields)
        
        # Summary
        print(f"\n" + "="*60)
        print(f"📊 FINAL SUMMARY")
        print(f"="*60)
        print(f"Scott Hanan contacts analyzed: {len(scott_contacts)}")
        print(f"Contacts with 6FN data: {len(contacts_with_6fn)}")
        print(f"Total 6FN field instances: {len(fn_data)}")
        print(f"Formatting variations detected: {'Yes' if variations_found else 'No'}")
        print(f"Total unique custom fields: {len(custom_fields)}")
        
        if fn_data:
            print(f"\n✅ 6FN data successfully found and analyzed!")
            print(f"   Ready to identify formatting inconsistencies")
        else:
            print(f"\n❌ No 6FN data found in custom fields")
            print(f"   May be stored under different field names or values")
        
        print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Get custom fields for Scott Hanan contacts to analyze 6FN data and formatting variations.
"""

import asyncio
import os
import json
from collections import defaultdict
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_collection_details


def extract_email(contact):
    """Extract email from contact properly"""
    if contact.get('email_addresses'):
        email_addresses = contact['email_addresses']
        if isinstance(email_addresses, list) and email_addresses:
            for email_obj in email_addresses:
                if isinstance(email_obj, dict) and email_obj.get('email'):
                    return email_obj['email']
    return contact.get('email', None)


async def get_scott_hanan_contacts():
    """Get the Scott Hanan contacts we found"""
    context = Context()
    
    print("🔍 Getting Scott Hanan contacts with full custom field data...")
    
    # Known Scott contact IDs from previous search
    scott_contact_ids = [22543, 22775, 22773, 22777]  # Scott Hanan, TestPT, TestMT, TestNoT
    
    scott_contacts = []
    
    # Search around the known IDs to get them
    for target_id in scott_contact_ids:
        print(f"\n📋 Looking for contact ID {target_id}...")
        
        # Try different offset ranges around the target ID
        found = False
        for offset in range(1900, 2100, 50):  # Search around where we found them
            try:
                result = await list_contacts(
                    context,
                    limit=50,
                    offset=offset
                )
                
                if result['count'] > 0:
                    details = await get_collection_details(
                        context,
                        result['collection_id'],
                        fields=["id", "given_name", "family_name", "email_addresses", "custom_fields", "date_created"]
                    )
                    
                    contacts = details.get('contacts', [])
                    
                    for contact in contacts:
                        if contact.get('id') == target_id:
                            scott_contacts.append(contact)
                            email = extract_email(contact)
                            print(f"   ✅ Found: {contact.get('given_name')} {contact.get('family_name')} - {email}")
                            found = True
                            break
                
                if found:
                    break
                    
            except Exception as e:
                continue
        
        if not found:
            print(f"   ❌ Could not retrieve contact {target_id}")
    
    return scott_contacts


def analyze_custom_fields_for_6fn(contacts):
    """Analyze custom fields for 6FN data and formatting variations"""
    print(f"\n📊 Analyzing custom fields for {len(contacts)} Scott contacts...")
    
    all_6fn_data = []
    custom_field_summary = defaultdict(list)
    
    for contact in contacts:
        contact_id = contact.get('id')
        given_name = contact.get('given_name', '')
        family_name = contact.get('family_name', '')
        email = extract_email(contact)
        custom_fields = contact.get('custom_fields', [])
        
        print(f"\n👤 {given_name} {family_name} (ID: {contact_id})")
        print(f"   Email: {email}")
        print(f"   Custom fields: {len(custom_fields)}")
        
        if not custom_fields:
            print("   ❌ No custom fields")
            continue
        
        # Check each custom field for 6FN data
        fields_with_data = []
        fn_fields = []
        
        for field in custom_fields:
            field_id = field.get('id')
            field_content = field.get('content')
            field_type = field.get('type', 'unknown')
            
            # Track all fields with data
            if field_content is not None and str(field_content).strip():
                fields_with_data.append(field)
                custom_field_summary[field_id].append({
                    'contact': f"{given_name} {family_name}",
                    'content': field_content,
                    'type': field_type
                })
            
            # Check for 6FN patterns
            content_str = str(field_content).lower()
            if any(pattern in content_str for pattern in ['6fn', 'sixfn', 'six figure', 'figure number', '6-fn']):
                fn_fields.append(field)
                all_6fn_data.append({
                    'contact_name': f"{given_name} {family_name}",
                    'contact_id': contact_id,
                    'email': email,
                    'field_id': field_id,
                    'field_type': field_type,
                    'content': field_content
                })
                print(f"   🎯 6FN FIELD {field_id}: {field_content}")
        
        print(f"   📋 Fields with data: {len(fields_with_data)}")
        print(f"   🔢 6FN fields: {len(fn_fields)}")
        
        # Show sample of non-empty fields
        if fields_with_data:
            print("   📝 Sample fields with data:")
            for field in fields_with_data[:10]:  # Show first 10
                content = str(field.get('content', ''))
                if len(content) < 100:
                    print(f"      Field {field.get('id')}: {content}")
                else:
                    print(f"      Field {field.get('id')}: {content[:97]}...")
    
    return all_6fn_data, custom_field_summary


def analyze_6fn_formatting_variations(fn_data):
    """Analyze 6FN data for formatting variations"""
    print(f"\n🔍 6FN Data Formatting Analysis")
    print("=" * 40)
    
    if not fn_data:
        print("❌ No 6FN data found to analyze")
        return
    
    print(f"✅ Found {len(fn_data)} 6FN field instances")
    
    # Group by field content to find variations
    content_groups = defaultdict(list)
    
    for item in fn_data:
        content = str(item['content']).strip()
        content_groups[content].append(item)
    
    print(f"\n📋 6FN Field Contents:")
    for content, instances in content_groups.items():
        print(f"\n   Content: '{content}'")
        print(f"   Type: {instances[0]['field_type']}")
        print(f"   Found in {len(instances)} instances:")
        
        for instance in instances:
            print(f"     - {instance['contact_name']} (Field {instance['field_id']})")
    
    # Look for formatting variations
    print(f"\n🔍 Formatting Variation Analysis:")
    
    normalized_groups = defaultdict(list)
    
    for content in content_groups.keys():
        # Multiple normalization approaches
        normalizations = [
            content.lower().replace('-', '').replace('_', '').replace(' ', ''),
            content.lower().replace('-', ' ').replace('_', ' ').strip(),
            ''.join(c for c in content.lower() if c.isalnum())
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
    
    if not variations_found:
        print("   ✅ No formatting variations detected in 6FN data")
        print("   (All 6FN fields use consistent formatting)")


def show_custom_field_overview(field_summary):
    """Show overview of all custom fields across Scott contacts"""
    print(f"\n📊 Custom Field Overview Across Scott Contacts")
    print("=" * 50)
    
    # Show fields that appear in multiple contacts
    multi_contact_fields = {fid: data for fid, data in field_summary.items() if len(data) > 1}
    
    if multi_contact_fields:
        print(f"\n📋 Fields appearing in multiple Scott contacts:")
        for field_id, instances in multi_contact_fields.items():
            print(f"\n   Field {field_id} (appears in {len(instances)} contacts):")
            for instance in instances:
                content = str(instance['content'])
                if len(content) < 50:
                    print(f"     {instance['contact']}: {content}")
                else:
                    print(f"     {instance['contact']}: {content[:47]}...")
    
    # Show unique fields per contact
    print(f"\n📋 Total unique custom fields found: {len(field_summary)}")
    
    # Look for any field names or patterns that might indicate 6FN
    potential_6fn_fields = []
    for field_id, instances in field_summary.items():
        # Check if field ID or content suggests 6FN relationship
        for instance in instances:
            content = str(instance['content']).lower()
            if any(pattern in content for pattern in ['network', 'figure', 'income', 'business', 'mlm', 'affiliate']):
                potential_6fn_fields.append((field_id, instance))
    
    if potential_6fn_fields:
        print(f"\n🔍 Potentially related fields (network/business/income):")
        for field_id, instance in potential_6fn_fields[:10]:  # Show first 10
            print(f"   Field {field_id}: {instance['content']} ({instance['contact']})")


async def main():
    """Main execution function"""
    print("🚀 Scott Hanan Custom Field Analysis for 6FN Data")
    print("=" * 55)
    
    try:
        # Get Scott Hanan contacts with full custom field data
        scott_contacts = await get_scott_hanan_contacts()
        
        if not scott_contacts:
            print("❌ Could not retrieve Scott contacts")
            return
        
        # Analyze custom fields for 6FN data
        fn_data, field_summary = analyze_custom_fields_for_6fn(scott_contacts)
        
        # Analyze formatting variations
        analyze_6fn_formatting_variations(fn_data)
        
        # Show custom field overview
        show_custom_field_overview(field_summary)
        
        print(f"\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
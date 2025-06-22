#!/usr/bin/env python3
"""
Fixed search script using offset-based pagination to find Scott Hanan and 6FN data.
"""

import asyncio
import os
import re
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_collection_details


async def search_with_offset_pagination():
    """Search using offset pagination since regular retrieval seems to have issues"""
    context = Context()
    
    print("🔍 Searching with offset pagination...")
    
    found_scott_hanan = []
    found_smhanan_emails = []
    found_6fn_data = []
    
    batch_size = 50
    max_offset = 1000  # Search through up to 1000 contacts
    
    for offset in range(0, max_offset, batch_size):
        try:
            print(f"📋 Checking contacts {offset}-{offset+batch_size-1}...")
            
            # Get batch with offset
            result = await list_contacts(
                context,
                limit=batch_size,
                offset=offset
            )
            
            if result['count'] == 0:
                print(f"   No contacts at offset {offset}")
                continue
            
            # Get details
            details = await get_collection_details(
                context,
                result['collection_id'],
                fields=["id", "given_name", "family_name", "email", "custom_fields"]
            )
            
            contacts = details.get('contacts', [])
            print(f"   Retrieved {len(contacts)} contact details")
            
            if not contacts:
                continue
            
            # Search this batch
            for contact in contacts:
                contact_id = contact.get('id')
                given_name = contact.get('given_name', '').lower()
                family_name = contact.get('family_name', '').lower()
                email = contact.get('email', '').lower()
                custom_fields = contact.get('custom_fields', [])
                
                # Check for Scott Hanan
                if 'scott' in given_name or 'hanan' in family_name:
                    found_scott_hanan.append(contact)
                    print(f"   🎯 SCOTT/HANAN: {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
                
                # Check for smhanan emails
                if 'smhanan' in email:
                    found_smhanan_emails.append(contact)
                    print(f"   📧 SMHANAN EMAIL: {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
                
                # Check custom fields for 6FN
                for field in custom_fields:
                    field_content = str(field.get('content', '')).lower()
                    field_id = field.get('id')
                    
                    if ('6fn' in field_content or 'sixfn' in field_content or 
                        'six figure' in field_content or 'figure number' in field_content):
                        found_6fn_data.append({
                            'contact': contact,
                            'field_id': field_id,
                            'content': field.get('content', ''),
                            'field_type': field.get('type', 'unknown')
                        })
                        print(f"   🔢 6FN DATA: {contact.get('given_name', '')} {contact.get('family_name', '')} - Field {field_id}: {field.get('content', '')}")
            
        except Exception as e:
            print(f"   ❌ Error at offset {offset}: {e}")
            continue
    
    return found_scott_hanan, found_smhanan_emails, found_6fn_data


async def analyze_found_data(scott_hanan, smhanan_emails, fn_data):
    """Analyze the found data for formatting variations"""
    print("\n" + "="*60)
    print("📊 ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\n👤 SCOTT HANAN CONTACTS FOUND: {len(scott_hanan)}")
    for contact in scott_hanan:
        print(f"   Name: {contact.get('given_name', '')} {contact.get('family_name', '')}")
        print(f"   Email: {contact.get('email', '')}")
        print(f"   ID: {contact.get('id', '')}")
        
        # Show custom fields with data
        custom_fields = contact.get('custom_fields', [])
        non_empty_fields = [f for f in custom_fields if f.get('content')]
        
        if non_empty_fields:
            print(f"   Custom fields with data: {len(non_empty_fields)}")
            for field in non_empty_fields[:10]:  # Show first 10
                content = field.get('content', '')
                if len(str(content)) < 100:  # Only show short values
                    print(f"     Field {field.get('id')}: {content}")
        print()
    
    print(f"\n📧 SMHANAN EMAIL CONTACTS FOUND: {len(smhanan_emails)}")
    for contact in smhanan_emails:
        print(f"   Name: {contact.get('given_name', '')} {contact.get('family_name', '')}")
        print(f"   Email: {contact.get('email', '')}")
        print(f"   ID: {contact.get('id', '')}")
        print()
    
    print(f"\n🔢 6FN CUSTOM FIELD DATA FOUND: {len(fn_data)}")
    if fn_data:
        # Group by field content to find variations
        content_variations = {}
        
        for item in fn_data:
            content = str(item['content']).strip()
            contact = item['contact']
            field_id = item['field_id']
            
            if content not in content_variations:
                content_variations[content] = []
            
            content_variations[content].append({
                'contact_name': f"{contact.get('given_name', '')} {contact.get('family_name', '')}",
                'contact_id': contact.get('id', ''),
                'field_id': field_id,
                'field_type': item['field_type']
            })
        
        print("   📝 Content variations found:")
        for content, instances in content_variations.items():
            print(f"\n   Content: '{content}'")
            print(f"   Found in {len(instances)} instances:")
            for instance in instances:
                print(f"     - {instance['contact_name']} (ID: {instance['contact_id']}) - Field {instance['field_id']}")
        
        # Look for formatting variations
        print(f"\n🔍 FORMATTING VARIATION ANALYSIS:")
        normalized_groups = {}
        
        for content in content_variations.keys():
            # Normalize content for comparison
            normalized = re.sub(r'[^a-z0-9]', '', content.lower())
            
            if normalized not in normalized_groups:
                normalized_groups[normalized] = []
            normalized_groups[normalized].append(content)
        
        variations_found = False
        for normalized, originals in normalized_groups.items():
            if len(set(originals)) > 1:
                variations_found = True
                print(f"\n   📋 Normalized '{normalized}' appears as:")
                for original in set(originals):
                    print(f"     - '{original}'")
        
        if not variations_found:
            print("   ✅ No formatting variations detected in 6FN data")
    
    else:
        print("   ❌ No 6FN data found in custom fields")


async def main():
    """Main execution function"""
    print("🚀 Fixed Search for Scott Hanan & 6FN Data")
    print("=" * 50)
    print("Using offset pagination to bypass API search issues...")
    print()
    
    try:
        # Search with pagination
        scott_hanan, smhanan_emails, fn_data = await search_with_offset_pagination()
        
        # Analyze results
        await analyze_found_data(scott_hanan, smhanan_emails, fn_data)
        
        print("\n✅ Search complete!")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
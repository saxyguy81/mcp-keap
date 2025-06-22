#!/usr/bin/env python3
"""
Comprehensive search script to find Scott Hanan contacts and 6FN data.
Uses multiple search strategies since standard filtering may not be working properly.
"""

import asyncio
import os
import json
import re
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


async def exhaustive_contact_search():
    """Search through all contacts exhaustively"""
    context = Context()
    
    print("🔍 Performing exhaustive contact search...")
    print("This will search through all available contacts to find Scott Hanan and 6FN data")
    
    all_contacts = []
    offset = 0
    batch_size = 50
    
    while True:
        try:
            print(f"📋 Fetching contacts {offset}-{offset+batch_size}...")
            
            # Get contacts in batches
            batch_result = await list_contacts(
                context, 
                limit=batch_size, 
                offset=offset
            )
            
            if batch_result['count'] == 0:
                print(f"   No more contacts found at offset {offset}")
                break
            
            # Get detailed information for this batch
            details = await get_collection_details(
                context, 
                batch_result['collection_id'],
                fields=["id", "given_name", "family_name", "email", "custom_fields"]
            )
            
            print(f"   Retrieved {len(details['contacts'])} contacts")
            all_contacts.extend(details['contacts'])
            
            # Move to next batch
            offset += batch_size
            
            # Safety limit to prevent infinite loops
            if offset >= 1000:
                print("   Reached safety limit of 1000 contacts")
                break
                
        except Exception as e:
            print(f"   ❌ Error fetching batch at offset {offset}: {e}")
            break
    
    print(f"✅ Total contacts retrieved: {len(all_contacts)}")
    return all_contacts


def search_for_scott_hanan(contacts):
    """Search for Scott Hanan contacts in the retrieved data"""
    print("\n🎯 Searching for Scott Hanan contacts...")
    
    scott_hanan_matches = []
    smhanan_email_matches = []
    
    for contact in contacts:
        contact_id = contact.get('id')
        given_name = contact.get('given_name', '')
        family_name = contact.get('family_name', '')
        email = contact.get('email', '')
        
        # Search patterns
        given_lower = given_name.lower() if given_name else ''
        family_lower = family_name.lower() if family_name else ''
        email_lower = email.lower() if email else ''
        
        # Check for Scott Hanan name patterns
        is_scott = 'scott' in given_lower
        is_hanan = 'hanan' in family_lower
        
        if is_scott or is_hanan:
            scott_hanan_matches.append({
                'contact': contact,
                'match_reason': f"Name: {given_name} {family_name}",
                'is_scott': is_scott,
                'is_hanan': is_hanan
            })
        
        # Check for smhanan email patterns
        if 'smhanan' in email_lower:
            smhanan_email_matches.append({
                'contact': contact,
                'match_reason': f"Email: {email}"
            })
    
    print(f"📧 Found {len(smhanan_email_matches)} contacts with 'smhanan' email pattern")
    for match in smhanan_email_matches:
        contact = match['contact']
        print(f"   👤 {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
    
    print(f"👤 Found {len(scott_hanan_matches)} contacts with Scott/Hanan name patterns")
    for match in scott_hanan_matches:
        contact = match['contact']
        print(f"   👤 {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
    
    return smhanan_email_matches + scott_hanan_matches


def search_for_6fn_in_custom_fields(contacts):
    """Search for 6FN in custom field names and values"""
    print("\n🔍 Searching for 6FN in custom fields...")
    
    fn_field_names = set()
    fn_field_values = []
    contacts_with_6fn = []
    
    for contact in contacts:
        contact_id = contact.get('id')
        given_name = contact.get('given_name', '')
        family_name = contact.get('family_name', '')
        email = contact.get('email', '')
        custom_fields = contact.get('custom_fields', [])
        
        contact_has_6fn = False
        contact_6fn_data = []
        
        for field in custom_fields:
            field_id = field.get('id')
            field_content = field.get('content', '')
            field_type = field.get('type', 'unknown')
            
            # Check field content for 6FN patterns
            content_str = str(field_content).lower()
            patterns = ['6fn', '6-fn', 'sixfn', 'six.*fn', 'figure.*number']
            
            for pattern in patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    fn_field_values.append({
                        'contact_id': contact_id,
                        'contact_name': f"{given_name} {family_name}",
                        'field_id': field_id,
                        'field_type': field_type,
                        'content': field_content,
                        'pattern': pattern
                    })
                    contact_6fn_data.append(field)
                    contact_has_6fn = True
                    break
        
        if contact_has_6fn:
            contacts_with_6fn.append({
                'contact': contact,
                '6fn_fields': contact_6fn_data
            })
    
    print(f"📊 Found {len(fn_field_values)} custom field values containing 6FN patterns")
    print(f"👥 Found {len(contacts_with_6fn)} contacts with 6FN data")
    
    if fn_field_values:
        print("\n🎯 6FN Field Data:")
        for item in fn_field_values:
            print(f"   Contact: {item['contact_name']} (ID: {item['contact_id']})")
            print(f"   Field {item['field_id']} ({item['field_type']}): {item['content']}")
            print(f"   Pattern: {item['pattern']}")
            print()
    
    return contacts_with_6fn, fn_field_values


def analyze_custom_field_structure(contacts):
    """Analyze the structure of custom fields to understand field naming"""
    print("\n🔧 Analyzing custom field structure...")
    
    field_ids_found = set()
    field_types_found = defaultdict(int)
    non_empty_fields = defaultdict(list)
    
    for contact in contacts[:10]:  # Sample first 10 contacts
        custom_fields = contact.get('custom_fields', [])
        
        for field in custom_fields:
            field_id = field.get('id')
            field_content = field.get('content')
            field_type = field.get('type', 'unknown')
            
            field_ids_found.add(field_id)
            field_types_found[field_type] += 1
            
            if field_content is not None and str(field_content).strip():
                non_empty_fields[field_id].append(field_content)
    
    print(f"📋 Found {len(field_ids_found)} unique custom field IDs")
    print(f"📊 Field types distribution: {dict(field_types_found)}")
    
    print(f"\n📝 Non-empty custom fields (sample):")
    for field_id, values in list(non_empty_fields.items())[:20]:  # Show first 20
        unique_values = list(set(str(v) for v in values))[:3]  # Show up to 3 unique values
        print(f"   Field {field_id}: {unique_values}")


async def main():
    """Main execution function"""
    print("🚀 Comprehensive Scott Hanan & 6FN Search")
    print("=" * 45)
    print("This script will exhaustively search all contacts for:")
    print("- Scott Hanan name patterns")
    print("- Email addresses starting with 'smhanan'") 
    print("- Custom fields containing '6FN' or similar patterns")
    print()
    
    try:
        # Get all contacts
        all_contacts = await exhaustive_contact_search()
        
        if not all_contacts:
            print("❌ No contacts retrieved - API may not be working properly")
            return
        
        # Search for Scott Hanan
        hanan_matches = search_for_scott_hanan(all_contacts)
        
        # Search for 6FN data
        fn_contacts, fn_fields = search_for_6fn_in_custom_fields(all_contacts)
        
        # Analyze field structure
        analyze_custom_field_structure(all_contacts)
        
        print("\n" + "="*50)
        print("📊 SUMMARY")
        print("="*50)
        print(f"Total contacts analyzed: {len(all_contacts)}")
        print(f"Scott Hanan / smhanan matches: {len(hanan_matches)}")
        print(f"Contacts with 6FN data: {len(fn_contacts)}")
        print(f"6FN field instances: {len(fn_fields)}")
        
        if hanan_matches:
            print(f"\n🎯 SCOTT HANAN CONTACTS FOUND:")
            for match in hanan_matches:
                contact = match['contact']
                print(f"   {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
                
                # Show custom fields for Scott Hanan contacts
                custom_fields = contact.get('custom_fields', [])
                non_empty_fields = [f for f in custom_fields if f.get('content')]
                if non_empty_fields:
                    print(f"     Custom fields with data: {len(non_empty_fields)}")
                    for field in non_empty_fields[:5]:  # Show first 5
                        print(f"       Field {field.get('id')}: {field.get('content')}")
                print()
        
        print("\n✅ Comprehensive search complete!")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
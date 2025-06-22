#!/usr/bin/env python3
"""
Comprehensive search for Scott Hanan contacts with proper email extraction.
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


def extract_email(contact):
    """Extract email from contact with all possible formats"""
    emails = []
    
    # Method 1: Direct email field
    if contact.get('email'):
        emails.append(contact['email'])
    
    # Method 2: email_addresses array
    if contact.get('email_addresses'):
        email_addresses = contact['email_addresses']
        if isinstance(email_addresses, list):
            for email_obj in email_addresses:
                if isinstance(email_obj, dict):
                    if email_obj.get('email'):
                        emails.append(email_obj['email'])
                    if email_obj.get('address'):
                        emails.append(email_obj['address'])
                elif isinstance(email_obj, str):
                    emails.append(email_obj)
    
    # Method 3: Other possible email fields
    for field in ['email_address', 'primary_email', 'main_email']:
        if contact.get(field):
            emails.append(contact[field])
    
    # Clean up emails - remove mailto: prefix if present
    clean_emails = []
    for email in emails:
        if email:
            email_str = str(email).strip()
            if email_str.startswith('mailto:'):
                email_str = email_str[7:]  # Remove 'mailto:' prefix
            if email_str and '@' in email_str:
                clean_emails.append(email_str)
    
    return clean_emails[0] if clean_emails else None


async def search_all_contacts_for_hanan():
    """Search through ALL contacts for Hanan/Scott patterns"""
    context = Context()
    
    print("🔍 Comprehensive search for Scott Hanan contacts...")
    print("This will search through ALL contacts in the account")
    
    found_contacts = []
    batch_size = 100
    offset = 0
    total_checked = 0
    
    while True:
        try:
            print(f"\n📋 Searching batch {offset//batch_size + 1} (contacts {offset+1}-{offset+batch_size})...")
            
            # Get batch of contacts
            result = await list_contacts(
                context,
                limit=batch_size,
                offset=offset
            )
            
            if result['count'] == 0:
                print(f"   No more contacts found. Searched {total_checked} total contacts.")
                break
            
            # Get detailed information
            details = await get_collection_details(
                context,
                result['collection_id'],
                fields=["id", "given_name", "family_name", "email", "email_addresses", "date_created"]
            )
            
            contacts = details.get('contacts', [])
            
            if not contacts:
                print(f"   No contact details retrieved for this batch")
                offset += batch_size
                continue
            
            print(f"   Checking {len(contacts)} contacts...")
            total_checked += len(contacts)
            
            # Search each contact
            batch_matches = 0
            for contact in contacts:
                given_name = contact.get('given_name', '').lower()
                family_name = contact.get('family_name', '').lower()
                email = extract_email(contact)
                
                # Search criteria
                is_scott = 'scott' in given_name
                is_hanan = 'hanan' in family_name
                has_smhanan = email and 'smhanan' in email.lower()
                
                if is_scott or is_hanan or has_smhanan:
                    found_contacts.append({
                        'contact': contact,
                        'email': email,
                        'match_reason': {
                            'scott': is_scott,
                            'hanan': is_hanan, 
                            'smhanan_email': has_smhanan
                        }
                    })
                    batch_matches += 1
                    
                    print(f"   🎯 MATCH: {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
                    print(f"       Reasons: Scott={is_scott}, Hanan={is_hanan}, smhanan_email={has_smhanan}")
            
            print(f"   Found {batch_matches} matches in this batch")
            
            # Move to next batch
            offset += batch_size
            
            # Safety limit
            if offset >= 2000:
                print(f"   Reached safety limit at {offset} contacts")
                break
                
        except Exception as e:
            print(f"   ❌ Error in batch starting at {offset}: {e}")
            offset += batch_size
            continue
    
    return found_contacts


async def search_with_filters():
    """Try searching with specific filters"""
    context = Context()
    
    print(f"\n🔍 Trying filtered searches...")
    
    search_attempts = [
        ("Family name contains 'Hanan'", [{"field": "family_name", "operator": "contains", "value": "Hanan"}]),
        ("Family name contains 'hanan'", [{"field": "family_name", "operator": "contains", "value": "hanan"}]),
        ("Given name contains 'Scott'", [{"field": "given_name", "operator": "contains", "value": "Scott"}]),
        ("Given name contains 'scott'", [{"field": "given_name", "operator": "contains", "value": "scott"}]),
        ("Email contains 'smhanan'", [{"field": "email", "operator": "contains", "value": "smhanan"}]),
        ("Family name equals 'Hanan'", [{"field": "family_name", "operator": "equals", "value": "Hanan"}]),
    ]
    
    for description, filters in search_attempts:
        try:
            print(f"\n   🔎 {description}")
            
            result = await list_contacts(
                context,
                filters=filters,
                limit=50
            )
            
            print(f"       Found {result['count']} contacts")
            
            if result['count'] > 0:
                details = await get_collection_details(
                    context,
                    result['collection_id'],
                    fields=["id", "given_name", "family_name", "email", "email_addresses"]
                )
                
                contacts = details.get('contacts', [])
                
                for contact in contacts:
                    email = extract_email(contact)
                    print(f"       📧 {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
            
        except Exception as e:
            print(f"       ❌ Failed: {e}")


async def check_email_extraction_methods():
    """Debug email extraction on recent contacts"""
    context = Context()
    
    print(f"\n🔧 Debugging email extraction methods...")
    
    # Get a few recent contacts to test email extraction
    result = await list_contacts(context, limit=3)
    
    if result['count'] > 0:
        details = await get_collection_details(
            context,
            result['collection_id'],
            fields=["id", "given_name", "family_name", "email", "email_addresses"]
        )
        
        contacts = details.get('contacts', [])
        
        for i, contact in enumerate(contacts, 1):
            print(f"\n   Contact {i}: {contact.get('given_name', '')} {contact.get('family_name', '')}")
            
            # Show all possible email fields
            print(f"       Raw email field: {contact.get('email')}")
            print(f"       Email_addresses field: {contact.get('email_addresses')}")
            
            # Show extracted email
            extracted = extract_email(contact)
            print(f"       Extracted email: {extracted}")
            
            # Show all keys for debugging
            print(f"       All contact keys: {list(contact.keys())}")


async def main():
    """Main execution function"""
    print("🚀 Comprehensive Scott Hanan Search")
    print("=" * 40)
    
    try:
        # Debug email extraction first
        await check_email_extraction_methods()
        
        # Try filtered searches
        await search_with_filters()
        
        # Comprehensive search through all contacts
        found_contacts = await search_all_contacts_for_hanan()
        
        # Summary
        print(f"\n" + "="*60)
        print(f"📊 SEARCH RESULTS SUMMARY")
        print(f"="*60)
        print(f"Total Scott/Hanan contacts found: {len(found_contacts)}")
        
        if found_contacts:
            print(f"\n🎯 FOUND CONTACTS:")
            for i, match in enumerate(found_contacts, 1):
                contact = match['contact']
                email = match['email']
                reasons = match['match_reason']
                
                print(f"\n{i}. {contact.get('given_name', '')} {contact.get('family_name', '')}")
                print(f"   Email: {email}")
                print(f"   ID: {contact.get('id')}")
                print(f"   Created: {contact.get('date_created', 'N/A')}")
                print(f"   Match reasons: {reasons}")
        else:
            print(f"\n❌ No Scott Hanan contacts found in the search")
            print(f"   This could mean:")
            print(f"   1. The contacts don't exist in this account")
            print(f"   2. They have different name spellings")
            print(f"   3. They are archived or deleted")
            print(f"   4. There's still an issue with the search method")
        
        print(f"\n✅ Comprehensive search complete!")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
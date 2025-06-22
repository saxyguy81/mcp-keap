#!/usr/bin/env python3
"""
Simple diagnostic script to check what contacts exist in the system.
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

from src.mcp.tools_collections import list_contacts, get_collection_details


async def check_contacts():
    """Check what contacts exist in the system"""
    context = Context()
    
    print("🔍 Basic contact system check...")
    
    # Get a small sample of contacts
    contacts_result = await list_contacts(context, limit=10)
    print(f"Total contacts found: {contacts_result['count']}")
    
    if contacts_result['count'] == 0:
        print("❌ No contacts found in the system")
        return
    
    # Get detailed information
    details = await get_collection_details(
        context, 
        contacts_result['collection_id'],
        fields=["id", "given_name", "family_name", "email"]
    )
    
    print(f"\nFirst {len(details['contacts'])} contacts:")
    print("-" * 40)
    
    for i, contact in enumerate(details['contacts'][:10], 1):
        given_name = contact.get('given_name', 'N/A')
        family_name = contact.get('family_name', 'N/A') 
        email = contact.get('email', 'N/A')
        contact_id = contact.get('id', 'N/A')
        
        print(f"{i:2d}. {given_name} {family_name}")
        print(f"    ID: {contact_id}")
        print(f"    Email: {email}")
        print()
    
    # Check custom fields on one contact
    if details['contacts']:
        first_contact = details['contacts'][0]
        contact_id = first_contact['id']
        
        print(f"📋 Checking custom fields for contact {contact_id}...")
        
        detailed_contact = await get_collection_details(
            context,
            contacts_result['collection_id'],
            fields=["id", "given_name", "family_name", "email", "custom_fields"]
        )
        
        if detailed_contact['contacts']:
            custom_fields = detailed_contact['contacts'][0].get('custom_fields', [])
            
            if custom_fields:
                print(f"Found {len(custom_fields)} custom fields")
                print("Sample custom fields (first 5):")
                for i, field in enumerate(custom_fields[:5]):
                    field_id = field.get('id')
                    content = field.get('content', '')
                    field_type = field.get('type', 'unknown')
                    print(f"  Field {field_id} ({field_type}): {content}")
            else:
                print("No custom fields found")


async def search_by_family_name():
    """Try searching by family name with common patterns"""
    context = Context()
    
    print("\n🔍 Searching by family name patterns...")
    
    # Get all contacts and check family names
    contacts_result = await list_contacts(context, limit=50)
    
    if contacts_result['count'] == 0:
        print("No contacts to search")
        return
    
    details = await get_collection_details(
        context, 
        contacts_result['collection_id'],
        fields=["id", "given_name", "family_name", "email"]
    )
    
    print(f"Checking {len(details['contacts'])} contacts for name patterns...")
    
    name_patterns = ['han', 'scott', 'hana', 'anan']
    
    for pattern in name_patterns:
        print(f"\n🔎 Looking for '{pattern}' in names:")
        found_any = False
        
        for contact in details['contacts']:
            given_name = contact.get('given_name', '').lower()
            family_name = contact.get('family_name', '').lower()
            
            if pattern in given_name or pattern in family_name:
                found_any = True
                print(f"   ✅ {contact.get('given_name', '')} {contact.get('family_name', '')} (ID: {contact.get('id')})")
        
        if not found_any:
            print(f"   ❌ No matches for '{pattern}'")


async def main():
    """Main execution function"""
    print("🚀 Simple Contact System Diagnostic")
    print("=" * 38)
    
    try:
        await check_contacts()
        await search_by_family_name()
        
        print("\n✅ Diagnostic complete!")
        
    except Exception as e:
        print(f"❌ Error during diagnostic: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
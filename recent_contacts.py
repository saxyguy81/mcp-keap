#!/usr/bin/env python3
"""
Get the 10 most recently added contacts from the Keap account.
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


async def get_recent_contacts():
    """Get the most recently added contacts"""
    context = Context()
    
    print("🔍 Getting 10 most recently added contacts...")
    
    try:
        # Get contacts ordered by creation date (most recent first)
        result = await list_contacts(
            context,
            limit=10,
            order_by="date_created", 
            order_direction="DESC"
        )
        
        print(f"Found {result['count']} contacts")
        
        if result['count'] == 0:
            print("❌ No contacts found")
            return
        
        # Get detailed information
        details = await get_collection_details(
            context,
            result['collection_id'],
            fields=["id", "given_name", "family_name", "email", "date_created", "email_addresses"]
        )
        
        contacts = details.get('contacts', [])
        
        if not contacts:
            print("❌ No contact details retrieved")
            return
        
        print(f"\n📋 {len(contacts)} Most Recently Added Contacts:")
        print("=" * 60)
        
        for i, contact in enumerate(contacts, 1):
            contact_id = contact.get('id', 'N/A')
            given_name = contact.get('given_name', '')
            family_name = contact.get('family_name', '')
            date_created = contact.get('date_created', 'N/A')
            
            # Get email - try different fields
            email = contact.get('email', '')
            if not email:
                # Try email_addresses array
                email_addresses = contact.get('email_addresses', [])
                if isinstance(email_addresses, list) and email_addresses:
                    if isinstance(email_addresses[0], dict):
                        email = email_addresses[0].get('email', '')
                    else:
                        email = str(email_addresses[0])
            
            # Format name
            full_name = f"{given_name} {family_name}".strip()
            if not full_name:
                full_name = "No name"
            
            print(f"{i:2d}. {full_name}")
            print(f"    Email: {email if email else 'No email'}")
            print(f"    ID: {contact_id}")
            print(f"    Created: {date_created}")
            print()
        
    except Exception as e:
        print(f"❌ Error getting recent contacts: {e}")
        import traceback
        traceback.print_exc()


async def get_contacts_with_different_sorting():
    """Try different sorting approaches to get recent contacts"""
    context = Context()
    
    print("\n🔍 Trying alternative approaches to get recent contacts...")
    
    sorting_approaches = [
        ("ID descending", "id", "DESC"),
        ("Last updated", "last_updated", "DESC"), 
        ("ID ascending", "id", "ASC"),
        ("Given name", "given_name", "ASC"),
    ]
    
    for approach_name, order_field, direction in sorting_approaches:
        try:
            print(f"\n📋 Approach: {approach_name} ({order_field} {direction})")
            
            result = await list_contacts(
                context,
                limit=5,
                order_by=order_field,
                order_direction=direction
            )
            
            if result['count'] > 0:
                details = await get_collection_details(
                    context,
                    result['collection_id'],
                    fields=["id", "given_name", "family_name", "email", "date_created"]
                )
                
                contacts = details.get('contacts', [])
                print(f"   Retrieved {len(contacts)} contacts")
                
                for contact in contacts:
                    given_name = contact.get('given_name', '')
                    family_name = contact.get('family_name', '')
                    email = contact.get('email', 'No email')
                    contact_id = contact.get('id', 'N/A')
                    date_created = contact.get('date_created', 'N/A')
                    
                    full_name = f"{given_name} {family_name}".strip() or "No name"
                    print(f"   - {full_name} ({email}) - ID: {contact_id} - Created: {date_created}")
            else:
                print(f"   No contacts returned")
                
        except Exception as e:
            print(f"   ❌ {approach_name} failed: {e}")


async def get_contacts_by_batches():
    """Get contacts in different batches to see variety"""
    context = Context()
    
    print("\n🔍 Getting contacts from different batches...")
    
    batches = [
        (0, "First 5 contacts"),
        (10, "Contacts 11-15"),
        (50, "Contacts 51-55"),
        (100, "Contacts 101-105"),
    ]
    
    for offset, description in batches:
        try:
            print(f"\n📋 {description} (offset {offset})")
            
            result = await list_contacts(
                context,
                limit=5,
                offset=offset
            )
            
            if result['count'] > 0:
                details = await get_collection_details(
                    context,
                    result['collection_id'], 
                    fields=["id", "given_name", "family_name", "email"]
                )
                
                contacts = details.get('contacts', [])
                
                for contact in contacts:
                    given_name = contact.get('given_name', '')
                    family_name = contact.get('family_name', '')
                    email = contact.get('email', 'No email')
                    contact_id = contact.get('id', 'N/A')
                    
                    full_name = f"{given_name} {family_name}".strip() or "No name"
                    print(f"   - {full_name} ({email}) - ID: {contact_id}")
            else:
                print(f"   No contacts at offset {offset}")
                
        except Exception as e:
            print(f"   ❌ Batch at offset {offset} failed: {e}")


async def main():
    """Main execution function"""
    print("🚀 Recent Contacts Retrieval")
    print("=" * 30)
    
    try:
        # Try to get recent contacts
        await get_recent_contacts()
        
        # Try different sorting approaches
        await get_contacts_with_different_sorting()
        
        # Try different batches
        await get_contacts_by_batches()
        
        print("\n✅ Contact retrieval complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
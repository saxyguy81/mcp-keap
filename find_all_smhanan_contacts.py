#!/usr/bin/env python3
"""
Comprehensive search to find ALL 10 smhanan contacts with improved search strategy.
"""

import asyncio
import os
import time
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_collection_details


def extract_email(contact):
    """Extract email using the same logic as the fixed MCP tools"""
    # Method 1: email_addresses array (primary source)
    if contact.get('email_addresses'):
        email_addresses = contact['email_addresses']
        if isinstance(email_addresses, list) and email_addresses:
            for email_obj in email_addresses:
                if isinstance(email_obj, dict) and email_obj.get('email'):
                    email = email_obj['email']
                    # Remove mailto: prefix if present
                    if email.startswith('mailto:'):
                        email = email[7:]
                    return email
    
    # Method 2: Direct email field (fallback)
    email = contact.get('email')
    if email:
        if email.startswith('mailto:'):
            email = email[7:]
        return email
    
    return None


async def comprehensive_smhanan_search():
    """Search for ALL smhanan contacts without artificial limits"""
    context = Context()
    
    print("🔍 Comprehensive search for ALL smhanan contacts...")
    print("Removing 2000 contact limit to find all 10 contacts")
    
    found_smhanan = []
    found_scott_hanan = []
    batch_size = 100
    offset = 0
    total_searched = 0
    consecutive_empty_batches = 0
    max_empty_batches = 5  # Stop after 5 consecutive empty batches
    
    while consecutive_empty_batches < max_empty_batches:
        try:
            print(f"\n📋 Batch {offset//batch_size + 1}: Searching contacts {offset+1}-{offset+batch_size}...")
            
            # Get batch with rate limit consideration
            start_time = time.time()
            
            result = await list_contacts(
                context,
                limit=batch_size,
                offset=offset
            )
            
            if result['count'] == 0:
                consecutive_empty_batches += 1
                print(f"   Empty batch {consecutive_empty_batches}/{max_empty_batches}")
                offset += batch_size
                continue
            else:
                consecutive_empty_batches = 0  # Reset counter
            
            # Get contact details with email extraction
            details = await get_collection_details(
                context,
                result['collection_id'],
                fields=["id", "given_name", "family_name", "email", "email_addresses", "date_created"]
            )
            
            contacts = details.get('contacts', [])
            
            if not contacts:
                print(f"   No contact details retrieved")
                offset += batch_size
                continue
            
            batch_time = time.time() - start_time
            print(f"   Retrieved {len(contacts)} contacts in {batch_time:.1f}s")
            total_searched += len(contacts)
            
            # Search this batch
            batch_smhanan = 0
            batch_scott_hanan = 0
            
            for contact in contacts:
                given_name = contact.get('given_name', '').lower()
                family_name = contact.get('family_name', '').lower()
                
                # Use both the old method and new method for email extraction
                email = contact.get('email')  # This should now work with our fix
                if not email:
                    email = extract_email(contact)  # Fallback method
                
                if email and 'smhanan' in email.lower():
                    found_smhanan.append({
                        'contact': contact,
                        'email': email,
                        'is_scott': 'scott' in given_name,
                        'is_hanan': 'hanan' in family_name
                    })
                    batch_smhanan += 1
                    
                    if 'scott' in given_name and 'hanan' in family_name:
                        found_scott_hanan.append(contact)
                        batch_scott_hanan += 1
                    
                    print(f"   🎯 SMHANAN: {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
            
            print(f"   Found {batch_smhanan} smhanan contacts in this batch")
            print(f"   Total smhanan found so far: {len(found_smhanan)}")
            
            # If we found 10, we can stop
            if len(found_smhanan) >= 10:
                print(f"   ✅ Found all 10 smhanan contacts!")
                break
            
            offset += batch_size
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Error in batch starting at {offset}: {e}")
            offset += batch_size
            consecutive_empty_batches += 1
            continue
    
    return found_smhanan, found_scott_hanan, total_searched


async def test_email_extraction():
    """Test the fixed email extraction on recent contacts"""
    context = Context()
    
    print("\n🧪 Testing fixed email extraction on recent contacts...")
    
    result = await list_contacts(context, limit=5, order_by="date_created", order_direction="DESC")
    
    if result['count'] > 0:
        details = await get_collection_details(
            context,
            result['collection_id'],
            fields=["id", "given_name", "family_name", "email", "email_addresses"]
        )
        
        contacts = details.get('contacts', [])
        
        for i, contact in enumerate(contacts, 1):
            print(f"\n   Contact {i}: {contact.get('given_name', '')} {contact.get('family_name', '')}")
            
            # Test our fixed email extraction
            email_fixed = contact.get('email')  # Should now work with our fix
            email_manual = extract_email(contact)  # Manual extraction
            
            print(f"       Fixed API email: {email_fixed}")
            print(f"       Manual extraction: {email_manual}")
            
            if email_fixed == email_manual:
                print(f"       ✅ Email extraction working correctly")
            else:
                print(f"       ❌ Email extraction mismatch")


async def analyze_found_contacts(smhanan_contacts, scott_hanan_contacts):
    """Analyze the found contacts"""
    print(f"\n" + "="*60)
    print(f"📊 COMPREHENSIVE SEARCH RESULTS")
    print(f"="*60)
    
    print(f"Total smhanan contacts found: {len(smhanan_contacts)}")
    print(f"Scott Hanan contacts found: {len(scott_hanan_contacts)}")
    
    if len(smhanan_contacts) < 10:
        print(f"⚠️  Found {len(smhanan_contacts)}/10 expected smhanan contacts")
        print(f"   May need to search deeper or investigate data location")
    else:
        print(f"✅ Found all expected smhanan contacts!")
    
    print(f"\n📧 ALL SMHANAN CONTACTS:")
    for i, match in enumerate(smhanan_contacts, 1):
        contact = match['contact']
        email = match['email']
        
        print(f"\n{i:2d}. {contact.get('given_name', '')} {contact.get('family_name', '')}")
        print(f"    Email: {email}")
        print(f"    ID: {contact.get('id')}")
        print(f"    Created: {contact.get('date_created', 'N/A')}")
        print(f"    Scott: {match['is_scott']}, Hanan: {match['is_hanan']}")


async def main():
    """Main execution function"""
    print("🚀 Find ALL 10 smhanan Contacts - Comprehensive Search")
    print("=" * 60)
    
    try:
        # Test email extraction fix
        await test_email_extraction()
        
        # Comprehensive search
        smhanan_contacts, scott_hanan_contacts, total_searched = await comprehensive_smhanan_search()
        
        print(f"\n📊 Search completed - Searched {total_searched} total contacts")
        
        # Analyze results
        await analyze_found_contacts(smhanan_contacts, scott_hanan_contacts)
        
        print(f"\n✅ Comprehensive search complete!")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
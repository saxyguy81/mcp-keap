#!/usr/bin/env python3
"""
Debug script to check API functionality and find Scott Hanan contacts.
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

from src.api.client import KeapApiService


async def debug_api_search():
    """Debug the API search functionality directly"""
    print("🔍 Debugging API search functionality...")
    
    try:
        # Initialize API client directly
        api_service = KeapApiService()
        
        print("\n1️⃣ Testing basic contact retrieval...")
        
        # Test basic contact retrieval
        basic_contacts = await api_service.get_contacts(limit=5)
        print(f"   Basic retrieval: {len(basic_contacts)} contacts")
        
        for contact in basic_contacts[:3]:
            print(f"   - {contact.get('given_name', '')} {contact.get('family_name', '')} (ID: {contact.get('id', '')})")
        
        print("\n2️⃣ Testing email-based search...")
        
        # Test search by email containing 'smhanan'
        try:
            email_search = await api_service.get_contacts(
                limit=20,
                email='*smhanan*'  # Wildcard search
            )
            print(f"   Email search (*smhanan*): {len(email_search)} contacts")
            
            for contact in email_search:
                print(f"   📧 {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
                
        except Exception as e:
            print(f"   ❌ Email search failed: {e}")
        
        print("\n3️⃣ Testing name-based search...")
        
        # Test search by given name
        try:
            name_search = await api_service.get_contacts(
                limit=20,
                given_name='*Scott*'
            )
            print(f"   Name search (*Scott*): {len(name_search)} contacts")
            
            for contact in name_search:
                print(f"   👤 {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
                
        except Exception as e:
            print(f"   ❌ Name search failed: {e}")
        
        print("\n4️⃣ Testing larger batch retrieval...")
        
        # Get a larger batch to scan manually
        large_batch = await api_service.get_contacts(limit=100)
        print(f"   Large batch: {len(large_batch)} contacts")
        
        # Manually search through the batch
        scott_matches = []
        smhanan_matches = []
        
        for contact in large_batch:
            given_name = contact.get('given_name', '').lower()
            family_name = contact.get('family_name', '').lower()
            email = contact.get('email', '').lower()
            
            if 'scott' in given_name or 'hanan' in family_name:
                scott_matches.append(contact)
            
            if 'smhanan' in email:
                smhanan_matches.append(contact)
        
        print(f"   Manual scan - Scott/Hanan matches: {len(scott_matches)}")
        print(f"   Manual scan - smhanan email matches: {len(smhanan_matches)}")
        
        for match in scott_matches + smhanan_matches:
            print(f"   🎯 FOUND: {match.get('given_name', '')} {match.get('family_name', '')} - {match.get('email', '')}")
        
        print("\n5️⃣ Testing custom field retrieval...")
        
        # Get custom fields for first contact
        if large_batch:
            first_contact_id = large_batch[0].get('id')
            print(f"   Getting custom fields for contact {first_contact_id}...")
            
            try:
                detailed_contact = await api_service.get_contact(
                    first_contact_id,
                    optional_properties=['custom_fields']
                )
                
                custom_fields = detailed_contact.get('custom_fields', [])
                print(f"   Custom fields found: {len(custom_fields)}")
                
                # Look for 6FN in field names or values
                fn_fields = []
                for field in custom_fields:
                    field_id = field.get('id')
                    content = str(field.get('content', '')).lower()
                    
                    if '6fn' in content or 'sixfn' in content or 'figure' in content:
                        fn_fields.append(field)
                
                print(f"   Fields with potential 6FN data: {len(fn_fields)}")
                for field in fn_fields:
                    print(f"     Field {field.get('id')}: {field.get('content')}")
                    
            except Exception as e:
                print(f"   ❌ Custom field retrieval failed: {e}")
        
    except Exception as e:
        print(f"❌ API debug failed: {e}")
        import traceback
        traceback.print_exc()


async def test_different_search_approaches():
    """Test different search approaches"""
    print("\n🧪 Testing different search approaches...")
    
    from src.mcp.tools_collections import list_contacts, get_collection_details
    
    context = Context()
    
    search_tests = [
        ("No filters", {}),
        ("Email contains @", {"filters": [{"field": "email", "operator": "contains", "value": "@"}]}),
        ("Large limit", {"limit": 200}),
        ("Different offset", {"limit": 50, "offset": 100}),
    ]
    
    for test_name, params in search_tests:
        try:
            print(f"\n   🔬 Test: {test_name}")
            print(f"      Params: {params}")
            
            result = await list_contacts(context, **params)
            print(f"      Result: {result['count']} contacts")
            
            if result['count'] > 0:
                # Get details for a few contacts
                details = await get_collection_details(
                    context,
                    result['collection_id'],
                    fields=["id", "given_name", "family_name", "email"]
                )
                
                print(f"      Retrieved details for {len(details['contacts'])} contacts")
                
                # Quick scan for our targets
                for contact in details['contacts'][:10]:  # Check first 10
                    given_name = contact.get('given_name', '').lower()
                    family_name = contact.get('family_name', '').lower()
                    email = contact.get('email', '').lower()
                    
                    if ('scott' in given_name or 'hanan' in family_name or 
                        'smhanan' in email):
                        print(f"      🎯 FOUND: {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
            
        except Exception as e:
            print(f"      ❌ Test failed: {e}")


async def main():
    """Main execution function"""
    print("🚀 API Debug & Search Test")
    print("=" * 30)
    
    await debug_api_search()
    await test_different_search_approaches()
    
    print("\n✅ Debug complete!")


if __name__ == "__main__":
    asyncio.run(main())
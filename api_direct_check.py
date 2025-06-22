#!/usr/bin/env python3
"""
Direct API check to diagnose the issue and verify we're looking at the right data.
"""

import asyncio
import os
import json
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.api.client import KeapApiService


async def check_api_directly():
    """Check the API directly to see what's happening"""
    print("🔍 Direct API diagnostics...")
    
    try:
        # Check API key
        api_key = os.getenv('KEAP_API_KEY')
        if api_key:
            print(f"✅ API key found: {api_key[:10]}...{api_key[-10:]}")
        else:
            print("❌ No API key found")
            return
        
        # Initialize API service
        api_service = KeapApiService()
        
        print("\n1️⃣ Testing basic API connectivity...")
        
        # Try to get contacts directly
        try:
            contacts = await api_service.get_contacts(limit=5)
            print(f"   ✅ API call successful - returned {len(contacts)} contacts")
            
            if contacts:
                print("   Sample contact structure:")
                sample_contact = contacts[0]
                print(f"   Keys: {list(sample_contact.keys())}")
                
                # Check for email fields
                if 'email_addresses' in sample_contact:
                    emails = sample_contact['email_addresses']
                    print(f"   Email addresses structure: {type(emails)} - {len(emails) if isinstance(emails, list) else 'Not a list'}")
                    if isinstance(emails, list) and emails:
                        print(f"   Sample email: {emails[0]}")
                
                # Check custom fields structure
                if 'custom_fields' in sample_contact:
                    custom_fields = sample_contact['custom_fields']
                    print(f"   Custom fields structure: {type(custom_fields)} - {len(custom_fields) if isinstance(custom_fields, list) else 'Not a list'}")
                    if isinstance(custom_fields, list) and custom_fields:
                        print(f"   Sample custom field: {custom_fields[0]}")
                
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            return
        
        print("\n2️⃣ Testing contact search by email...")
        
        # Try searching for contacts with smhanan in email
        try:
            search_result = await api_service.search_contacts("smhanan")
            print(f"   Search result: {len(search_result)} contacts")
            
            for contact in search_result:
                print(f"   📧 {contact.get('given_name', '')} {contact.get('family_name', '')} - {contact.get('email', '')}")
                
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
        
        print("\n3️⃣ Checking pagination and total count...")
        
        # Get more contacts with pagination
        try:
            page1 = await api_service.get_contacts(limit=100, offset=0)
            page2 = await api_service.get_contacts(limit=100, offset=100)
            
            print(f"   Page 1: {len(page1)} contacts")
            print(f"   Page 2: {len(page2)} contacts")
            
            # Check if any contacts have smhanan in email
            all_contacts = page1 + page2
            smhanan_contacts = []
            
            for contact in all_contacts:
                # Check all possible email fields
                email_fields = [
                    contact.get('email', ''),
                    contact.get('email_address', ''),
                ]
                
                # Check email_addresses array
                if 'email_addresses' in contact:
                    emails = contact['email_addresses']
                    if isinstance(emails, list):
                        for email_obj in emails:
                            if isinstance(email_obj, dict):
                                email_fields.append(email_obj.get('email', ''))
                            else:
                                email_fields.append(str(email_obj))
                
                # Search for smhanan in any email field
                for email in email_fields:
                    if email and 'smhanan' in email.lower():
                        smhanan_contacts.append(contact)
                        print(f"   🎯 FOUND SMHANAN: {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
                        break
            
            print(f"   Total smhanan contacts found: {len(smhanan_contacts)}")
            
        except Exception as e:
            print(f"   ❌ Pagination test failed: {e}")
        
        print("\n4️⃣ Custom field analysis...")
        
        # Get one contact with full details
        try:
            if contacts:
                first_contact_id = contacts[0]['id']
                detailed = await api_service.get_contact(first_contact_id)
                
                print(f"   Detailed contact keys: {list(detailed.keys())}")
                
                if 'custom_fields' in detailed:
                    custom_fields = detailed['custom_fields']
                    print(f"   Custom fields: {len(custom_fields) if isinstance(custom_fields, list) else 'Not a list'}")
                    
                    if isinstance(custom_fields, list):
                        # Look for field structure
                        for i, field in enumerate(custom_fields[:5]):
                            print(f"   Field {i+1}: {field}")
                            
                            # Check for 6FN in field content or names
                            field_str = json.dumps(field).lower()
                            if '6fn' in field_str or 'figure' in field_str:
                                print(f"     🎯 POTENTIAL 6FN FIELD: {field}")
                
        except Exception as e:
            print(f"   ❌ Custom field analysis failed: {e}")
        
    except Exception as e:
        print(f"❌ Direct API check failed: {e}")
        import traceback
        traceback.print_exc()


async def check_environment():
    """Check environment configuration"""
    print("\n🔧 Environment check...")
    
    # Check .env file
    env_file = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_file):
        print(f"✅ .env file exists at {env_file}")
        with open(env_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'KEAP' in line and not line.strip().startswith('#'):
                    # Mask the key for security
                    parts = line.split('=')
                    if len(parts) >= 2:
                        key = parts[0]
                        value = parts[1].strip()
                        if len(value) > 20:
                            masked_value = f"{value[:10]}...{value[-10:]}"
                        else:
                            masked_value = f"{value[:5]}..."
                        print(f"   {key}={masked_value}")
    else:
        print(f"❌ .env file not found at {env_file}")
    
    # Check environment variables
    api_key = os.getenv('KEAP_API_KEY')
    if api_key:
        print(f"✅ KEAP_API_KEY loaded from environment")
    else:
        print(f"❌ KEAP_API_KEY not found in environment")


async def main():
    """Main execution function"""
    print("🚀 Direct API Diagnostic")
    print("=" * 25)
    
    await check_environment()
    await check_api_directly()
    
    print("\n" + "="*50)
    print("💡 TROUBLESHOOTING SUGGESTIONS")
    print("="*50)
    print("If Scott Hanan contacts and 6FN data should exist but weren't found:")
    print("1. Verify you're connected to the correct Keap account")
    print("2. Check if the data is in a different Keap app/environment")
    print("3. Verify the API key has the correct permissions")
    print("4. Check if contacts were archived or deleted")
    print("5. Try searching in the Keap web interface to confirm data exists")
    
    print("\n✅ Diagnostic complete!")


if __name__ == "__main__":
    asyncio.run(main())
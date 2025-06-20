#!/usr/bin/env python3
"""
Simple API Connection Test Script

This script tests if the Keap API connection is working with the API key from the .env file.
It performs basic API calls to verify connectivity and authentication.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api.client import KeapApiService

# Load environment variables
load_dotenv()


async def test_api_connection():
    """Test the API connection with basic operations."""
    print("🔍 Testing Keap API Connection...")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv("KEAP_API_KEY")
    if not api_key:
        print("❌ Error: KEAP_API_KEY not found in environment variables")
        print("Please check your .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Create API client
    try:
        client = KeapApiService(api_key=api_key)
        print(f"✅ API Client created successfully")
        print(f"   - Base URL: {client.base_url}")
        print(f"   - API Version: {client.api_version}")
    except Exception as e:
        print(f"❌ Error creating API client: {e}")
        return False
    
    # Test basic API info
    try:
        api_info = client.get_api_info()
        print(f"✅ API Info retrieved:")
        print(f"   - Rate limit remaining: {api_info.get('rate_limit_remaining')}")
        print(f"   - Cache entries: {api_info.get('cache_entries')}")
    except Exception as e:
        print(f"❌ Error getting API info: {e}")
    
    # Test API connectivity with a simple request
    print("\n🔗 Testing API Connectivity...")
    print("-" * 30)
    
    try:
        # Try to get a small number of contacts to test connectivity
        start_time = time.time()
        response = await client.get_contacts(limit=1, offset=0)
        elapsed_time = time.time() - start_time
        
        if response and "contacts" in response:
            contact_count = len(response["contacts"])
            print(f"✅ API Connection successful!")
            print(f"   - Response time: {elapsed_time:.2f} seconds")
            print(f"   - Contacts returned: {contact_count}")
            
            # Show sample contact if available
            if contact_count > 0:
                contact = response["contacts"][0]
                print(f"   - Sample contact ID: {contact.get('id')}")
                name = f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
                if name:
                    print(f"   - Sample contact name: {name}")
        else:
            print(f"✅ API Connection successful but no contacts returned")
            print(f"   - Response time: {elapsed_time:.2f} seconds")
            
    except Exception as e:
        print(f"❌ API Connection failed: {e}")
        print(f"   - Error type: {type(e).__name__}")
        return False
    
    # Test tags endpoint
    print("\n🏷️  Testing Tags Endpoint...")
    print("-" * 30)
    
    try:
        start_time = time.time()
        tags_response = await client.get_tags(limit=5)
        elapsed_time = time.time() - start_time
        
        if tags_response and "tags" in tags_response:
            tag_count = len(tags_response["tags"])
            print(f"✅ Tags endpoint successful!")
            print(f"   - Response time: {elapsed_time:.2f} seconds")
            print(f"   - Tags returned: {tag_count}")
            
            # Show sample tags if available
            if tag_count > 0:
                for i, tag in enumerate(tags_response["tags"][:3]):
                    print(f"   - Tag {i+1}: {tag.get('name')} (ID: {tag.get('id')})")
        else:
            print(f"✅ Tags endpoint successful but no tags returned")
            print(f"   - Response time: {elapsed_time:.2f} seconds")
            
    except Exception as e:
        print(f"❌ Tags endpoint failed: {e}")
        print(f"   - Error type: {type(e).__name__}")
    
    # Test diagnostics
    print("\n📊 API Diagnostics...")
    print("-" * 30)
    
    try:
        diagnostics = client.get_diagnostics()
        print(f"✅ Diagnostics retrieved:")
        print(f"   - Total requests: {diagnostics.get('total_requests', 0)}")
        print(f"   - Successful requests: {diagnostics.get('successful_requests', 0)}")
        print(f"   - Failed requests: {diagnostics.get('failed_requests', 0)}")
        print(f"   - Average response time: {diagnostics.get('average_response_time', 0):.3f}s")
        print(f"   - Cache hits: {diagnostics.get('cache_hits', 0)}")
        print(f"   - Cache misses: {diagnostics.get('cache_misses', 0)}")
        
        if diagnostics.get('endpoints_called'):
            print(f"   - Endpoints called: {list(diagnostics['endpoints_called'].keys())}")
            
    except Exception as e:
        print(f"❌ Error getting diagnostics: {e}")
    
    # Close the client
    try:
        await client.close()
        print(f"\n✅ API Client closed successfully")
    except Exception as e:
        print(f"❌ Error closing API client: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Connection Test Complete!")
    
    return True


async def main():
    """Main function to run the API connection test."""
    success = await test_api_connection()
    
    if success:
        print("\n✅ Overall Result: API connection is working correctly!")
        return 0
    else:
        print("\n❌ Overall Result: API connection has issues!")
        return 1


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
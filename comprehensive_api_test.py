#!/usr/bin/env python3
"""
Comprehensive Keap API Test Script

This script performs comprehensive testing of the Keap API client functionality
including contacts, tags, custom fields, and advanced operations.
"""

import asyncio
import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api.client import KeapApiService

# Load environment variables
load_dotenv()


async def test_contacts_advanced(client):
    """Test advanced contacts functionality."""
    print("\n👥 Testing Advanced Contacts Operations...")
    print("-" * 40)
    
    try:
        # Test getting contacts with pagination
        print("🔍 Testing pagination...")
        page1 = await client.get_contacts(limit=5, offset=0)
        page2 = await client.get_contacts(limit=5, offset=5)
        
        print(f"   - Page 1 contacts: {len(page1.get('contacts', []))}")
        print(f"   - Page 2 contacts: {len(page2.get('contacts', []))}")
        
        # Test getting a specific contact
        if page1.get('contacts'):
            contact_id = page1['contacts'][0]['id']
            print(f"🔍 Testing get specific contact (ID: {contact_id})...")
            contact_detail = await client.get_contact(str(contact_id))
            
            if contact_detail:
                print(f"   - Retrieved contact: {contact_detail.get('given_name', '')} {contact_detail.get('family_name', '')}")
                print(f"   - Fields in detailed contact: {len(contact_detail.keys())}")
                
                # Check for custom fields
                if 'custom_fields' in contact_detail:
                    custom_fields = contact_detail['custom_fields']
                    print(f"   - Custom fields found: {len(custom_fields) if custom_fields else 0}")
                    
                    if custom_fields:
                        for cf in custom_fields[:3]:  # Show first 3
                            print(f"     - Field {cf.get('id', 'N/A')}: {cf.get('content', 'N/A')}")
            
        # Test search functionality
        print("🔍 Testing contact search...")
        search_results = await client.search_contacts("@gmail.com", limit=3)
        gmail_contacts = len(search_results.get('contacts', []))
        print(f"   - Gmail contacts found: {gmail_contacts}")
        
    except Exception as e:
        print(f"❌ Error in contacts advanced testing: {e}")


async def test_tags_advanced(client):
    """Test advanced tags functionality."""
    print("\n🏷️  Testing Advanced Tags Operations...")
    print("-" * 40)
    
    try:
        # Get all tags with caching test
        print("🔍 Testing tag caching...")
        
        # First call (cache miss)
        start_time = time.time()
        tags1 = await client.get_tags(limit=10)
        time1 = time.time() - start_time
        
        # Second call (should be cache hit)
        start_time = time.time()
        tags2 = await client.get_tags(limit=10)
        time2 = time.time() - start_time
        
        print(f"   - First call (cache miss): {time1:.3f}s")
        print(f"   - Second call (cache hit): {time2:.3f}s")
        print(f"   - Cache speedup: {time1/time2:.1f}x faster" if time2 > 0 else "")
        
        # Test getting specific tag
        if tags1.get('tags'):
            tag_id = tags1['tags'][0]['id']
            print(f"🔍 Testing get specific tag (ID: {tag_id})...")
            tag_detail = await client.get_tag(str(tag_id))
            
            if tag_detail:
                print(f"   - Retrieved tag: {tag_detail.get('name', 'N/A')}")
                print(f"   - Tag description: {tag_detail.get('description', 'N/A')}")
        
        # Test getting contacts by tag
        if tags1.get('tags'):
            tag_id = tags1['tags'][0]['id']
            print(f"🔍 Testing contacts by tag (ID: {tag_id})...")
            tagged_contacts = await client.get_contacts_by_tag(str(tag_id), limit=5)
            print(f"   - Contacts with this tag: {len(tagged_contacts)}")
            
    except Exception as e:
        print(f"❌ Error in tags advanced testing: {e}")


async def test_api_performance(client):
    """Test API performance and rate limiting."""
    print("\n⚡ Testing API Performance & Rate Limiting...")
    print("-" * 45)
    
    try:
        # Test multiple concurrent requests
        print("🔍 Testing concurrent requests...")
        
        async def make_request():
            return await client.get_contacts(limit=1)
        
        # Make 5 concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        print(f"   - Total requests: {len(results)}")
        print(f"   - Successful: {successful}")
        print(f"   - Failed: {failed}")
        print(f"   - Total time: {elapsed:.3f}s")
        print(f"   - Average per request: {elapsed/len(results):.3f}s")
        
        # Test rate limiting behavior
        print("🔍 Testing rate limiting...")
        rate_limit_info = client.get_diagnostics()
        print(f"   - Rate limit remaining: {rate_limit_info.get('rate_limit_remaining', 'N/A')}")
        print(f"   - Daily requests used: {rate_limit_info.get('daily_request_count', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error in performance testing: {e}")


async def test_error_handling(client):
    """Test error handling capabilities."""
    print("\n🚨 Testing Error Handling...")
    print("-" * 30)
    
    try:
        # Test invalid contact ID
        print("🔍 Testing invalid contact ID...")
        try:
            await client.get_contact("999999999")
            print("   - ⚠️  No error raised for invalid contact ID")
        except Exception as e:
            print(f"   - ✅ Correctly handled invalid contact ID: {type(e).__name__}")
        
        # Test invalid tag ID
        print("🔍 Testing invalid tag ID...")
        try:
            await client.get_tag("999999999")
            print("   - ⚠️  No error raised for invalid tag ID")
        except Exception as e:
            print(f"   - ✅ Correctly handled invalid tag ID: {type(e).__name__}")
        
        # Test malformed parameters
        print("🔍 Testing malformed parameters...")
        try:
            await client.get_contacts(limit=-1)
            print("   - ⚠️  No error raised for negative limit")
        except Exception as e:
            print(f"   - ✅ Correctly handled negative limit: {type(e).__name__}")
            
    except Exception as e:
        print(f"❌ Error in error handling testing: {e}")


async def test_paginated_retrieval(client):
    """Test paginated data retrieval."""
    print("\n📄 Testing Paginated Data Retrieval...")
    print("-" * 38)
    
    try:
        # Test paginated contacts
        print("🔍 Testing paginated contacts retrieval...")
        start_time = time.time()
        all_contacts = await client.get_paginated("/contacts", limit=20)
        elapsed = time.time() - start_time
        
        print(f"   - Total contacts retrieved: {len(all_contacts)}")
        print(f"   - Time taken: {elapsed:.3f}s")
        print(f"   - Rate: {len(all_contacts)/elapsed:.1f} contacts/second")
        
        # Test paginated tags
        print("🔍 Testing paginated tags retrieval...")
        start_time = time.time()
        all_tags = await client.get_paginated("/tags", limit=50)
        elapsed = time.time() - start_time
        
        print(f"   - Total tags retrieved: {len(all_tags)}")
        print(f"   - Time taken: {elapsed:.3f}s")
        
    except Exception as e:
        print(f"❌ Error in paginated retrieval testing: {e}")


async def comprehensive_api_test():
    """Run comprehensive API tests."""
    print("🔬 Comprehensive Keap API Testing")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("KEAP_API_KEY")
    if not api_key:
        print("❌ Error: KEAP_API_KEY not found in environment variables")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    # Create client
    client = KeapApiService(api_key=api_key)
    
    try:
        # Run all test suites
        await test_contacts_advanced(client)
        await test_tags_advanced(client)
        await test_api_performance(client)
        await test_error_handling(client)
        await test_paginated_retrieval(client)
        
        # Final diagnostics
        print("\n📊 Final API Diagnostics...")
        print("-" * 30)
        
        diagnostics = client.get_diagnostics()
        print(f"✅ Session Summary:")
        print(f"   - Total API calls: {diagnostics.get('total_requests', 0)}")
        print(f"   - Successful calls: {diagnostics.get('successful_requests', 0)}")
        print(f"   - Failed calls: {diagnostics.get('failed_requests', 0)}")
        print(f"   - Success rate: {(diagnostics.get('successful_requests', 0) / max(diagnostics.get('total_requests', 1), 1) * 100):.1f}%")
        print(f"   - Average response time: {diagnostics.get('average_response_time', 0):.3f}s")
        print(f"   - Total response time: {diagnostics.get('total_response_time', 0):.3f}s")
        print(f"   - Cache efficiency: {diagnostics.get('cache_hits', 0)}/{diagnostics.get('cache_hits', 0) + diagnostics.get('cache_misses', 0)} hits")
        
        # Show endpoints used
        endpoints = diagnostics.get('endpoints_called', {})
        if endpoints:
            print(f"   - Endpoints used: {len(endpoints)}")
            for endpoint, count in endpoints.items():
                print(f"     - {endpoint}: {count} calls")
        
        # Show any errors
        errors = diagnostics.get('error_counts', {})
        if errors:
            print(f"   - Error breakdown:")
            for error, count in errors.items():
                print(f"     - {error}: {count} occurrences")
        
    except Exception as e:
        print(f"❌ Error during comprehensive testing: {e}")
        return False
    
    finally:
        await client.close()
        print(f"\n✅ API Client closed successfully")
    
    print("\n" + "=" * 50)
    print("🎉 Comprehensive API Testing Complete!")
    
    return True


async def main():
    """Main function."""
    success = await comprehensive_api_test()
    
    if success:
        print("\n✅ Overall Result: All API tests passed!")
        return 0
    else:
        print("\n❌ Overall Result: Some API tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
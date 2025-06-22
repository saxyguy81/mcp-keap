#!/usr/bin/env python3
"""
Test both optimization engine and client-side filtering to isolate the issue.
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


async def test_both_filtering_approaches():
    """Test both optimization engine and client-side filtering"""
    print("🧪 Testing both filtering approaches...")
    
    context = Context()
    
    test_filter = {"field": "email", "operator": "contains", "value": "@gmail.com"}
    
    print(f"Test filter: {test_filter}")
    
    # Test 1: With optimization (default)
    print(f"\n1️⃣ Testing with optimization engine (enable_optimization=True)...")
    try:
        result_optimized = await list_contacts(
            context,
            filters=[test_filter],
            limit=5,
            enable_optimization=True
        )
        
        count_optimized = result_optimized.get('count', 0)
        print(f"   ✅ Optimization engine: Found {count_optimized} contacts")
        
        if count_optimized > 0:
            details = await get_collection_details(
                context,
                result_optimized['collection_id'],
                fields=["id", "given_name", "family_name", "email"],
                limit=2
            )
            
            contacts = details.get('contacts', [])
            for contact in contacts:
                name = f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
                email = contact.get('email', 'No email')
                print(f"      • {name}: {email}")
    
    except Exception as e:
        print(f"   ❌ Optimization engine failed: {e}")
    
    # Test 2: Without optimization (client-side filtering)
    print(f"\n2️⃣ Testing with client-side filtering (enable_optimization=False)...")
    try:
        result_client = await list_contacts(
            context,
            filters=[test_filter],
            limit=5,
            enable_optimization=False
        )
        
        count_client = result_client.get('count', 0)
        print(f"   ✅ Client-side filtering: Found {count_client} contacts")
        
        if count_client > 0:
            details = await get_collection_details(
                context,
                result_client['collection_id'],
                fields=["id", "given_name", "family_name", "email"],
                limit=2
            )
            
            contacts = details.get('contacts', [])
            for contact in contacts:
                name = f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
                email = contact.get('email', 'No email')
                print(f"      • {name}: {email}")
    
    except Exception as e:
        print(f"   ❌ Client-side filtering failed: {e}")
    
    # Test 3: No filtering at all to see raw data
    print(f"\n3️⃣ Testing without any filtering to see raw data...")
    try:
        result_none = await list_contacts(
            context,
            limit=5,
            enable_optimization=False
        )
        
        count_none = result_none.get('count', 0)
        print(f"   ✅ No filtering: Found {count_none} contacts")
        
        details = await get_collection_details(
            context,
            result_none['collection_id'],
            fields=["id", "given_name", "family_name", "email"],
            limit=5
        )
        
        contacts = details.get('contacts', [])
        gmail_count = 0
        for contact in contacts:
            name = f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
            email = contact.get('email', 'No email')
            print(f"      • {name}: {email}")
            if '@gmail.com' in email:
                gmail_count += 1
        
        print(f"   📊 Gmail contacts in raw data: {gmail_count}/{len(contacts)}")
    
    except Exception as e:
        print(f"   ❌ Raw data retrieval failed: {e}")


async def test_simple_filters():
    """Test very simple filters to isolate the issue"""
    print(f"\n🧪 Testing simple filters...")
    
    context = Context()
    
    simple_tests = [
        {
            "name": "is_not_null (should work)",
            "filter": {"field": "email", "operator": "is_not_null", "value": ""}
        },
        {
            "name": "contains '@' (might fail)",
            "filter": {"field": "email", "operator": "contains", "value": "@"}
        },
        {
            "name": "equals specific email (might fail)",
            "filter": {"field": "email", "operator": "equals", "value": "smunira@gmail.com"}
        }
    ]
    
    for test in simple_tests:
        print(f"\n📋 {test['name']}")
        print(f"   Filter: {test['filter']}")
        
        # Test with client-side filtering (more predictable)
        try:
            result = await list_contacts(
                context,
                filters=[test['filter']],
                limit=3,
                enable_optimization=False
            )
            
            count = result.get('count', 0)
            print(f"   ✅ Client-side: Found {count} contacts")
            
        except Exception as e:
            print(f"   ❌ Client-side failed: {e}")
        
        # Test with optimization
        try:
            result = await list_contacts(
                context,
                filters=[test['filter']],
                limit=3,
                enable_optimization=True
            )
            
            count = result.get('count', 0)
            print(f"   ✅ Optimized: Found {count} contacts")
            
        except Exception as e:
            print(f"   ❌ Optimized failed: {e}")


async def main():
    """Main test function"""
    print("🚀 Testing Optimization vs Client-Side Filtering")
    print("=" * 55)
    
    await test_both_filtering_approaches()
    await test_simple_filters()
    
    print(f"\n" + "="*55)
    print(f"📊 ANALYSIS COMPLETE")
    print(f"="*55)
    print(f"This will help identify whether the issue is in:")
    print(f"1. Optimization engine")
    print(f"2. Client-side filtering logic")
    print(f"3. Data format/structure issues")


if __name__ == "__main__":
    asyncio.run(main())
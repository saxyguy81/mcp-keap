#!/usr/bin/env python3
"""
Test Form-Based Contact Filtering

Based on the investigation, this script tests various approaches to find contacts
who filled out specific forms like 'VSN Website guest registration'.
"""

import asyncio
from datetime import datetime, timedelta
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts, 
    get_collection_details, 
    get_tags,
    collection_intersect
)


async def test_form_filtering():
    """Test different approaches to find form submissions."""
    print("🔍 Testing Form-Based Contact Filtering")
    print("=" * 50)
    
    context = Context()
    
    # 1. Search for the specific contact mentioned
    print("\n1. Searching for smhanan+test6@gmail.com...")
    
    target_email_result = await list_contacts(
        context,
        filters=[{"field": "email", "operator": "equals", "value": "smhanan+test6@gmail.com"}],
        limit=10
    )
    
    print(f"   Found {target_email_result['count']} contacts with target email")
    
    if target_email_result["count"] > 0:
        details = await get_collection_details(
            context, 
            target_email_result["collection_id"],
            fields=["id", "given_name", "family_name", "email", "date_created", "last_updated"]
        )
        
        for contact in details.get("contacts", []):
            print(f"   Contact: {contact.get('given_name')} {contact.get('family_name')}")
            print(f"   Email: {contact.get('email')}")
            print(f"   Created: {contact.get('date_created')}")
            print(f"   ID: {contact.get('id')}")
    
    # 2. Search for VSN-related tags
    print("\n2. Searching for VSN-related tags...")
    
    vsn_tags = await get_tags(
        context,
        filters=[{"field": "name", "operator": "contains", "value": "VSN"}],
        limit=20
    )
    
    print(f"   Found {vsn_tags.get('count', 0)} VSN-related tags:")
    for tag in vsn_tags.get("tags", [])[:10]:
        print(f"   - {tag.get('name')} (ID: {tag.get('id')})")
    
    # 3. Search for registration-related tags
    print("\n3. Searching for registration-related tags...")
    
    reg_tags = await get_tags(
        context,
        filters=[{"field": "name", "operator": "contains", "value": "registration"}],
        limit=20
    )
    
    print(f"   Found {reg_tags.get('count', 0)} registration-related tags:")
    for tag in reg_tags.get("tags", [])[:10]:
        print(f"   - {tag.get('name')} (ID: {tag.get('id')})")
    
    # 4. Search for guest-related tags
    print("\n4. Searching for guest-related tags...")
    
    guest_tags = await get_tags(
        context,
        filters=[{"field": "name", "operator": "contains", "value": "guest"}],
        limit=20
    )
    
    print(f"   Found {guest_tags.get('count', 0)} guest-related tags:")
    for tag in guest_tags.get("tags", [])[:10]:
        print(f"   - {tag.get('name')} (ID: {tag.get('id')})")
    
    # 5. Search for contacts created around 6/10/25
    print("\n5. Searching for contacts created around 6/10/25...")
    
    # Search for contacts created in June 2025
    june_contacts = await list_contacts(
        context,
        filters=[{"field": "date_created", "operator": "after", "value": "2025-06-01T00:00:00Z"}],
        limit=50
    )
    
    print(f"   Found {june_contacts['count']} contacts created in June 2025")
    
    if june_contacts["count"] > 0:
        june_details = await get_collection_details(
            context,
            june_contacts["collection_id"],
            fields=["id", "given_name", "family_name", "email", "date_created"],
            limit=10
        )
        
        print("   Recent contacts:")
        for contact in june_details.get("contacts", [])[:5]:
            name = f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
            print(f"   - {name} ({contact.get('email')}) - {contact.get('date_created')}")
    
    # 6. Test specific tag-based filtering if we found relevant tags
    print("\n6. Testing tag-based filtering for VSN/registration...")
    
    # Get the most relevant tags from our searches
    relevant_tag_ids = []
    
    for tag_result in [vsn_tags, reg_tags, guest_tags]:
        for tag in tag_result.get("tags", [])[:3]:  # Take top 3 from each category
            if any(keyword in tag.get("name", "").lower() 
                   for keyword in ["vsn", "registration", "guest", "website"]):
                relevant_tag_ids.append(tag.get("id"))
    
    if relevant_tag_ids:
        print(f"   Testing with relevant tag IDs: {relevant_tag_ids[:5]}")
        
        # Try to find contacts with these tags
        for tag_id in relevant_tag_ids[:3]:  # Test first 3 tags
            try:
                # Use the API client directly to get contacts by tag
                from src.mcp.tools_collections import get_api_client
                api_client = get_api_client()
                
                tagged_contacts = await api_client.get_contacts_by_tag(str(tag_id), limit=10)
                print(f"   Tag {tag_id}: {len(tagged_contacts)} contacts")
                
                for contact in tagged_contacts[:3]:
                    name = f"{contact.get('given_name', '')} {contact.get('family_name', '')}".strip()
                    print(f"     - {name} ({contact.get('email')})")
                    
            except Exception as e:
                print(f"   Error checking tag {tag_id}: {e}")
    
    # 7. Try searching by email pattern for test accounts
    print("\n7. Searching for test email patterns...")
    
    test_patterns = [
        "smhanan+test",
        "@gmail.com",
        "test"
    ]
    
    for pattern in test_patterns:
        try:
            pattern_result = await list_contacts(
                context,
                filters=[{"field": "email", "operator": "contains", "value": pattern}],
                limit=10
            )
            
            print(f"   Pattern '{pattern}': {pattern_result['count']} contacts")
            
            if pattern_result["count"] > 0 and pattern_result["count"] <= 5:
                pattern_details = await get_collection_details(
                    context,
                    pattern_result["collection_id"],
                    fields=["id", "email", "date_created"],
                    limit=5
                )
                
                for contact in pattern_details.get("contacts", []):
                    print(f"     - {contact.get('email')} (Created: {contact.get('date_created')})")
                    
        except Exception as e:
            print(f"   Error searching pattern '{pattern}': {e}")
    
    print("\n" + "=" * 50)
    print("Form filtering investigation complete!")
    print("\nNext steps to implement form-based filtering:")
    print("1. Identify specific tags applied when VSN forms are submitted")
    print("2. Use date_created filtering for time-based searches")
    print("3. Combine tag and date filters for precise form submission tracking")
    print("4. Consider custom fields that might track form submission details")


if __name__ == "__main__":
    asyncio.run(test_form_filtering())
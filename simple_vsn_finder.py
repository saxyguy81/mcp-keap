#!/usr/bin/env python3
"""
Simple VSN Website guest registration finder using direct API client approach.
Based on the working form investigation results.
"""

import asyncio
import os

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.api.client import KeapApiService


async def find_vsn_website_guests():
    """Find VSN website guest registrations using direct API approach"""
    print("🔍 FINDING VSN WEBSITE GUEST REGISTRATIONS (DIRECT API)")
    print("="*70)
    
    api_service = KeapApiService()
    
    try:
        # Step 1: Get recent contacts to analyze
        print("\n📅 Step 1: Getting recent contacts...")
        recent_response = await api_service.get_contacts(
            limit=200,
            order_by="date_created",
            order_direction="DESC",
            include_custom_fields=True,
            include_tags=True
        )
        
        recent_contacts = recent_response.get('contacts', []) if isinstance(recent_response, dict) else []
        print(f"✅ Retrieved {len(recent_contacts)} recent contacts")
        
        # Step 2: Filter by date range (6/9-6/12/25)
        print(f"\n📅 Step 2: Filtering for contacts created around 6/10/25...")
        
        june_10_contacts = []
        for contact in recent_contacts:
            created_date = contact.get('date_created', '')
            if created_date and '2025-06' in created_date:
                # Check if it's between 6/9 and 6/12
                if any(day in created_date for day in ['2025-06-09', '2025-06-10', '2025-06-11', '2025-06-12']):
                    june_10_contacts.append(contact)
        
        print(f"📋 Found {len(june_10_contacts)} contacts created around 6/10/25:")
        for contact in june_10_contacts:
            email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
            print(f"  • {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
            print(f"    ID: {contact.get('id')} | Created: {contact.get('date_created', 'Unknown')}")
            print(f"    Tags: {contact.get('tag_ids', [])}")
        
        # Step 3: Look for VSN-related tags in all recent contacts
        print(f"\n🏷️  Step 3: Analyzing VSN tags in recent contacts...")
        
        # VSN-related tag IDs from our investigation
        target_vsn_tags = [5031, 4537, 3519]  # VSN June A, VSN Guest, General VSN Guest
        tag_names = {
            5031: "Attended - 2025 - VSN - June A",
            4537: "Attended - 2025 - VSN - Guest", 
            3519: "Guest - VSN"
        }
        
        vsn_tagged_contacts = []
        for contact in recent_contacts:
            contact_tags = contact.get('tag_ids', [])
            if any(tag in contact_tags for tag in target_vsn_tags):
                vsn_tagged_contacts.append(contact)
        
        print(f"📋 Found {len(vsn_tagged_contacts)} contacts with VSN tags:")
        for contact in vsn_tagged_contacts:
            email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
            contact_tags = contact.get('tag_ids', [])
            matching_vsn_tags = [tag for tag in target_vsn_tags if tag in contact_tags]
            
            print(f"  • {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
            print(f"    ID: {contact.get('id')} | Created: {contact.get('date_created', 'Unknown')}")
            vsn_tag_desc = [f"{tag}({tag_names.get(tag, 'Unknown')})" for tag in matching_vsn_tags]
            print(f"    VSN Tags: {vsn_tag_desc}")
        
        # Step 4: Find the intersection - contacts that match BOTH criteria
        print(f"\n🎯 Step 4: Finding contacts that match BOTH date AND VSN criteria...")
        
        final_matches = []
        for contact in june_10_contacts:
            contact_tags = contact.get('tag_ids', [])
            if any(tag in contact_tags for tag in target_vsn_tags):
                final_matches.append(contact)
        
        print(f"🎯 FINAL RESULTS:")
        print(f"="*70)
        
        if final_matches:
            print(f"✅ Found {len(final_matches)} contacts who filled VSN Website guest registration around 6/10/25:")
            
            for i, contact in enumerate(final_matches, 1):
                email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                contact_tags = contact.get('tag_ids', [])
                matching_vsn_tags = [tag for tag in target_vsn_tags if tag in contact_tags]
                
                print(f"\n{i}. Contact ID: {contact.get('id')}")
                print(f"   Name: {contact.get('given_name', '')} {contact.get('family_name', '')}")
                print(f"   Email: {email}")
                print(f"   Created: {contact.get('date_created', 'Unknown')}")
                vsn_tag_desc = [f"{tag}({tag_names.get(tag, 'Unknown')})" for tag in matching_vsn_tags]
                print(f"   VSN Tags: {vsn_tag_desc}")
                print(f"   All Tags: {contact_tags}")
                
                # Look for form-related custom fields
                custom_fields = contact.get('custom_fields', [])
                form_related_fields = []
                for field in custom_fields:
                    content = str(field.get('content', '')).lower()
                    field_name = field.get('field_name', '')
                    if content and any(keyword in content for keyword in ['vsn', 'registration', 'website', 'form', 'guest']):
                        form_related_fields.append(field)
                
                if form_related_fields:
                    print(f"   📋 Form-related custom fields:")
                    for field in form_related_fields:
                        print(f"     - {field.get('field_name', 'Unknown')}: {field.get('content', '')}")
        else:
            print(f"❌ No contacts found matching BOTH criteria")
            print(f"   - Contacts around 6/10/25: {len(june_10_contacts)}")
            print(f"   - Contacts with VSN tags: {len(vsn_tagged_contacts)}")
        
        # Step 5: Check the specific test contact
        print(f"\n📧 Step 5: Checking specific test contact (smhanan+test6@gmail.com)...")
        
        test_contact = None
        for contact in recent_contacts:
            email_addresses = contact.get('email_addresses', [])
            for email_obj in email_addresses:
                if email_obj.get('email') == 'smhanan+test6@gmail.com':
                    test_contact = contact
                    break
            if test_contact:
                break
        
        if test_contact:
            print(f"✅ Found test contact:")
            print(f"  ID: {test_contact.get('id')}")
            print(f"  Name: {test_contact.get('given_name', '')} {test_contact.get('family_name', '')}")
            print(f"  Created: {test_contact.get('date_created')}")
            print(f"  Tags: {test_contact.get('tag_ids', [])}")
            
            # Check criteria
            created_date = test_contact.get('date_created', '')
            contact_tags = test_contact.get('tag_ids', [])
            
            in_date_range = any(day in created_date for day in ['2025-06-09', '2025-06-10', '2025-06-11', '2025-06-12'])
            has_vsn_tags = any(tag in contact_tags for tag in target_vsn_tags)
            
            print(f"  📅 In target date range: {in_date_range}")
            print(f"  🏷️  Has VSN tags: {has_vsn_tags}")
            
            if has_vsn_tags:
                matching_tags = [tag for tag in target_vsn_tags if tag in contact_tags]
                matching_tag_desc = [f"{tag}({tag_names.get(tag, 'Unknown')})" for tag in matching_tags]
                print(f"  🎯 Matching VSN tags: {matching_tag_desc}")
            
            if in_date_range and has_vsn_tags:
                print(f"  ✅ Test contact MATCHES all criteria!")
            else:
                print(f"  ⚠️  Test contact doesn't match all criteria")
        else:
            print(f"❌ Test contact not found in recent data")
        
        # Summary
        print(f"\n" + "="*70)
        print(f"📊 SUMMARY")
        print(f"="*70)
        print(f"Investigation Results:")
        print(f"• Total recent contacts analyzed: {len(recent_contacts)}")
        print(f"• Contacts created around 6/10/25: {len(june_10_contacts)}")
        print(f"• Contacts with VSN tags: {len(vsn_tagged_contacts)}")
        print(f"• Final matches (both criteria): {len(final_matches)}")
        
        print(f"\nForm Filtering Strategy:")
        if final_matches:
            print(f"✅ SUCCESS: Use tag-based + date filtering approach")
            print(f"✅ Key VSN tags: {target_vsn_tags}")
            print(f"✅ Date range: 6/9-6/12/25 works well")
        else:
            print(f"💡 Consider expanding date range or checking additional VSN tags")
            print(f"💡 Review custom fields for form source information")
        
        print(f"\nNext Steps:")
        print(f"1. Use the identified tag IDs {target_vsn_tags} for VSN filtering")
        print(f"2. Combine with date ranges for precise targeting")
        print(f"3. Use MCP collection operations for complex filtering")
        print(f"4. Investigate custom fields for additional form tracking data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await api_service.close()


async def main():
    await find_vsn_website_guests()


if __name__ == "__main__":
    asyncio.run(main())
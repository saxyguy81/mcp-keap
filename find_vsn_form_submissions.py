#!/usr/bin/env python3
"""
Find contacts who filled out VSN Website guest registration forms around 6/10/25
Uses the discovered tag-based filtering approach.
"""

import asyncio
import os

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Simple context class for testing
class Context:
    pass

from src.mcp.tools_collections import (
    list_contacts, get_collection_details, get_contact_schema, 
    collection_intersect, get_tags
)


async def find_vsn_form_submissions():
    """Find VSN Website guest registration submissions around 6/10/25"""
    print("🔍 FINDING VSN WEBSITE GUEST REGISTRATION SUBMISSIONS")
    print("=" * 70)
    print("Target: Contacts who filled 'VSN Website guest registration' around 6/10/25")
    print("=" * 70)
    
    context = Context()
    
    try:
        # Step 1: Get recent contacts and filter by date manually 
        print("\n📅 Step 1: Finding contacts created around 6/10/25...")
        
        # Get recent contacts (order by date_created DESC to get newest first)
        print("🔍 Calling list_contacts...")
        date_result = await list_contacts(
            context,
            limit=100,
            order_by="date_created",
            order_direction="DESC"
        )
        
        print(f"📊 list_contacts returned: {type(date_result)} - {date_result}")
        
        if date_result and 'collection_id' in date_result:
            recent_collection_id = date_result['collection_id']
            recent_count = date_result.get('count', 0)
            print(f"✅ Retrieved {recent_count} recent contacts (Collection: {recent_collection_id})")
            
            # Get details and filter by date range manually
            recent_details = await get_collection_details(context, recent_collection_id)
            print(f"📊 get_collection_details returned: {type(recent_details)}")
            if recent_details and ('contacts' in recent_details or recent_details.get('success')):
                all_recent_contacts = recent_details.get('contacts', [])
                
                # Filter for contacts created around 6/10/25 (6/9 to 6/12)
                june_10_contacts = []
                for contact in all_recent_contacts:
                    created_date = contact.get('date_created', '')
                    if created_date and '2025-06' in created_date:
                        # Check if it's between 6/9 and 6/12
                        if any(day in created_date for day in ['2025-06-09', '2025-06-10', '2025-06-11', '2025-06-12']):
                            june_10_contacts.append(contact)
                
                print(f"📋 Contacts created around 6/10/25: {len(june_10_contacts)}")
                for contact in june_10_contacts:
                    email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                    print(f"  • {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
                    print(f"    Created: {contact.get('date_created', 'Unknown')} | Tags: {contact.get('tag_ids', [])}")
                
                # Update the count for later use
                date_count = len(june_10_contacts)
        else:
            print(f"❌ Date filtering failed: {date_result.get('error')}")
            return
        
        # Step 2: Find contacts with VSN-related tags
        print(f"\n🏷️  Step 2: Searching for contacts with VSN tags in recent data...")
        
        # Instead of complex filtering, search through the recent contacts for VSN tags
        vsn_tagged_contacts = []
        target_vsn_tags = [5031, 4537, 3519]  # VSN June A, VSN Guest, General VSN Guest
        
        for contact in all_recent_contacts:
            contact_tags = contact.get('tag_ids', [])
            if any(tag in contact_tags for tag in target_vsn_tags):
                vsn_tagged_contacts.append(contact)
        
        print(f"✅ Found {len(vsn_tagged_contacts)} contacts with VSN tags")
        
        if vsn_tagged_contacts:
            print(f"📋 VSN tagged contacts:")
            for contact in vsn_tagged_contacts:
                email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                contact_tags = contact.get('tag_ids', [])
                matching_vsn_tags = [tag for tag in target_vsn_tags if tag in contact_tags]
                print(f"  • {contact.get('given_name', '')} {contact.get('family_name', '')} - {email}")
                print(f"    Created: {contact.get('date_created', 'Unknown')} | VSN Tags: {matching_vsn_tags}")
        
        # Step 3: Find the intersection of date and VSN tag criteria
        print(f"\n🔗 Step 3: Finding contacts that match BOTH date and VSN criteria...")
        
        # Find contacts that are both in June 10 timeframe AND have VSN tags
        final_matches = []
        for contact in june_10_contacts:
            contact_tags = contact.get('tag_ids', [])
            if any(tag in contact_tags for tag in target_vsn_tags):
                final_matches.append(contact)
        
        print(f"✅ Found {len(final_matches)} contacts matching BOTH criteria")
        
        # Step 4: Display final results
        if final_matches:
            print(f"\n🎯 FINAL RESULTS - VSN Website Guest Registrations around 6/10/25:")
            print(f"=" * 70)
            
            for i, contact in enumerate(final_matches, 1):
                email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                contact_tags = contact.get('tag_ids', [])
                matching_vsn_tags = [tag for tag in target_vsn_tags if tag in contact_tags]
                
                print(f"\n{i}. Contact ID: {contact.get('id')}")
                print(f"   Name: {contact.get('given_name', '')} {contact.get('family_name', '')}")
                print(f"   Email: {email}")
                print(f"   Created: {contact.get('date_created', 'Unknown')}")
                print(f"   VSN Tags: {matching_vsn_tags}")
                print(f"   All Tags: {contact_tags}")
                
                # Check for form-related custom fields
                custom_fields = contact.get('custom_fields', [])
                form_fields = []
                for field in custom_fields:
                    content = str(field.get('content', '')).lower()
                    field_name = field.get('field_name', '')
                    if content and any(keyword in content for keyword in ['vsn', 'registration', 'website', 'form', 'guest']):
                        form_fields.append(field)
                
                if form_fields:
                    print(f"   📋 Form-related custom fields:")
                    for field in form_fields:
                        print(f"     - {field.get('field_name', 'Unknown')}: {field.get('content', '')}")
                
        # Step 5: Check specific test contact if we didn't find it in results
        print(f"\n📧 Step 5: Checking specific test contact (smhanan+test6@gmail.com)...")
        
        test_contact_found = False
        for contact in all_recent_contacts:
            email_addresses = contact.get('email_addresses', [])
            for email_obj in email_addresses:
                if email_obj.get('email') == 'smhanan+test6@gmail.com':
                    test_contact_found = True
                    print(f"✅ Found test contact in recent data:")
                    print(f"  ID: {contact.get('id')}")
                    print(f"  Name: {contact.get('given_name', '')} {contact.get('family_name', '')}")
                    print(f"  Created: {contact.get('date_created')}")
                    print(f"  Tags: {contact.get('tag_ids', [])}")
                    
                    # Check if it matches our criteria
                    created_date = contact.get('date_created', '')
                    contact_tags = contact.get('tag_ids', [])
                    
                    in_date_range = any(day in created_date for day in ['2025-06-09', '2025-06-10', '2025-06-11', '2025-06-12'])
                    has_vsn_tags = any(tag in contact_tags for tag in target_vsn_tags)
                    
                    print(f"  📅 In date range (6/9-6/12): {in_date_range}")
                    print(f"  🏷️  Has VSN tags: {has_vsn_tags}")
                    
                    if has_vsn_tags:
                        matching_tags = [tag for tag in target_vsn_tags if tag in contact_tags]
                        print(f"  🎯 Matching VSN tags: {matching_tags}")
                    
                    break
        
        if not test_contact_found:
            print("❌ Test contact not found in recent data - may need to expand search")
        
        # Summary
        print(f"\n" + "="*70)
        print(f"📊 SUMMARY & ANALYSIS")
        print(f"="*70)
        print(f"Search Results:")
        print(f"• Total recent contacts analyzed: {recent_count}")
        print(f"• Contacts created around 6/10/25: {date_count}")
        print(f"• Contacts with VSN tags: {len(vsn_tagged_contacts)}")
        print(f"• Contacts matching BOTH criteria: {len(final_matches)}")
        
        if final_matches:
            print(f"\n🎯 SUCCESS: Found {len(final_matches)} contacts who likely filled out VSN Website guest registration around 6/10/25")
        else:
            print(f"\n⚠️  No exact matches found - possible reasons:")
            print(f"   - Form submissions may use different tags")
            print(f"   - Date range may need adjustment")
            print(f"   - Custom fields may contain the form source information")
        
        print(f"\nKey VSN Tags Found in Data:")
        if vsn_tagged_contacts:
            all_vsn_tags = set()
            for contact in vsn_tagged_contacts:
                contact_tags = contact.get('tag_ids', [])
                for tag in target_vsn_tags:
                    if tag in contact_tags:
                        all_vsn_tags.add(tag)
            
            tag_names = {
                5031: "Attended - 2025 - VSN - June A",
                4537: "Attended - 2025 - VSN - Guest", 
                3519: "Guest - VSN"
            }
            
            for tag in all_vsn_tags:
                print(f"   - Tag {tag}: {tag_names.get(tag, 'Unknown VSN tag')}")
        else:
            print(f"   - No VSN tags found in recent contacts")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if final_matches:
            print(f"✅ Use the {len(final_matches)} contacts found - they are the best matches")
            print(f"✅ Review their custom fields for additional form tracking data")
        elif date_count > 0 and len(vsn_tagged_contacts) > 0:
            print(f"💡 Manually review date-filtered contacts with VSN tags")
            print(f"💡 Consider broader VSN tag search (check other VSN tag IDs)")
        elif date_count > 0:
            print(f"💡 Review the {date_count} date-filtered contacts manually")
            print(f"💡 Look for form-related custom fields in those contacts")
        else:
            print(f"⚠️  Consider expanding the date range beyond 6/9-6/12/25")
            print(f"⚠️  Search for other form-related tag patterns")
            
        print(f"\n🔍 FORM TRACKING INSIGHTS:")
        print(f"• VSN events use structured tagging for attendance tracking")
        print(f"• Guest registrations get specific tags (found guest-related tags)")
        print(f"• Date filtering works well for time-based searches")
        print(f"• Manual filtering can be more reliable than complex API filters")
        print(f"• Custom fields likely contain additional form source information")
        
    except Exception as e:
        print(f"❌ Error during VSN form submission search: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main execution function"""
    await find_vsn_form_submissions()


if __name__ == "__main__":
    asyncio.run(main())
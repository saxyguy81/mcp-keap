#!/usr/bin/env python3
"""
Practical implementation to find contacts who filled out VSN Website guest registration around 6/10/25
Uses the discovered form filtering capabilities and MCP tools.
"""

import asyncio
import json
import sys
sys.path.insert(0, '/Users/smhanan/CascadeProjects/mcp-keap/src')

from mcp.tools_collections import (
    list_contacts, get_contact_schema, get_tags, apply_tags_to_collection, 
    collection_intersect, get_collection_details, get_collection_ids
)
from mcp.server.fastmcp import Context

# Create a mock context for testing
class MockContext:
    def __init__(self):
        pass

async def find_vsn_website_guests():
    """Find contacts who filled out VSN Website guest registration around 6/10/25."""
    print("🔍 FINDING VSN WEBSITE GUEST REGISTRATIONS AROUND 6/10/25")
    print("="*70)
    
    context = MockContext()
    
    try:
        # Step 1: Get the contact schema to understand field structure
        print("\n📋 Step 1: Getting contact schema...")
        schema_result = await get_contact_schema(context)
        if schema_result.get('success'):
            custom_fields = schema_result.get('custom_fields', [])
            print(f"✅ Found {len(custom_fields)} custom fields")
            
            # Look for form/source related fields
            form_fields = []
            for field in custom_fields:
                field_name = field.get('field_name', '').lower()
                if any(keyword in field_name for keyword in ['form', 'source', 'registration', 'website', 'vsn']):
                    form_fields.append(field)
                    print(f"  🎯 Form field: {field.get('field_name')} ({field.get('label')})")
            
            print(f"Found {len(form_fields)} potentially relevant form fields")
        
        # Step 2: Create collection with date filter around 6/10/25
        print("\n📅 Step 2: Creating collection with date filter (6/9-6/12/25)...")
        date_filter = {
            "date_created": {
                "start_date": "2025-06-09",
                "end_date": "2025-06-12"
            }
        }
        
        date_result = await list_contacts(
            context,
            filters=json.dumps(date_filter),
            limit=100,
            order_by="date_created",
            order_direction="ASC"
        )
        
        if date_result.get('success'):
            date_collection_id = date_result.get('collection_id')
            contacts_count = date_result.get('count', 0)
            print(f"✅ Created date collection '{date_collection_id}' with {contacts_count} contacts")
            
            # Get details of these contacts
            date_details = await get_collection_details(context, date_collection_id)
            if date_details.get('success'):
                date_contacts = date_details.get('contacts', [])
                print(f"📋 Date-filtered contacts ({len(date_contacts)}):")
                for contact in date_contacts:
                    email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                    print(f"  • {contact.get('given_name', '')} {contact.get('family_name', '')} - {email} (Created: {contact.get('date_created', 'Unknown')})")
        else:
            print(f"❌ Failed to create date collection: {date_result.get('error')}")
            return
        
        # Step 3: Create collection with VSN June A tag (most relevant)
        print("\n🏷️  Step 3: Creating collection with VSN June A tag (ID: 5031)...")
        vsn_june_filter = {
            "tag_ids": [5031]  # "Attended - 2025 - VSN - June A"
        }
        
        vsn_june_result = await list_contacts(
            context,
            filters=json.dumps(vsn_june_filter),
            limit=100
        )
        
        if vsn_june_result.get('success'):
            vsn_june_collection_id = vsn_june_result.get('collection_id')
            vsn_june_count = vsn_june_result.get('count', 0)
            print(f"✅ Created VSN June A collection '{vsn_june_collection_id}' with {vsn_june_count} contacts")
            
            # Get details
            vsn_june_details = await get_collection_details(context, vsn_june_collection_id)
            if vsn_june_details.get('success'):
                vsn_june_contacts = vsn_june_details.get('contacts', [])
                print(f"📋 VSN June A contacts ({len(vsn_june_contacts)}):")
                for contact in vsn_june_contacts:
                    email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                    print(f"  • {contact.get('given_name', '')} {contact.get('family_name', '')} - {email} (Created: {contact.get('date_created', 'Unknown')})")
        else:
            print(f"⚠️  VSN June A tag collection returned: {vsn_june_result}")
        
        # Step 4: Create collection with general VSN Guest tag
        print("\n🏷️  Step 4: Creating collection with VSN Guest tag (ID: 4537)...")
        vsn_guest_filter = {
            "tag_ids": [4537]  # "Attended - 2025 - VSN - Guest"
        }
        
        vsn_guest_result = await list_contacts(
            context,
            filters=json.dumps(vsn_guest_filter),
            limit=100
        )
        
        if vsn_guest_result.get('success'):
            vsn_guest_collection_id = vsn_guest_result.get('collection_id')
            vsn_guest_count = vsn_guest_result.get('count', 0)
            print(f"✅ Created VSN Guest collection '{vsn_guest_collection_id}' with {vsn_guest_count} contacts")
            
            # Get details
            vsn_guest_details = await get_collection_details(context, vsn_guest_collection_id)
            if vsn_guest_details.get('success'):
                vsn_guest_contacts = vsn_guest_details.get('contacts', [])
                print(f"📋 VSN Guest contacts ({len(vsn_guest_contacts)}):")
                for contact in vsn_guest_contacts:
                    email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                    created = contact.get('date_created', 'Unknown')
                    print(f"  • {contact.get('given_name', '')} {contact.get('family_name', '')} - {email} (Created: {created})")
        else:
            print(f"⚠️  VSN Guest tag collection returned: {vsn_guest_result}")
        
        # Step 5: Try intersection if we have multiple collections
        print("\n🔗 Step 5: Finding intersections...")
        collections_to_intersect = []
        
        if date_result.get('success'):
            collections_to_intersect.append(date_collection_id)
        if vsn_june_result.get('success'):
            collections_to_intersect.append(vsn_june_collection_id)
        if vsn_guest_result.get('success'):
            collections_to_intersect.append(vsn_guest_collection_id)
        
        if len(collections_to_intersect) >= 2:
            print(f"🔍 Intersecting collections: {collections_to_intersect}")
            intersection_result = await collection_intersect(context, collections_to_intersect)
            
            if intersection_result.get('success'):
                intersection_collection_id = intersection_result.get('collection_id')
                intersection_count = intersection_result.get('count', 0)
                print(f"✅ Created intersection collection '{intersection_collection_id}' with {intersection_count} contacts")
                
                if intersection_count > 0:
                    # Get intersection details
                    intersection_details = await get_collection_details(context, intersection_collection_id)
                    if intersection_details.get('success'):
                        intersection_contacts = intersection_details.get('contacts', [])
                        print(f"\n🎯 FINAL RESULTS - VSN Website Guest Registrations around 6/10/25:")
                        print(f"Found {len(intersection_contacts)} matching contacts:")
                        
                        for i, contact in enumerate(intersection_contacts, 1):
                            email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                            created = contact.get('date_created', 'Unknown')
                            tags = contact.get('tag_ids', [])
                            
                            print(f"\n  {i}. Contact ID: {contact.get('id')}")
                            print(f"     Name: {contact.get('given_name', '')} {contact.get('family_name', '')}")
                            print(f"     Email: {email}")
                            print(f"     Created: {created}")
                            print(f"     Tags: {tags}")
                            
                            # Look for relevant custom fields
                            custom_fields = contact.get('custom_fields', [])
                            relevant_fields = []
                            for field in custom_fields:
                                content = field.get('content', '')
                                if content and any(keyword in str(content).lower() for keyword in ['vsn', 'registration', 'website', 'form']):
                                    relevant_fields.append(field)
                            
                            if relevant_fields:
                                print(f"     Relevant custom fields:")
                                for field in relevant_fields:
                                    print(f"       - {field.get('field_name', 'Unknown')}: {field.get('content', '')}")
                else:
                    print("❌ No contacts found in intersection - try broader criteria")
            else:
                print(f"❌ Intersection failed: {intersection_result.get('error')}")
        else:
            print("⚠️  Not enough collections for intersection analysis")
            
        # Step 6: Alternative approach - check specific contact
        print("\n🔍 Step 6: Checking the specific test contact...")
        test_email_filter = {
            "email": "smhanan+test6@gmail.com"
        }
        
        test_result = await list_contacts(
            context,
            filters=json.dumps(test_email_filter),
            limit=10
        )
        
        if test_result.get('success'):
            test_collection_id = test_result.get('collection_id')
            test_details = await get_collection_details(context, test_collection_id)
            
            if test_details.get('success'):
                test_contacts = test_details.get('contacts', [])
                if test_contacts:
                    test_contact = test_contacts[0]
                    print(f"📧 Test contact analysis:")
                    print(f"   ID: {test_contact.get('id')}")
                    print(f"   Created: {test_contact.get('date_created')}")
                    print(f"   Tags: {test_contact.get('tag_ids', [])}")
                    
                    # Check if any of the target tags are present
                    target_tags = [5031, 4537, 3519]  # VSN-related tags
                    contact_tags = test_contact.get('tag_ids', [])
                    matching_tags = [tag for tag in target_tags if tag in contact_tags]
                    
                    if matching_tags:
                        print(f"   ✅ Contact has VSN tags: {matching_tags}")
                    else:
                        print(f"   ❌ Contact does not have target VSN tags")
                        print(f"   💡 Actual tags: {contact_tags}")
        
        print("\n" + "="*70)
        print("🎯 SUMMARY & RECOMMENDATIONS")
        print("="*70)
        print("Based on the analysis:")
        print("1. Date filtering around 6/10/25 works and finds contacts")
        print("2. VSN-specific tags exist and can be used for filtering")
        print("3. Intersection operations can combine multiple criteria")
        print("4. Custom fields may contain additional form source information")
        print("\nNext steps:")
        print("- Use the identified tag IDs for precise filtering")
        print("- Combine date and tag filters for best results")
        print("- Examine custom fields for additional form tracking data")
        print("- Test with broader date ranges if needed")
        
    except Exception as e:
        print(f"❌ Error in VSN guest investigation: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main execution function"""
    await find_vsn_website_guests()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Form Investigation Script - Investigate form-related filtering capabilities in Keap API
Focus on finding ways to identify contacts who filled out forms like 'VSN Website guest registration'
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.api.client import KeapApiService


class FormInvestigator:
    """Investigates form-related capabilities in the Keap API."""
    
    def __init__(self):
        self.api_service = KeapApiService()
        
    async def step1_contact_schema(self):
        """Step 1: Get contact schema by examining sample contacts."""
        print("=== STEP 1: CONTACT SCHEMA INVESTIGATION ===")
        
        try:
            # Get sample contacts with all fields to understand schema
            print("🔍 Getting sample contacts to analyze schema...")
            contacts_response = await self.api_service.get_contacts(
                limit=5,
                include_custom_fields=True
            )
            
            contacts = contacts_response.get('contacts', []) if isinstance(contacts_response, dict) else []
            
            if contacts:
                print(f"✅ Retrieved {len(contacts)} sample contacts")
                
                # Get detailed contact to see all fields
                first_contact = contacts[0]
                contact_id = first_contact.get('id')
                detailed_contact = await self.api_service.get_contact(contact_id, include_custom_fields=True)
                
                print("📋 Available standard fields:")
                standard_fields = [key for key in detailed_contact.keys() if key != 'custom_fields']
                for field in sorted(standard_fields):
                    print(f"  • {field}")
                
                # Analyze custom fields
                custom_fields = detailed_contact.get('custom_fields', [])
                print(f"\n📋 Custom fields found: {len(custom_fields)}")
                
                # Filter for form-related fields
                form_keywords = ['form', 'source', 'lead', 'registration', 'submit', 'website', 'vsn', 'guest', 'campaign', 'origin']
                form_related_fields = []
                
                for field in custom_fields:
                    field_name = field.get('field_name', '').lower()
                    content = str(field.get('content', '')).lower()
                    
                    # Check if field contains form-related keywords
                    if any(keyword in field_name or keyword in content for keyword in form_keywords):
                        form_related_fields.append(field)
                        print(f"  🎯 FORM-RELATED: {field.get('field_name')} = {field.get('content')}")
                    else:
                        print(f"  • {field.get('field_name')} = {field.get('content')}")
                
                print(f"\n📊 Form-related custom fields found: {len(form_related_fields)}")
                
                return {
                    'custom_fields': custom_fields,
                    'form_related_fields': form_related_fields,
                    'standard_fields': standard_fields,
                    'sample_contact': detailed_contact
                }
            else:
                print("❌ No contacts found to analyze schema")
                return None
                
        except Exception as e:
            print(f"❌ Error getting contact schema: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def step2_search_specific_contact(self):
        """Step 2: Search for smhanan+test6@gmail.com to see actual data structure."""
        print("\n=== STEP 2: SEARCHING FOR SPECIFIC CONTACT ===")
        
        email = "smhanan+test6@gmail.com"
        print(f"🔍 Searching for: {email}")
        
        try:
            # Try multiple search approaches
            print("  Approach 1: Direct email search...")
            contacts_response = await self.api_service.get_contacts(email=email)
            contacts = contacts_response.get('contacts', []) if isinstance(contacts_response, dict) else []
            
            if contacts:
                print(f"  ✅ Found {len(contacts)} contact(s)")
                contact = contacts[0]
                
                # Get detailed contact info
                contact_id = contact.get('id')
                detailed_contact = await self.api_service.get_contact(contact_id)
                
                print(f"  📋 Contact ID: {contact_id}")
                print(f"  👤 Name: {detailed_contact.get('given_name', '')} {detailed_contact.get('family_name', '')}")
                print(f"  📧 Email: {detailed_contact.get('email_addresses', [])}")
                print(f"  📅 Created: {detailed_contact.get('date_created', 'Unknown')}")
                print(f"  🔄 Updated: {detailed_contact.get('last_updated', 'Unknown')}")
                
                # Analyze custom fields
                custom_fields = detailed_contact.get('custom_fields', [])
                print(f"  📊 Custom fields: {len(custom_fields)}")
                
                form_related_data = []
                for field in custom_fields:
                    field_name = field.get('field_name', '')
                    content = field.get('content', '')
                    field_type = field.get('field_type', '')
                    
                    if content and content.strip():
                        print(f"    • {field_name} ({field_type}): {content}")
                        
                        # Check for form-related content
                        content_lower = content.lower()
                        if any(keyword in content_lower for keyword in ['form', 'registration', 'website', 'vsn', 'guest']):
                            form_related_data.append(field)
                            print(f"      🎯 POTENTIALLY FORM-RELATED!")
                
                # Analyze tags
                tag_ids = detailed_contact.get('tag_ids', [])
                print(f"  🏷️  Tags: {tag_ids}")
                
                return {
                    'contact': detailed_contact,
                    'form_related_data': form_related_data,
                    'tag_ids': tag_ids
                }
            else:
                print("  ❌ No contacts found with that email")
                
                # Try broader search
                print("  Approach 2: Broader search...")
                broader_response = await self.api_service.get_contacts(given_name="*smhanan*")
                broader_contacts = broader_response.get('contacts', []) if isinstance(broader_response, dict) else []
                print(f"  Found {len(broader_contacts)} contacts with smhanan in name")
                
                return None
                
        except Exception as e:
            print(f"❌ Error searching for specific contact: {e}")
            return None
    
    async def step3_investigate_tags(self):
        """Step 3: Investigate available tags for form-related filtering."""
        print("\n=== STEP 3: TAG INVESTIGATION ===")
        
        try:
            # Get all tags
            tags_response = await self.api_service.get_tags()
            
            # Handle different response formats
            if isinstance(tags_response, dict):
                tags = tags_response.get('tags', [])
            elif isinstance(tags_response, list):
                tags = tags_response
            else:
                print(f"⚠️  Unexpected tags response format: {type(tags_response)}")
                return []
            
            print(f"📋 Total tags available: {len(tags)}")
            
            # Filter for form-related tags
            form_keywords = ['form', 'registration', 'submit', 'website', 'vsn', 'guest', 'lead', 'source', 'campaign']
            form_related_tags = []
            
            for tag in tags:
                if isinstance(tag, dict):
                    tag_name = tag.get('name', '').lower()
                    description = tag.get('description', '').lower()
                    
                    if any(keyword in tag_name or keyword in description for keyword in form_keywords):
                        form_related_tags.append(tag)
                        print(f"  🎯 FORM-RELATED TAG: {tag.get('name')} (ID: {tag.get('id')})")
                        if tag.get('description'):
                            print(f"    Description: {tag.get('description')}")
                    else:
                        print(f"  • {tag.get('name')} (ID: {tag.get('id')})")
                else:
                    print(f"  ⚠️  Unexpected tag format: {tag}")
            
            print(f"\n📊 Form-related tags found: {len(form_related_tags)}")
            
            return form_related_tags
            
        except Exception as e:
            print(f"❌ Error investigating tags: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def step4_recent_contacts_analysis(self):
        """Step 4: Analyze recent contacts around 6/10/25 for patterns."""
        print("\n=== STEP 4: RECENT CONTACTS ANALYSIS ===")
        
        try:
            # Get recent contacts (last 30 days worth)
            print("🔍 Getting recent contacts...")
            recent_response = await self.api_service.get_contacts(
                limit=50,
                order_by='date_created',
                order_direction='DESC'
            )
            
            recent_contacts = recent_response.get('contacts', []) if isinstance(recent_response, dict) else []
            print(f"📋 Retrieved {len(recent_contacts)} recent contacts")
            
            # Analyze patterns
            form_patterns = {}
            june_contacts = []
            
            for contact in recent_contacts:
                contact_id = contact.get('id')
                date_created = contact.get('date_created', '')
                
                # Check if created in June 2025
                if '2025-06' in date_created:
                    june_contacts.append(contact)
                    
                    # Get detailed contact
                    detailed = await self.api_service.get_contact(contact_id)
                    
                    print(f"  📅 June 2025 contact: {detailed.get('given_name', '')} {detailed.get('family_name', '')}")
                    print(f"    Created: {date_created}")
                    
                    # Analyze custom fields
                    custom_fields = detailed.get('custom_fields', [])
                    for field in custom_fields:
                        field_name = field.get('field_name', '')
                        content = field.get('content', '')
                        
                        if content and content.strip():
                            if field_name not in form_patterns:
                                form_patterns[field_name] = []
                            form_patterns[field_name].append(content)
                            print(f"    • {field_name}: {content}")
            
            print(f"\n📊 June 2025 contacts found: {len(june_contacts)}")
            print(f"📊 Custom field patterns identified: {len(form_patterns)}")
            
            # Show patterns
            for field_name, values in form_patterns.items():
                unique_values = list(set(values))
                print(f"  {field_name}: {len(unique_values)} unique values")
                for value in unique_values[:3]:
                    print(f"    - {value}")
            
            return {
                'june_contacts': june_contacts,
                'form_patterns': form_patterns
            }
            
        except Exception as e:
            print(f"❌ Error analyzing recent contacts: {e}")
            return {}
    
    async def step5_lead_source_investigation(self):
        """Step 5: Investigate lead sources which might track form submissions."""
        print("\n=== STEP 5: LEAD SOURCE INVESTIGATION ===")
        
        try:
            # Get some contacts to check lead source patterns
            contacts_response = await self.api_service.get_contacts(limit=20)
            contacts = contacts_response.get('contacts', []) if isinstance(contacts_response, dict) else []
            
            lead_sources = {}
            
            for contact in contacts:
                lead_source_id = contact.get('lead_source_id')
                if lead_source_id:
                    if lead_source_id not in lead_sources:
                        lead_sources[lead_source_id] = 0
                    lead_sources[lead_source_id] += 1
            
            print(f"📊 Lead source IDs found: {len(lead_sources)}")
            for source_id, count in lead_sources.items():
                print(f"  Lead Source {source_id}: {count} contacts")
            
            return lead_sources
            
        except Exception as e:
            print(f"❌ Error investigating lead sources: {e}")
            return {}
    
    async def generate_recommendations(self, schema_info, contact_data, tags, recent_analysis, lead_sources):
        """Generate actionable recommendations for form filtering."""
        print("\n" + "="*80)
        print("🎯 FORM FILTERING RECOMMENDATIONS")
        print("="*80)
        
        print("\n1. CUSTOM FIELD FILTERING:")
        if schema_info and schema_info.get('form_related_fields'):
            print("   ✅ Form-related custom fields are available:")
            for field in schema_info['form_related_fields'][:5]:
                field_name = field.get('field_name')
                print(f"   • Use '{field_name}' for filtering form submissions")
        else:
            print("   ⚠️  No obvious form-related custom fields found")
        
        print("\n2. TAG-BASED FILTERING:")
        if tags:
            print("   ✅ Form-related tags are available:")
            for tag in tags[:5]:
                print(f"   • Filter by tag '{tag.get('name')}' (ID: {tag.get('id')})")
        else:
            print("   ⚠️  No obvious form-related tags found")
        
        print("\n3. DATE-BASED FILTERING:")
        if recent_analysis and recent_analysis.get('june_contacts'):
            print(f"   ✅ Found {len(recent_analysis['june_contacts'])} contacts from June 2025")
            print("   • Use date_created filter for 2025-06-10 timeframe")
        else:
            print("   ⚠️  No June 2025 contacts found in recent data")
        
        print("\n4. LEAD SOURCE FILTERING:")
        if lead_sources:
            print(f"   ✅ Found {len(lead_sources)} different lead sources")
            print("   • Form submissions might be tracked via lead_source_id")
        else:
            print("   ⚠️  No lead source patterns identified")
        
        print("\n5. RECOMMENDED FILTERING STRATEGY:")
        print("   For finding 'VSN Website guest registration' contacts from 6/10/25:")
        print("   ")
        print("   A. DATE + EMAIL PATTERN:")
        print("      - Filter contacts created between 2025-06-09 and 2025-06-11")
        print("      - Look for email patterns that match form submission emails")
        print("   ")
        print("   B. CUSTOM FIELD SEARCH:")
        if schema_info and schema_info.get('form_related_fields'):
            print("      - Search custom fields for 'VSN' or 'website' or 'guest registration'")
            for field in schema_info['form_related_fields'][:3]:
                print(f"      - Check '{field.get('field_name')}' field")
        print("   ")
        print("   C. TAG COMBINATION:")
        if tags:
            print("      - Apply form-related tags as filters")
            for tag in tags[:3]:
                print(f"      - Use tag '{tag.get('name')}' (ID: {tag.get('id')})")
        print("   ")
        print("   D. MULTI-STEP APPROACH:")
        print("      1. Create collection with date range (6/10/25 ±1 day)")
        print("      2. Apply email pattern or custom field filters")
        print("      3. Use collection intersection for precise targeting")
        print("      4. Validate results manually")
        
        print("\n6. NEXT STEPS:")
        print("   1. Test the filtering approach with a small date range")
        print("   2. Examine the actual contact data for VSN-related content")
        print("   3. Create collections using the MCP tools")
        print("   4. Use collection operations to refine results")


async def main():
    """Main investigation workflow."""
    print("🚀 FORM INVESTIGATION STARTING")
    print("="*50)
    
    investigator = FormInvestigator()
    
    try:
        # Step 1: Contact Schema
        schema_info = await investigator.step1_contact_schema()
        
        # Step 2: Specific Contact Search
        contact_data = await investigator.step2_search_specific_contact()
        
        # Step 3: Tag Investigation
        tags = await investigator.step3_investigate_tags()
        
        # Step 4: Recent Contacts Analysis
        recent_analysis = await investigator.step4_recent_contacts_analysis()
        
        # Step 5: Lead Source Investigation
        lead_sources = await investigator.step5_lead_source_investigation()
        
        # Generate Recommendations
        await investigator.generate_recommendations(
            schema_info, contact_data, tags, recent_analysis, lead_sources
        )
        
        print("\n✅ INVESTIGATION COMPLETE!")
        
    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
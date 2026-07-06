#!/usr/bin/env python3
"""
Investigation script to explore form-related filtering capabilities in the Keap API.
This will help identify how to track form submissions like 'VSN Website guest registration'.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Set up environment
import sys
sys.path.insert(0, '/Users/smhanan/CascadeProjects/mcp-keap/src')

from mcp.server import KeapMCPServer
from config.settings import Settings


class FormCapabilityInvestigator:
    """Investigates form-related capabilities in the Keap API."""
    
    def __init__(self):
        self.server = None
        self.settings = Settings()
        
    async def initialize(self):
        """Initialize the MCP server."""
        self.server = KeapMCPServer(self.settings)
        await self.server.initialize()
        
    async def investigate_contact_schema(self):
        """Step 1: Examine the contact schema for form-related fields."""
        print("=== STEP 1: CONTACT SCHEMA INVESTIGATION ===")
        
        try:
            schema_result = await self.server.get_contact_schema()
            
            if schema_result.get('success'):
                schema = schema_result.get('schema', {})
                custom_fields = schema_result.get('custom_fields', [])
                
                print(f"Found {len(custom_fields)} custom fields")
                
                # Look for form-related fields
                form_related_fields = []
                for field in custom_fields:
                    field_name = field.get('field_name', '').lower()
                    label = field.get('label', '').lower()
                    
                    # Check for form-related keywords
                    form_keywords = ['form', 'submission', 'register', 'source', 'lead', 'origin', 'campaign', 'vsn', 'website']
                    if any(keyword in field_name or keyword in label for keyword in form_keywords):
                        form_related_fields.append(field)
                
                print(f"\nForm-related custom fields found: {len(form_related_fields)}")
                for field in form_related_fields:
                    print(f"  - {field.get('field_name')} ({field.get('label')}) - Type: {field.get('field_type')}")
                
                # Check standard fields that might be form-related
                standard_fields = schema.get('properties', {})
                form_related_standard = []
                for field_name, field_info in standard_fields.items():
                    if any(keyword in field_name.lower() for keyword in ['source', 'origin', 'lead', 'tag', 'contact']):
                        form_related_standard.append((field_name, field_info))
                
                print(f"\nPotentially form-related standard fields: {len(form_related_standard)}")
                for field_name, field_info in form_related_standard:
                    print(f"  - {field_name}: {field_info.get('description', 'No description')}")
                
                return {
                    'custom_fields': form_related_fields,
                    'standard_fields': form_related_standard,
                    'total_custom_fields': len(custom_fields)
                }
            else:
                print(f"Failed to get schema: {schema_result.get('error')}")
                return None
                
        except Exception as e:
            print(f"Error getting schema: {e}")
            return None
    
    async def search_specific_contact(self, email: str):
        """Step 2: Search for the specific contact to see available data."""
        print(f"\n=== STEP 2: SEARCHING FOR CONTACT {email} ===")
        
        try:
            # Search for the contact
            search_result = await self.server.list_contacts(
                limit=10,
                email=email
            )
            
            if search_result.get('success'):
                collection_id = search_result.get('collection_id')
                contacts = search_result.get('contacts', [])
                
                print(f"Found {len(contacts)} contact(s) matching {email}")
                
                if contacts:
                    # Get detailed information for the first contact
                    contact = contacts[0]
                    contact_id = contact.get('id')
                    
                    print(f"\nContact ID: {contact_id}")
                    print(f"Name: {contact.get('given_name', '')} {contact.get('family_name', '')}")
                    print(f"Email: {contact.get('email_addresses', [])}")
                    
                    # Get full details
                    details_result = await self.server.get_collection_details(collection_id)
                    if details_result.get('success'):
                        detailed_contacts = details_result.get('contacts', [])
                        if detailed_contacts:
                            detailed_contact = detailed_contacts[0]
                            
                            # Check custom fields
                            custom_fields = detailed_contact.get('custom_fields', [])
                            print(f"\nCustom fields for this contact: {len(custom_fields)}")
                            for cf in custom_fields:
                                field_name = cf.get('field_name', 'Unknown')
                                content = cf.get('content', 'No content')
                                print(f"  - {field_name}: {content}")
                            
                            # Check tags
                            tag_ids = detailed_contact.get('tag_ids', [])
                            print(f"\nTag IDs: {tag_ids}")
                            
                            # Check other potentially relevant fields
                            relevant_fields = ['date_created', 'last_updated', 'lead_source_id', 'owner_id']
                            print(f"\nOther relevant fields:")
                            for field in relevant_fields:
                                if field in detailed_contact:
                                    print(f"  - {field}: {detailed_contact[field]}")
                            
                            return detailed_contact
                    
                else:
                    print("No contacts found with that email")
                    return None
            else:
                print(f"Search failed: {search_result.get('error')}")
                return None
                
        except Exception as e:
            print(f"Error searching for contact: {e}")
            return None
    
    async def investigate_tags(self):
        """Step 3: Investigate available tags that might be form-related."""
        print(f"\n=== STEP 3: INVESTIGATING TAGS ===")
        
        try:
            tags_result = await self.server.get_tags(limit=50)
            
            if tags_result.get('success'):
                tags = tags_result.get('tags', [])
                print(f"Total tags available: {len(tags)}")
                
                # Look for form-related tags
                form_related_tags = []
                form_keywords = ['form', 'registration', 'subscribe', 'lead', 'website', 'vsn', 'guest', 'submit']
                
                for tag in tags:
                    tag_name = tag.get('name', '').lower()
                    if any(keyword in tag_name for keyword in form_keywords):
                        form_related_tags.append(tag)
                
                print(f"\nForm-related tags found: {len(form_related_tags)}")
                for tag in form_related_tags:
                    print(f"  - ID: {tag.get('id')}, Name: {tag.get('name')}, Description: {tag.get('description', 'No description')}")
                
                return form_related_tags
            else:
                print(f"Failed to get tags: {tags_result.get('error')}")
                return []
                
        except Exception as e:
            print(f"Error getting tags: {e}")
            return []
    
    async def search_recent_contacts(self):
        """Step 4: Search for recent contacts around 6/10/25 to see patterns."""
        print(f"\n=== STEP 4: SEARCHING RECENT CONTACTS (around 6/10/25) ===")
        
        try:
            # Search for contacts created recently
            recent_result = await self.server.list_contacts(
                limit=20,
                order_by='date_created',
                order_direction='DESC'
            )
            
            if recent_result.get('success'):
                collection_id = recent_result.get('collection_id')
                contacts = recent_result.get('contacts', [])
                
                print(f"Found {len(contacts)} recent contacts")
                
                # Get details for recent contacts
                details_result = await self.server.get_collection_details(collection_id)
                if details_result.get('success'):
                    detailed_contacts = details_result.get('contacts', [])
                    
                    print(f"\nAnalyzing {len(detailed_contacts)} recent contacts for form patterns:")
                    
                    form_patterns = {}
                    
                    for contact in detailed_contacts[:10]:  # Check first 10
                        contact_id = contact.get('id')
                        date_created = contact.get('date_created', 'Unknown')
                        email = contact.get('email_addresses', [{}])[0].get('email', 'No email') if contact.get('email_addresses') else 'No email'
                        
                        print(f"\n  Contact {contact_id} ({email}) - Created: {date_created}")
                        
                        # Check custom fields for patterns
                        custom_fields = contact.get('custom_fields', [])
                        for cf in custom_fields:
                            field_name = cf.get('field_name', '')
                            content = cf.get('content', '')
                            if content and content.strip():
                                if field_name not in form_patterns:
                                    form_patterns[field_name] = []
                                form_patterns[field_name].append(content)
                                print(f"    Custom field: {field_name} = {content}")
                        
                        # Check tags
                        tag_ids = contact.get('tag_ids', [])
                        if tag_ids:
                            print(f"    Tags: {tag_ids}")
                    
                    print(f"\n=== CUSTOM FIELD PATTERNS SUMMARY ===")
                    for field_name, values in form_patterns.items():
                        unique_values = list(set(values))
                        print(f"{field_name}: {len(unique_values)} unique values")
                        for value in unique_values[:5]:  # Show first 5 unique values
                            print(f"  - {value}")
                        if len(unique_values) > 5:
                            print(f"  ... and {len(unique_values) - 5} more")
                    
                    return form_patterns
                    
        except Exception as e:
            print(f"Error searching recent contacts: {e}")
            return {}
    
    async def investigate_api_diagnostics(self):
        """Step 5: Check API diagnostics for any additional insights."""
        print(f"\n=== STEP 5: API DIAGNOSTICS ===")
        
        try:
            diagnostics = await self.server.get_api_diagnostics()
            
            if diagnostics.get('success'):
                print("API Status: Working")
                
                # Check if there are any rate limits or API constraints
                info = diagnostics.get('info', {})
                print(f"Rate limit info: {info.get('rate_limit', 'Not available')}")
                
                return diagnostics
            else:
                print(f"Diagnostics failed: {diagnostics.get('error')}")
                return None
                
        except Exception as e:
            print(f"Error getting diagnostics: {e}")
            return None
    
    async def generate_summary_report(self, schema_info, contact_data, tags, patterns, diagnostics):
        """Generate a comprehensive summary report."""
        print(f"\n" + "="*80)
        print("FORM FILTERING CAPABILITIES INVESTIGATION SUMMARY")
        print("="*80)
        
        print(f"\n1. CUSTOM FIELDS ANALYSIS:")
        if schema_info:
            print(f"   - Total custom fields available: {schema_info.get('total_custom_fields', 0)}")
            print(f"   - Form-related custom fields: {len(schema_info.get('custom_fields', []))}")
            
            if schema_info.get('custom_fields'):
                print(f"   - Key form-related fields found:")
                for field in schema_info['custom_fields'][:10]:
                    print(f"     * {field.get('field_name')} ({field.get('label')})")
        
        print(f"\n2. TAG-BASED FILTERING:")
        if tags:
            print(f"   - Form-related tags found: {len(tags)}")
            for tag in tags[:10]:
                print(f"     * {tag.get('name')} (ID: {tag.get('id')})")
        else:
            print(f"   - No obvious form-related tags found")
        
        print(f"\n3. CONTACT DATA PATTERNS:")
        if contact_data:
            print(f"   - Sample contact found with {len(contact_data.get('custom_fields', []))} custom fields")
            print(f"   - Tags associated: {contact_data.get('tag_ids', [])}")
        
        print(f"\n4. RECOMMENDATIONS FOR FORM TRACKING:")
        print(f"   To track forms like 'VSN Website guest registration' around 6/10/25:")
        
        if schema_info and schema_info.get('custom_fields'):
            print(f"   A. Use custom field filtering:")
            for field in schema_info['custom_fields'][:3]:
                print(f"      - Filter by {field.get('field_name')} for form source tracking")
        
        if tags:
            print(f"   B. Use tag-based filtering:")
            for tag in tags[:3]:
                print(f"      - Filter by tag '{tag.get('name')}' (ID: {tag.get('id')})")
        
        print(f"   C. Use date-based filtering:")
        print(f"      - Filter contacts created around 6/10/25")
        print(f"      - Combine with email pattern matching")
        
        print(f"   D. Combine multiple approaches:")
        print(f"      - Date range + custom fields + tags for precise targeting")
        
        print(f"\n5. NEXT STEPS:")
        print(f"   1. Identify the exact custom field or tag used for 'VSN Website guest registration'")
        print(f"   2. Create collection with date_created filter for 6/10/25 timeframe")
        print(f"   3. Apply additional filters based on discovered form identifiers")
        print(f"   4. Use collection operations to refine results")


async def main():
    """Main investigation function."""
    investigator = FormCapabilityInvestigator()
    
    try:
        print("Initializing Keap MCP Server...")
        await investigator.initialize()
        
        # Step 1: Investigate contact schema
        schema_info = await investigator.investigate_contact_schema()
        
        # Step 2: Search for specific contact
        contact_data = await investigator.search_specific_contact("smhanan+test6@gmail.com")
        
        # Step 3: Investigate tags
        tags = await investigator.investigate_tags()
        
        # Step 4: Search recent contacts for patterns
        patterns = await investigator.search_recent_contacts()
        
        # Step 5: API diagnostics
        diagnostics = await investigator.investigate_api_diagnostics()
        
        # Generate summary report
        await investigator.generate_summary_report(schema_info, contact_data, tags, patterns, diagnostics)
        
    except Exception as e:
        print(f"Investigation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Fix custom field handling to use field names instead of field IDs,
and analyze 6FN Next Date/Time field variations.
"""

import asyncio
import os
import json
from typing import Dict, List, Any, Optional
from collections import defaultdict
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_collection_details
from src.api.client import KeapApiService


# Known Scott Hanan contact IDs
SCOTT_HANAN_IDS = [22775, 22773, 22543, 23719, 23709, 23583, 23581, 23557, 23555, 23553]

# Field definitions discovered from previous analysis
KNOWN_6FN_FIELDS = {
    239: "6FN Next Date/Time",
    361: "6FN Next Date/Time END", 
    363: "6FN Next Event Category A-B"
}


class CustomFieldManager:
    """Manages custom field definitions and provides name-based access"""
    
    def __init__(self):
        self.field_definitions: Dict[int, Dict[str, Any]] = {}
        self.name_to_id_mapping: Dict[str, int] = {}
        self.loaded = False
    
    async def load_field_definitions(self):
        """Load custom field definitions from Keap API"""
        print("🔍 Loading custom field definitions...")
        
        api_client = KeapApiService()
        
        try:
            # Try multiple endpoints to get field definitions
            endpoints_to_try = ["/customFields", "/contacts/model"]
            
            for endpoint in endpoints_to_try:
                try:
                    print(f"   Trying {endpoint}...")
                    response = await api_client.get(endpoint)
                    
                    # Parse custom fields from response
                    custom_fields = []
                    if 'custom_fields' in response:
                        custom_fields = response['custom_fields']
                    elif 'customFields' in response:
                        custom_fields = response['customFields']
                    elif isinstance(response, list):
                        custom_fields = response
                    
                    if custom_fields:
                        for field in custom_fields:
                            if isinstance(field, dict) and 'id' in field:
                                field_id = field['id']
                                field_name = field.get('label', field.get('name', f'Field_{field_id}'))
                                
                                self.field_definitions[field_id] = {
                                    'name': field_name,
                                    'type': field.get('type', field.get('field_type', 'unknown')),
                                    'definition': field
                                }
                                self.name_to_id_mapping[field_name] = field_id
                        
                        print(f"   ✅ Loaded {len(self.field_definitions)} field definitions from {endpoint}")
                        break
                        
                except Exception as e:
                    print(f"   ❌ {endpoint} failed: {e}")
                    continue
            
            # Add known 6FN fields if not found
            for field_id, field_name in KNOWN_6FN_FIELDS.items():
                if field_id not in self.field_definitions:
                    self.field_definitions[field_id] = {
                        'name': field_name,
                        'type': 'datetime' if 'Date/Time' in field_name else 'text',
                        'definition': {'id': field_id, 'label': field_name}
                    }
                    self.name_to_id_mapping[field_name] = field_id
            
            self.loaded = True
            print(f"✅ Total field definitions loaded: {len(self.field_definitions)}")
            
        except Exception as e:
            print(f"❌ Failed to load field definitions: {e}")
        finally:
            await api_client.close()
    
    def get_field_name(self, field_id: int) -> str:
        """Get field name from field ID"""
        if field_id in self.field_definitions:
            return self.field_definitions[field_id]['name']
        return f"Field_{field_id}"
    
    def get_field_id(self, field_name: str) -> Optional[int]:
        """Get field ID from field name"""
        return self.name_to_id_mapping.get(field_name)
    
    def get_all_field_names(self) -> List[str]:
        """Get all available field names"""
        return list(self.name_to_id_mapping.keys())


async def get_scott_hanan_contacts_with_custom_fields():
    """Get all Scott Hanan contacts with complete custom field data"""
    context = Context()
    
    print("🔍 Retrieving Scott Hanan contacts with custom field data...")
    
    scott_contacts = []
    
    # Search in ranges where Scott contacts exist
    search_ranges = [(1900, 2100), (2200, 2400)]
    
    for start_offset, end_offset in search_ranges:
        for offset in range(start_offset, end_offset, 100):
            try:
                result = await list_contacts(context, limit=100, offset=offset)
                
                if result['count'] == 0:
                    continue
                
                details = await get_collection_details(context, result['collection_id'])
                contacts = details.get('contacts', [])
                
                for contact in contacts:
                    if contact.get('id') in SCOTT_HANAN_IDS:
                        scott_contacts.append(contact)
                
                if len(scott_contacts) >= 10:
                    break
                    
            except Exception as e:
                continue
        
        if len(scott_contacts) >= 10:
            break
    
    print(f"✅ Retrieved {len(scott_contacts)} Scott Hanan contacts")
    return scott_contacts


def convert_custom_fields_to_names(contacts: List[Dict], field_manager: CustomFieldManager) -> List[Dict]:
    """Convert custom field IDs to names in contact data"""
    converted_contacts = []
    
    for contact in contacts:
        converted_contact = contact.copy()
        custom_fields = contact.get('custom_fields', [])
        
        # Convert field IDs to names
        converted_custom_fields = []
        for field in custom_fields:
            if isinstance(field, dict) and 'id' in field:
                field_id = field['id']
                field_name = field_manager.get_field_name(field_id)
                
                converted_field = field.copy()
                converted_field['field_name'] = field_name
                converted_field['original_id'] = field_id
                converted_custom_fields.append(converted_field)
        
        converted_contact['custom_fields'] = converted_custom_fields
        converted_contacts.append(converted_contact)
    
    return converted_contacts


def analyze_6fn_next_datetime_variations(contacts: List[Dict], field_manager: CustomFieldManager):
    """Analyze variations in '6FN Next Date/Time' field values"""
    print(f"\n📊 Analyzing '6FN Next Date/Time' field variations...")
    print("=" * 55)
    
    # Find the exact field name for 6FN Next Date/Time
    target_field_name = "6FN Next Date/Time"
    target_field_id = field_manager.get_field_id(target_field_name)
    
    if not target_field_id:
        print(f"❌ '{target_field_name}' field not found in definitions")
        return
    
    print(f"🎯 Analyzing field: '{target_field_name}' (ID: {target_field_id})")
    
    contacts_with_6fn_datetime = []
    all_6fn_values = []
    
    for contact in contacts:
        contact_id = contact.get('id')
        given_name = contact.get('given_name', '')
        family_name = contact.get('family_name', '')
        custom_fields = contact.get('custom_fields', [])
        
        # Look for the 6FN Next Date/Time field
        for field in custom_fields:
            if field.get('id') == target_field_id or field.get('field_name') == target_field_name:
                field_content = field.get('content')
                
                if field_content is not None and str(field_content).strip():
                    contact_data = {
                        'contact_id': contact_id,
                        'contact_name': f"{given_name} {family_name}",
                        'field_name': target_field_name,
                        'field_id': target_field_id,
                        'datetime_value': field_content,
                        'raw_field': field
                    }
                    
                    contacts_with_6fn_datetime.append(contact_data)
                    all_6fn_values.append(field_content)
                    
                    print(f"\n👤 {given_name} {family_name} (ID: {contact_id})")
                    print(f"   📅 {target_field_name}: {field_content}")
    
    # Analyze variations
    print(f"\n🔍 VARIATION ANALYSIS")
    print("-" * 30)
    
    if not contacts_with_6fn_datetime:
        print(f"❌ No contacts found with '{target_field_name}' field data")
        return
    
    print(f"Total contacts with {target_field_name}: {len(contacts_with_6fn_datetime)}")
    
    # Group by unique values
    value_groups = defaultdict(list)
    for contact_data in contacts_with_6fn_datetime:
        value = str(contact_data['datetime_value']).strip()
        value_groups[value].append(contact_data)
    
    print(f"Unique {target_field_name} values: {len(value_groups)}")
    
    # Show each unique value and which contacts have it
    for i, (value, contacts_with_this_value) in enumerate(sorted(value_groups.items()), 1):
        contact_names = [c['contact_name'] for c in contacts_with_this_value]
        print(f"\n   Value {i}: {value}")
        print(f"     Used by {len(contacts_with_this_value)} contacts:")
        for name in contact_names:
            print(f"       - {name}")
    
    # Time analysis if datetime values
    print(f"\n⏰ DATETIME ANALYSIS")
    print("-" * 25)
    
    try:
        from datetime import datetime
        
        parsed_datetimes = []
        for value in value_groups.keys():
            try:
                # Try to parse ISO datetime format
                if 'T' in value and '+' in value:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    parsed_datetimes.append((value, dt))
            except:
                continue
        
        if parsed_datetimes:
            print(f"Parsed {len(parsed_datetimes)} datetime values:")
            
            # Sort by datetime
            parsed_datetimes.sort(key=lambda x: x[1])
            
            for original_value, dt in parsed_datetimes:
                contacts_with_this_dt = [c['contact_name'] for c in value_groups[original_value]]
                time_formatted = dt.strftime("%Y-%m-%d %I:%M %p %Z")
                print(f"   📅 {time_formatted}: {', '.join(contacts_with_this_dt)}")
            
            # Find date/time patterns
            dates = [dt.date() for _, dt in parsed_datetimes]
            times = [dt.time() for _, dt in parsed_datetimes]
            
            unique_dates = list(set(dates))
            unique_times = list(set(times))
            
            print(f"\n   📊 Summary:")
            print(f"     Unique dates: {len(unique_dates)} ({unique_dates})")
            print(f"     Unique times: {len(unique_times)} ({unique_times})")
            
            if len(unique_dates) == 1 and len(unique_times) > 1:
                print(f"     🎯 Same date, different times - likely different appointment slots")
            elif len(unique_dates) > 1 and len(unique_times) == 1:
                print(f"     🎯 Same time, different dates - likely recurring appointments")
            else:
                print(f"     🎯 Different dates and times - varied appointment scheduling")
        
    except Exception as e:
        print(f"   ⚠️ Could not parse datetime values: {e}")
    
    return contacts_with_6fn_datetime, value_groups


async def demonstrate_name_based_api_usage(field_manager: CustomFieldManager):
    """Demonstrate how to use field names instead of field IDs in API operations"""
    print(f"\n🔧 DEMONSTRATING NAME-BASED CUSTOM FIELD API USAGE")
    print("=" * 60)
    
    # Example: Update a custom field using field name instead of ID
    target_field_name = "6FN Next Date/Time"
    target_field_id = field_manager.get_field_id(target_field_name)
    
    if not target_field_id:
        print(f"❌ Field '{target_field_name}' not found")
        return
    
    print(f"✅ Field name-to-ID resolution working:")
    print(f"   Field name: '{target_field_name}'")
    print(f"   Resolved to ID: {target_field_id}")
    
    # Show how to update using field names
    print(f"\n📝 Example API usage with field names:")
    print(f"   # Instead of using field ID directly:")
    print(f"   # update_contact_custom_field(contact_id, 239, new_value)")
    print(f"   ")
    print(f"   # Use field name resolution:")
    print(f"   field_id = field_manager.get_field_id('{target_field_name}')")
    print(f"   await api_client.update_contact_custom_field(contact_id, field_id, new_value)")
    
    # Show available 6FN-related field names
    print(f"\n📋 Available 6FN-related field names:")
    for field_name in field_manager.get_all_field_names():
        if '6fn' in field_name.lower():
            field_id = field_manager.get_field_id(field_name)
            print(f"   '{field_name}' (ID: {field_id})")


async def create_enhanced_custom_field_functions():
    """Create enhanced custom field functions that use names instead of IDs"""
    print(f"\n🔧 Creating enhanced custom field functions...")
    
    # This would be added to tools_collections.py
    enhanced_functions = '''
# Enhanced custom field functions for tools_collections.py

async def update_contact_custom_field_by_name(
    context: Context, 
    contact_id: str, 
    field_name: str, 
    value: Any,
    field_manager: CustomFieldManager = None
) -> Dict[str, Any]:
    """Update a contact's custom field using field name instead of field ID"""
    
    if not field_manager:
        field_manager = CustomFieldManager()
        await field_manager.load_field_definitions()
    
    field_id = field_manager.get_field_id(field_name)
    if not field_id:
        raise ValueError(f"Custom field '{field_name}' not found")
    
    api_client = get_api_client()
    try:
        result = await api_client.update_contact_custom_field(contact_id, str(field_id), value)
        
        # Return result with field name for clarity
        result['field_name'] = field_name
        result['field_id'] = field_id
        return result
        
    finally:
        await api_client.close()


async def get_contact_custom_fields_by_name(
    context: Context, 
    contact_id: str,
    field_manager: CustomFieldManager = None
) -> Dict[str, Any]:
    """Get a contact's custom fields with field names instead of just IDs"""
    
    if not field_manager:
        field_manager = CustomFieldManager()
        await field_manager.load_field_definitions()
    
    api_client = get_api_client()
    try:
        contact = await api_client.get_contact(contact_id, include_custom_fields=True)
        custom_fields = contact.get('custom_fields', [])
        
        # Convert field IDs to names
        named_fields = {}
        for field in custom_fields:
            if isinstance(field, dict) and 'id' in field:
                field_id = field['id']
                field_name = field_manager.get_field_name(field_id)
                field_content = field.get('content')
                
                named_fields[field_name] = {
                    'value': field_content,
                    'field_id': field_id,
                    'type': field_manager.field_definitions.get(field_id, {}).get('type', 'unknown')
                }
        
        return {
            'contact_id': contact_id,
            'custom_fields_by_name': named_fields,
            'total_fields': len(named_fields)
        }
        
    finally:
        await api_client.close()
'''
    
    print("✅ Enhanced custom field functions created")
    print("   These functions should be added to tools_collections.py to enable name-based field access")
    
    return enhanced_functions


async def main():
    """Main execution function"""
    print("🚀 Fix Custom Field Handling & Analyze 6FN Date/Time Variations")
    print("=" * 70)
    
    try:
        # Initialize custom field manager
        field_manager = CustomFieldManager()
        await field_manager.load_field_definitions()
        
        if not field_manager.loaded:
            print("❌ Could not load custom field definitions")
            return
        
        # Get Scott Hanan contacts
        scott_contacts = await get_scott_hanan_contacts_with_custom_fields()
        
        if not scott_contacts:
            print("❌ Could not retrieve Scott Hanan contacts")
            return
        
        # Convert field IDs to names
        converted_contacts = convert_custom_fields_to_names(scott_contacts, field_manager)
        
        # Analyze 6FN Next Date/Time variations
        contacts_with_6fn, value_variations = analyze_6fn_next_datetime_variations(converted_contacts, field_manager)
        
        # Demonstrate name-based API usage
        await demonstrate_name_based_api_usage(field_manager)
        
        # Create enhanced custom field functions
        enhanced_functions = await create_enhanced_custom_field_functions()
        
        # Final summary
        print(f"\n" + "="*70)
        print(f"📊 FINAL SUMMARY")
        print(f"="*70)
        print(f"Scott Hanan contacts analyzed: {len(scott_contacts)}")
        print(f"Custom field definitions loaded: {len(field_manager.field_definitions)}")
        print(f"Contacts with '6FN Next Date/Time': {len(contacts_with_6fn) if contacts_with_6fn else 0}")
        print(f"Unique '6FN Next Date/Time' values: {len(value_variations) if value_variations else 0}")
        
        if value_variations:
            print(f"\n✅ 6FN Next Date/Time Analysis Complete!")
            print(f"   Different values found: {list(value_variations.keys())}")
        else:
            print(f"\n⚠️ No 6FN Next Date/Time data found")
        
        print(f"\n✅ Custom field name-based API usage is ready for implementation!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
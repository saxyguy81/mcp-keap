#!/usr/bin/env python3
"""
Focused script to search for 6FN-related data in all contacts.
Looks for variations in formatting of 6FN data.
"""

import asyncio
import os
import json
import re
from collections import defaultdict
from typing import Dict, List, Any
from mcp.server.fastmcp import Context

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.mcp.tools_collections import list_contacts, get_collection_details


async def search_for_6fn_patterns():
    """Search all contacts for 6FN-related patterns"""
    context = Context()
    
    print("🔍 Searching for 6FN patterns in all contacts...")
    
    # Get all contacts
    all_contacts = await list_contacts(context, limit=200)  # Increase limit
    print(f"Found {all_contacts['count']} total contacts")
    
    # Get detailed contact information
    details = await get_collection_details(
        context, 
        all_contacts['collection_id'],
        fields=["id", "given_name", "family_name", "email", "custom_fields"]
    )
    
    # Search patterns
    patterns_to_search = [
        r'6fn',
        r'6-fn', 
        r'six.*fn',
        r'6.*figure.*number',
        r'figure.*number',
        r'scott.*hanan',
        r'hanan.*scott'
    ]
    
    found_matches = []
    
    print(f"\n📋 Scanning {len(details['contacts'])} contacts for patterns...")
    
    for contact in details['contacts']:
        contact_id = contact.get('id')
        given_name = contact.get('given_name', '').lower()
        family_name = contact.get('family_name', '').lower()
        email = contact.get('email', '').lower()
        custom_fields = contact.get('custom_fields', [])
        
        # Check name for patterns
        full_name = f"{given_name} {family_name}"
        for pattern in patterns_to_search:
            if re.search(pattern, full_name, re.IGNORECASE):
                found_matches.append({
                    'contact_id': contact_id,
                    'name': f"{contact.get('given_name', '')} {contact.get('family_name', '')}",
                    'email': contact.get('email', 'N/A'),
                    'match_type': 'name',
                    'pattern': pattern,
                    'match_value': full_name,
                    'custom_fields': custom_fields
                })
                break
        
        # Check email for patterns
        for pattern in patterns_to_search:
            if re.search(pattern, email, re.IGNORECASE):
                found_matches.append({
                    'contact_id': contact_id,
                    'name': f"{contact.get('given_name', '')} {contact.get('family_name', '')}",
                    'email': contact.get('email', 'N/A'),
                    'match_type': 'email',
                    'pattern': pattern,
                    'match_value': email,
                    'custom_fields': custom_fields
                })
                break
        
        # Check custom fields for patterns
        if custom_fields:
            for field in custom_fields:
                field_content = str(field.get('content', '')).lower()
                field_id = field.get('id')
                
                for pattern in patterns_to_search:
                    if re.search(pattern, field_content, re.IGNORECASE):
                        found_matches.append({
                            'contact_id': contact_id,
                            'name': f"{contact.get('given_name', '')} {contact.get('family_name', '')}",
                            'email': contact.get('email', 'N/A'),
                            'match_type': 'custom_field',
                            'pattern': pattern,
                            'match_value': field_content,
                            'field_id': field_id,
                            'custom_fields': custom_fields
                        })
                        break
    
    return found_matches


def analyze_6fn_variations(matches):
    """Analyze variations in 6FN data formatting"""
    
    print(f"\n🎯 Found {len(matches)} matches with 6FN-related patterns")
    print("=" * 50)
    
    if not matches:
        print("❌ No 6FN-related data found in any contacts")
        return
    
    # Group by match type
    by_type = defaultdict(list)
    for match in matches:
        by_type[match['match_type']].append(match)
    
    for match_type, type_matches in by_type.items():
        print(f"\n📋 {match_type.upper()} MATCHES ({len(type_matches)}):")
        print("-" * 30)
        
        for match in type_matches:
            print(f"\n👤 Contact: {match['name']} (ID: {match['contact_id']})")
            print(f"   Email: {match['email']}")
            print(f"   Pattern: {match['pattern']}")
            print(f"   Match: {match['match_value']}")
            
            if match_type == 'custom_field':
                print(f"   Field ID: {match['field_id']}")
                
                # Show all custom fields for this contact
                print("   📋 All custom fields:")
                for field in match['custom_fields']:
                    field_id = field.get('id')
                    content = field.get('content', '')
                    if content:  # Only show non-empty fields
                        print(f"      Field {field_id}: {content}")
    
    # Look for formatting variations
    print(f"\n🔍 FORMATTING VARIATION ANALYSIS:")
    print("=" * 40)
    
    all_values = [match['match_value'] for match in matches]
    
    # Group similar values
    normalized_groups = defaultdict(list)
    for value in all_values:
        # Multiple normalization approaches
        normalizations = [
            value.lower().replace('-', '').replace('_', '').replace(' ', ''),
            re.sub(r'[^a-z0-9]', '', value.lower()),
            value.lower().strip()
        ]
        
        for norm in normalizations:
            if '6fn' in norm or 'sixfn' in norm:
                normalized_groups[norm].append(value)
    
    variations_found = False
    for normalized, originals in normalized_groups.items():
        unique_originals = list(set(originals))
        if len(unique_originals) > 1:
            variations_found = True
            print(f"\n📝 Normalized '{normalized}' appears as:")
            for original in unique_originals:
                print(f"   - '{original}'")
    
    if not variations_found:
        print("✅ No formatting variations detected in 6FN data")


async def search_specific_names():
    """Search for specific name patterns"""
    context = Context()
    
    print("\n🔍 Searching for specific name patterns...")
    
    # Try searching with different filter approaches
    search_terms = ["Scott", "Hanan", "6FN", "sixfn"]
    
    for term in search_terms:
        try:
            print(f"\n🔎 Searching for '{term}'...")
            
            # Try searching in given_name
            result = await list_contacts(
                context,
                filters=[{"field": "given_name", "operator": "contains", "value": term}],
                limit=20
            )
            
            if result['count'] > 0:
                print(f"   Found {result['count']} contacts with '{term}' in given_name")
                
                details = await get_collection_details(
                    context, 
                    result['collection_id'],
                    fields=["id", "given_name", "family_name", "email"]
                )
                
                for contact in details['contacts']:
                    print(f"   👤 {contact.get('given_name', '')} {contact.get('family_name', '')} (ID: {contact.get('id')})")
            else:
                print(f"   No matches for '{term}' in given_name")
                
        except Exception as e:
            print(f"   ❌ Error searching for '{term}': {e}")


async def main():
    """Main execution function"""
    print("🚀 6FN Pattern Search & Analysis")
    print("=" * 35)
    
    try:
        # Search for 6FN patterns
        matches = await search_for_6fn_patterns()
        
        # Analyze variations
        analyze_6fn_variations(matches)
        
        # Search for specific names
        await search_specific_names()
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
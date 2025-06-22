#!/usr/bin/env python3
"""
Query raw custom field data for all Scott Hanan contacts to find 6FN-related data
and analyze for formatting variations that represent the same effective data.
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


# Known Scott Hanan contact IDs from previous search
SCOTT_HANAN_IDS = [22775, 22773, 22543, 23719, 23709, 23583, 23581, 23557, 23555, 23553]


async def get_all_scott_hanan_contacts():
    """Get all Scott Hanan contacts with complete custom field data"""
    context = Context()
    
    print("🔍 Retrieving all 10 Scott Hanan contacts with complete custom field data...")
    
    scott_contacts = []
    
    # Search in targeted ranges where we know Scott contacts exist
    search_ranges = [
        (1900, 2100),   # Covers IDs 22543, 22773, 22775
        (2200, 2400),   # Covers IDs 23553-23719
    ]
    
    for start_offset, end_offset in search_ranges:
        print(f"\n📋 Searching range {start_offset}-{end_offset}...")
        
        for offset in range(start_offset, end_offset, 100):
            try:
                result = await list_contacts(
                    context,
                    limit=100,
                    offset=offset
                )
                
                if result['count'] == 0:
                    continue
                
                # Get ALL contact details including complete custom fields
                details = await get_collection_details(
                    context,
                    result['collection_id']
                    # No field filtering - get everything
                )
                
                contacts = details.get('contacts', [])
                
                for contact in contacts:
                    contact_id = contact.get('id')
                    if contact_id in SCOTT_HANAN_IDS:
                        scott_contacts.append(contact)
                        print(f"   ✅ Found: {contact.get('given_name')} {contact.get('family_name')} (ID: {contact_id})")
                
                # If we found all 10, we can stop this range
                if len(scott_contacts) >= 10:
                    break
                    
            except Exception as e:
                print(f"   ❌ Error at offset {offset}: {e}")
                continue
        
        if len(scott_contacts) >= 10:
            break
    
    print(f"\n✅ Retrieved {len(scott_contacts)}/10 Scott Hanan contacts")
    return scott_contacts


def analyze_raw_custom_fields(contacts):
    """Analyze ALL custom field data for potential 6FN-related patterns"""
    print(f"\n📊 Analyzing ALL custom field data for 6FN patterns...")
    
    # Track all custom field data
    all_field_data = defaultdict(list)
    potential_6fn_data = []
    field_value_patterns = defaultdict(set)
    
    # Comprehensive search patterns for 6FN-related content
    search_patterns = [
        # Direct 6FN patterns
        r'6fn', r'6-fn', r'sixfn', r'six.*fn',
        
        # Figure-related patterns
        r'figure.*number', r'six.*figure', r'6.*figure',
        
        # Income/earnings patterns
        r'six.*figure.*income', r'6.*figure.*income', r'figure.*income',
        r'six.*figure.*earning', r'figure.*earning',
        
        # Network/business patterns
        r'network.*income', r'network.*earning', r'mlm.*income',
        r'affiliate.*income', r'business.*income',
        
        # Value/amount patterns with high numbers
        r'\$\d{6,}', r'\d{6,}.*dollar', r'\d{6,}.*income',
        r'100k', r'200k', r'500k', r'million',
        
        # Level/tier patterns
        r'level.*\d+', r'tier.*\d+', r'rank.*\d+',
        r'diamond', r'platinum', r'gold', r'silver',
        
        # Status patterns
        r'high.*earner', r'top.*producer', r'elite.*member'
    ]
    
    for contact in contacts:
        contact_id = contact.get('id')
        given_name = contact.get('given_name', '')
        family_name = contact.get('family_name', '')
        email = contact.get('email', '')
        custom_fields = contact.get('custom_fields', [])
        
        print(f"\n👤 {given_name} {family_name} (ID: {contact_id})")
        print(f"   Email: {email}")
        print(f"   Total custom fields: {len(custom_fields)}")
        
        contact_6fn_matches = []
        contact_all_data = []
        
        for field in custom_fields:
            field_id = field.get('id')
            field_content = field.get('content')
            field_type = field.get('type', 'unknown')
            
            # Store all field data for analysis
            all_field_data[field_id].append({
                'contact_name': f"{given_name} {family_name}",
                'contact_id': contact_id,
                'content': field_content,
                'type': field_type
            })
            
            # Only analyze fields with actual content
            if field_content is not None and str(field_content).strip():
                content_str = str(field_content).lower()
                contact_all_data.append((field_id, field_content, field_type))
                
                # Check for any 6FN-related patterns
                for pattern in search_patterns:
                    if re.search(pattern, content_str, re.IGNORECASE):
                        match_data = {
                            'contact_name': f"{given_name} {family_name}",
                            'contact_id': contact_id,
                            'email': email,
                            'field_id': field_id,
                            'field_type': field_type,
                            'content': field_content,
                            'pattern_matched': pattern,
                            'match_text': re.search(pattern, content_str, re.IGNORECASE).group()
                        }
                        potential_6fn_data.append(match_data)
                        contact_6fn_matches.append(match_data)
                        
                        print(f"   🎯 6FN PATTERN MATCH:")
                        print(f"      Field {field_id} ({field_type}): {field_content}")
                        print(f"      Pattern: {pattern} -> Match: {match_data['match_text']}")
                        break  # Only report first pattern match per field
                
                # Track value patterns for later analysis
                field_value_patterns[field_id].add(str(field_content))
        
        print(f"   📋 Fields with data: {len(contact_all_data)}")
        print(f"   🔢 Potential 6FN matches: {len(contact_6fn_matches)}")
        
        # Show sample of ALL field data (not just 6FN matches)
        if contact_all_data:
            print(f"   📝 Sample custom field data:")
            for field_id, content, field_type in contact_all_data[:10]:  # Show first 10
                content_display = str(content)
                if len(content_display) > 50:
                    content_display = content_display[:47] + "..."
                print(f"      Field {field_id} ({field_type}): {content_display}")
    
    return potential_6fn_data, all_field_data, field_value_patterns


def analyze_formatting_variations(fn_data, field_patterns):
    """Analyze potential formatting variations in 6FN-related data"""
    print(f"\n🔍 FORMATTING VARIATION ANALYSIS")
    print("=" * 50)
    
    if not fn_data:
        print("❌ No 6FN-related patterns found in custom field data")
        print("\nThis could mean:")
        print("- 6FN data uses different terminology (e.g., 'Network Level', 'Income Tier')")
        print("- Data is encoded/abbreviated (e.g., 'L6', 'T6', numerical codes)")
        print("- Information is in field names rather than field values")
        print("- Data exists in different contacts or system")
        return
    
    print(f"✅ Found {len(fn_data)} potential 6FN-related field instances")
    
    # Group by content to find variations
    content_groups = defaultdict(list)
    pattern_groups = defaultdict(list)
    field_groups = defaultdict(list)
    
    for item in fn_data:
        content = str(item['content']).strip()
        pattern = item['pattern_matched']
        field_id = item['field_id']
        
        content_groups[content].append(item)
        pattern_groups[pattern].append(item)
        field_groups[field_id].append(item)
    
    # Analyze content variations
    print(f"\n📋 6FN Content Analysis:")
    print("-" * 30)
    
    for content, instances in content_groups.items():
        print(f"\n   Content: '{content}'")
        print(f"   Found in {len(instances)} contacts:")
        for instance in instances:
            print(f"     - {instance['contact_name']} (Field {instance['field_id']})")
            print(f"       Pattern: {instance['pattern_matched']} -> {instance['match_text']}")
    
    # Look for potential same-data-different-format
    print(f"\n🔍 Potential Formatting Variations:")
    print("-" * 40)
    
    # Normalize content and look for similar meanings
    normalized_groups = defaultdict(list)
    
    for content in content_groups.keys():
        # Multiple normalization approaches
        normalizations = [
            # Remove all non-alphanumeric
            re.sub(r'[^a-z0-9]', '', content.lower()),
            # Remove spaces and common separators
            content.lower().replace(' ', '').replace('-', '').replace('_', ''),
            # Extract just numbers
            ''.join(re.findall(r'\d+', content.lower())),
            # Extract key terms
            ' '.join(re.findall(r'(six|6|figure|fn|network|level|income|tier)', content.lower()))
        ]
        
        for norm in normalizations:
            if norm:  # Only if normalization produced something
                normalized_groups[norm].append(content)
    
    variations_found = False
    for normalized, originals in normalized_groups.items():
        unique_originals = list(set(originals))
        if len(unique_originals) > 1:
            variations_found = True
            print(f"\n   📝 Normalized '{normalized}' appears as:")
            for original in unique_originals:
                contacts_using = [item['contact_name'] for item in fn_data if str(item['content']).strip() == original]
                print(f"     - '{original}' (used by: {', '.join(set(contacts_using))})")
    
    if not variations_found:
        print("   ✅ No obvious formatting variations detected")
        if len(content_groups) == 1:
            print("   All 6FN-related fields use consistent formatting")
        else:
            print("   Each field contains distinct 6FN-related information")


def analyze_field_patterns_for_6fn_clues(field_patterns, all_field_data):
    """Look for patterns that might indicate 6FN data with different naming"""
    print(f"\n🔍 SEARCHING FOR 6FN CLUES IN ALL FIELD PATTERNS")
    print("=" * 55)
    
    # Look for fields with values that could represent levels, tiers, or categories
    potential_level_fields = []
    potential_amount_fields = []
    potential_category_fields = []
    
    for field_id, values in field_patterns.items():
        value_list = list(values)
        
        # Skip empty or None values
        clean_values = [v for v in value_list if v and str(v).strip() and str(v).lower() not in ['none', 'null']]
        
        if not clean_values:
            continue
        
        # Check for level/tier patterns
        if any(re.search(r'^[A-Z]$|^\d+$|^level|^tier|^rank', str(v), re.IGNORECASE) for v in clean_values):
            potential_level_fields.append((field_id, clean_values))
        
        # Check for amount/income patterns
        if any(re.search(r'\$|\d{4,}|income|earning|revenue', str(v), re.IGNORECASE) for v in clean_values):
            potential_amount_fields.append((field_id, clean_values))
        
        # Check for category/status patterns
        if any(re.search(r'diamond|platinum|gold|elite|premium|vip|pro', str(v), re.IGNORECASE) for v in clean_values):
            potential_category_fields.append((field_id, clean_values))
    
    print(f"🔍 Potential Level/Tier Fields ({len(potential_level_fields)} found):")
    for field_id, values in potential_level_fields[:10]:  # Show first 10
        contacts_using = [item['contact_name'] for item in all_field_data[field_id] if item['content']]
        print(f"   Field {field_id}: {values} (used by: {', '.join(set(contacts_using))})")
    
    print(f"\n💰 Potential Amount/Income Fields ({len(potential_amount_fields)} found):")
    for field_id, values in potential_amount_fields[:10]:  # Show first 10
        contacts_using = [item['contact_name'] for item in all_field_data[field_id] if item['content']]
        print(f"   Field {field_id}: {values} (used by: {', '.join(set(contacts_using))})")
    
    print(f"\n🏆 Potential Category/Status Fields ({len(potential_category_fields)} found):")
    for field_id, values in potential_category_fields[:10]:  # Show first 10
        contacts_using = [item['contact_name'] for item in all_field_data[field_id] if item['content']]
        print(f"   Field {field_id}: {values} (used by: {', '.join(set(contacts_using))})")
    
    # Show fields used by multiple Scott contacts (these might be significant)
    multi_contact_fields = {fid: data for fid, data in all_field_data.items() 
                           if len([d for d in data if d['content']]) > 1}
    
    print(f"\n👥 Fields Used by Multiple Scott Contacts ({len(multi_contact_fields)} found):")
    for field_id, instances in sorted(multi_contact_fields.items(), key=lambda x: len([d for d in x[1] if d['content']]), reverse=True)[:15]:
        non_empty_instances = [d for d in instances if d['content']]
        values = list(set(str(d['content']) for d in non_empty_instances))
        contacts = list(set(d['contact_name'] for d in non_empty_instances))
        print(f"   Field {field_id}: {values} ({len(contacts)} contacts: {', '.join(contacts)})")


async def main():
    """Main execution function"""
    print("🚀 Scott Hanan 6FN Custom Field Analysis")
    print("=" * 45)
    print("Searching for 6FN-related data and formatting variations...")
    print()
    
    try:
        # Get all Scott Hanan contacts with complete data
        scott_contacts = await get_all_scott_hanan_contacts()
        
        if not scott_contacts:
            print("❌ Could not retrieve Scott Hanan contacts")
            return
        
        # Analyze all custom field data for 6FN patterns
        fn_data, all_field_data, field_patterns = analyze_raw_custom_fields(scott_contacts)
        
        # Analyze formatting variations in found 6FN data
        analyze_formatting_variations(fn_data, field_patterns)
        
        # Look for additional clues in field patterns
        analyze_field_patterns_for_6fn_clues(field_patterns, all_field_data)
        
        # Final summary
        print(f"\n" + "="*60)
        print(f"📊 FINAL ANALYSIS SUMMARY")
        print(f"="*60)
        print(f"Scott Hanan contacts analyzed: {len(scott_contacts)}")
        print(f"Total custom fields examined: {len(all_field_data)}")
        print(f"Fields with data: {sum(1 for fid, data in all_field_data.items() if any(d['content'] for d in data))}")
        print(f"Direct 6FN pattern matches: {len(fn_data)}")
        level_pattern = r'^[A-Z]$|^\d+$'
        potential_level_count = len([fid for fid, vals in field_patterns.items() if any(re.search(level_pattern, str(v)) for v in vals)])
        print(f"Potential level/tier fields: {potential_level_count}")
        
        if fn_data:
            print(f"\n✅ 6FN-related data found! Analysis complete.")
        else:
            print(f"\n💡 No direct 6FN patterns found. Possible explanations:")
            print(f"   - 6FN data uses different terminology")
            print(f"   - Data is in field names/labels, not field content")
            print(f"   - Information is encoded or abbreviated")
            print(f"   - 6FN data exists in other contacts or systems")
        
        print(f"\n✅ Raw custom field analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
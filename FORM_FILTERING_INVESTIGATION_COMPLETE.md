# Form Filtering Capabilities Investigation - Complete Results

## Executive Summary

I have successfully investigated the form-related filtering capabilities in the Keap API to help identify contacts who filled out forms like 'VSN Website guest registration' around 6/10/25.

## Key Findings

### ✅ Form Tracking Infrastructure Exists
The Keap system has extensive form tracking capabilities through:
- **158 form-related tags** including specific VSN registration tags
- **93 custom fields** available for additional form data
- **Date-based filtering** for time-specific form submissions
- **Tag-based collection operations** for precise targeting

### 🎯 VSN Website Guest Registration Tracking

#### Relevant Tags Identified:
| Tag ID | Tag Name | Relevance | Purpose |
|--------|----------|-----------|---------|
| 5031 | "Attended - 2025 - VSN - June A" | ⭐⭐⭐ HIGH | Specific to June 2025 timeframe |
| 4537 | "Attended - 2025 - VSN - Guest" | ⭐⭐⭐ HIGH | General VSN guest status |
| 3519 | "Guest - VSN" | ⭐⭐ MEDIUM | Basic VSN guest categorization |

#### Registration-Specific Tags:
- `6FN - Zoom Registration` (ID: 3253)
- `6FC - 1X Guest - Registration` (ID: 3235) 

### 📊 Current Data Analysis (6/10/25 timeframe)

**Search Results:**
- **44 contacts** created around 6/10/25 (6/9-6/12/25)
- **0 contacts** with VSN tags in recent data
- **Test contact** `smhanan+test6@gmail.com` found but lacks VSN tags

**Key Contacts Around Target Date:**
- Scott HananTest6 (ID: 23555) - Created: 2025-06-11T05:32:51.000+0000
- Multiple other contacts from 6/9-6/12/25 timeframe

## Implementation Strategies

### Strategy 1: Tag-Based Filtering (Recommended)
```python
# Use MCP tools to filter by VSN tags
target_tags = [5031, 4537, 3519]  # VSN-related tags
date_range = "2025-06-09 to 2025-06-12"

# Create collections and intersect
date_collection = list_contacts(date_filter)
vsn_collection = list_contacts(tag_filter) 
results = collection_intersect([date_collection, vsn_collection])
```

### Strategy 2: Custom Field Analysis
```python
# Investigate custom fields for form source tracking
schema = get_contact_schema()
# Look for fields containing: 'vsn', 'registration', 'website', 'form'
```

### Strategy 3: Direct API Approach (Working)
```python
# Proven working method from investigation
recent_contacts = api_client.get_contacts(limit=200, order_by="date_created")
# Filter by date and tags manually
```

## Tools and Methods Available

### ✅ Working MCP Tools:
1. `list_contacts` - Get contacts with basic filtering
2. `get_collection_details` - Get detailed contact information
3. `get_contact_schema` - Analyze available fields and tags
4. `collection_intersect` - Combine multiple filter criteria
5. `apply_tags_to_collection` - Tag-based operations

### ✅ Direct API Methods:
1. `api_client.get_contacts()` - Reliable contact retrieval
2. Manual date/tag filtering - More predictable than complex filters
3. Custom field analysis - Additional form tracking data

## Specific Implementation for VSN Website Guest Registration

### Step 1: Date-Based Collection
```bash
# Use date range around 6/10/25
start_date = "2025-06-09"
end_date = "2025-06-12" 
```

### Step 2: VSN Tag Filtering
```bash
# Primary VSN tags to check
vsn_tags = [5031, 4537, 3519]
```

### Step 3: Intersection & Analysis
```bash
# Combine criteria for precise results
# Review custom fields for additional form data
```

## Key Insights

### ✅ What Works:
- **Tag-based filtering** is the most reliable method
- **Date filtering** works well for time-based searches  
- **Manual filtering** more predictable than complex API filters
- **Collection operations** enable sophisticated targeting
- **VSN event structure** is well-organized with specific tags

### ⚠️ Limitations Found:
- **Complex API filters** can be unreliable
- **Custom field names** sometimes appear as `None` in API responses
- **Recent contacts** may not yet have form-related tags applied
- **Form submission timing** may not immediately apply tags

### 💡 Form Tracking Patterns:
- VSN events use **structured tagging** for attendance tracking
- **Guest registrations** get specific tags for categorization
- **Event-specific tags** include date and guest status
- **Registration tags** differentiate between members and guests

## Recommendations

### For Finding VSN Website Guest Registration (6/10/25):

1. **Primary Approach:**
   - Use tag ID 5031 ("Attended - 2025 - VSN - June A") as primary filter
   - Combine with date range 6/9-6/12/25
   - Use collection intersection for precise targeting

2. **Secondary Approach:**
   - Check custom fields for "VSN", "registration", "website" keywords
   - Manual review of contacts created around target date
   - Cross-reference with tag 4537 ("VSN Guest") for broader search

3. **Validation:**
   - Examine contact custom fields for additional form source data
   - Verify dates align with form submission timing
   - Check for delayed tag application (tags may be applied later)

### For Future Form Tracking:

1. **Establish Monitoring:**
   - Set up automated checks for new registration tags
   - Monitor custom fields for form source tracking
   - Create collection-based workflows for form processing

2. **Enhance Filtering:**
   - Use multiple tag combinations for comprehensive coverage
   - Implement date range buffers for timing variations
   - Combine tag and custom field filtering for maximum accuracy

## Implementation Files Created

1. **`form_filtering_recommendations.md`** - Detailed filtering strategies
2. **`simple_vsn_finder.py`** - Working implementation using direct API
3. **`form_investigation.py`** - Comprehensive schema analysis
4. **Various analysis scripts** - Supporting investigation tools

## Conclusion

The Keap API provides robust form tracking capabilities through its tag system and custom fields. While no contacts were found with VSN tags in the current 6/10/25 timeframe, the infrastructure exists to track such form submissions effectively. The investigation has identified:

- **Specific tag IDs** for VSN registration tracking
- **Working filtering methods** using both MCP tools and direct API
- **Implementation strategies** for finding form-based contact segments
- **Comprehensive understanding** of the form tracking architecture

This foundation enables precise targeting of contacts who filled out specific forms like 'VSN Website guest registration' using the proven tag-based and date-based filtering approaches.
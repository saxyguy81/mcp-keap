# Form Filtering Capabilities Investigation Results

## Summary
Investigation of the Keap API revealed extensive form tracking capabilities, particularly for VSN (Virtual Sisterhood Network) events and guest registrations.

## Key Findings

### 1. Contact Schema
- **Total Custom Fields:** 93 available
- **Standard Fields:** 16 core fields including date_created, email_addresses, tag_ids
- **Field Names Issue:** Custom field names showing as `None` - may need schema investigation from MCP tools

### 2. Form-Related Tags Discovered (158 form-related tags found)

#### VSN Event Tags (Primary target for investigation):
- `Attended - 2025 - VSN - Guest` (ID: 4537)
- `Attended - 2025 - VSN - June A` (ID: 5031) ⭐ **HIGHLY RELEVANT for 6/10/25**
- `Guest - VSN` (ID: 3519)
- `Conversion Source - VSN - Event` (ID: 4553)
- `Attended - VSN - Guest - Recent` (ID: 4591)

#### Registration-Specific Tags:
- `6FN - Zoom Registration` (ID: 3253)
- `6FC - 1X Guest - Registration` (ID: 3235)

#### Lead Source Tags:
- `Hot Lead - 2023` (ID: 3000)
- `Guest - Attended Event` (ID: 3511)

### 3. Target Contact Analysis
**Contact:** smhanan+test6@gmail.com
- **ID:** 23555
- **Created:** 2025-06-11T05:32:51.000+0000 (Day after 6/10/25!)
- **Current Tags:** [572, 784, 3206, 3220]
- **Custom Fields:** 93 fields with various date/time and business data

## Recommended Filtering Strategies

### Strategy 1: Date + VSN Tags (Most Precise)
```
1. Filter contacts created between 2025-06-09 and 2025-06-12
2. Apply tag filter for VSN-related tags:
   - Tag ID 5031: "Attended - 2025 - VSN - June A"
   - Tag ID 4537: "Attended - 2025 - VSN - Guest"
   - Tag ID 3519: "Guest - VSN"
```

### Strategy 2: Tag-Based Collection Operations
```
1. Create collection with tag "Attended - 2025 - VSN - June A" (ID: 5031)
2. Intersect with contacts created around 6/10/25
3. Apply additional guest-specific filters
```

### Strategy 3: Lead Source + Date Combination
```
1. Filter by lead_source_id patterns
2. Combine with date_created filter for 6/10/25 timeframe
3. Cross-reference with VSN-related tags
```

### Strategy 4: Email Pattern + Tag Filtering
```
1. Search for email patterns that match form submissions
2. Apply VSN guest tags as secondary filters
3. Validate results with date ranges
```

## Implementation Using MCP Tools

### Step 1: Create Date-Based Collection
```
list_contacts(
  filters='{"date_created": {"start": "2025-06-09", "end": "2025-06-12"}}',
  limit=100
)
```

### Step 2: Apply Tag Filters
```
apply_tags_to_collection(
  collection_id="<from_step1>",
  tag_ids=[5031, 4537, 3519],
  action="filter"
)
```

### Step 3: Intersect Collections
```
collection_intersect([
  "date_based_collection",
  "vsn_tagged_collection"
])
```

## Next Steps

1. **Test the filtering approach** with VSN June A tag (ID: 5031)
2. **Investigate custom field names** using get_contact_schema MCP tool
3. **Examine specific contact tags** to understand the [572, 784, 3206, 3220] tag meanings
4. **Create collections** using the MCP tools with the identified filters
5. **Validate results** by checking contact details for VSN website registration indicators

## Key Tags for VSN Website Guest Registration

| Tag ID | Tag Name | Relevance |
|--------|----------|-----------|
| 5031 | Attended - 2025 - VSN - June A | ⭐⭐⭐ High (June timing) |
| 4537 | Attended - 2025 - VSN - Guest | ⭐⭐⭐ High (Guest status) |
| 3519 | Guest - VSN | ⭐⭐ Medium (General VSN guest) |
| 4591 | Attended - VSN - Guest - Recent | ⭐⭐ Medium (Recent guest) |
| 4553 | Conversion Source - VSN - Event | ⭐ Low (Source tracking) |

## Implementation Priority

1. **Start with Tag ID 5031** ("Attended - 2025 - VSN - June A") - most specific to timeframe
2. **Combine with date filtering** for 6/10/25 ± 2 days
3. **Use collection operations** to refine results
4. **Validate manually** by examining contact details
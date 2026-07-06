# Keap Form-Based Contact Filtering Strategy

Based on investigation of the Keap API and documentation, here's a comprehensive approach to filter contacts who filled out specific forms.

## 🎯 **Core Challenge**

The Keap API doesn't directly expose form submission data or dates. However, there are several effective workarounds to track form submissions:

## 🛠️ **Available Methods**

### 1. **Tag-Based Form Tracking** (Recommended)

Keap can automatically apply tags when forms are submitted. This is the most reliable method:

```javascript
// Find contacts with specific form tags
get_tags({"filters": [{"field": "name", "operator": "contains", "value": "VSN"}]})

// Common VSN-related tags found:
// - VSN June A (ID: 5031)
// - VSN Guest (ID: 4537) 
// - General VSN Guest (ID: 3519)

// Filter contacts by tag
list_contacts({"filters": [{"field": "tag_id", "operator": "equals", "value": "5031"}]})
```

### 2. **Date-Based Filtering**

Filter contacts created around the form submission timeframe:

```javascript
// Contacts created around 6/10/25
list_contacts({
  "filters": [
    {"field": "date_created", "operator": "after", "value": "2025-06-09T00:00:00Z"},
    {"field": "date_created", "operator": "before", "value": "2025-06-12T23:59:59Z"}
  ]
})
```

### 3. **Custom Field Tracking**

Check for custom fields that might store form information:

```javascript
// Get contact schema to see available custom fields
get_contact_schema()

// Look for fields like:
// - "Form Source"
// - "Registration Date"  
// - "Last Form Submitted"
// - "Webinar Registration"
```

### 4. **Combined Approach** (Most Effective)

Combine multiple filters for precise targeting:

```javascript
// Step 1: Get contacts from date range
date_collection = list_contacts({
  "filters": [{"field": "date_created", "operator": "after", "value": "2025-06-09T00:00:00Z"}]
})

// Step 2: Get contacts with VSN tags
vsn_collection = list_contacts({
  "filters": [{"field": "tag_id", "operator": "in", "value": [5031, 4537, 3519]}]
})

// Step 3: Find intersection
form_contacts = collection_intersect([date_collection.collection_id, vsn_collection.collection_id])
```

## 🔍 **Specific Case: VSN Website Guest Registration**

For finding contacts who filled out 'VSN Website guest registration' on 6/10/25:

### Implementation Steps:

```python
async def find_vsn_form_submissions():
    """Find contacts who submitted VSN website guest registration forms."""
    
    # 1. Search for VSN-related tags
    vsn_tags = await get_tags(
        filters=[{"field": "name", "operator": "contains", "value": "VSN"}]
    )
    
    # 2. Get contacts created around 6/10/25
    date_contacts = await list_contacts(
        filters=[
            {"field": "date_created", "operator": "after", "value": "2025-06-09T00:00:00Z"},
            {"field": "date_created", "operator": "before", "value": "2025-06-12T23:59:59Z"}
        ]
    )
    
    # 3. Find contacts with VSN tags in that timeframe
    if vsn_tags["count"] > 0:
        vsn_tag_ids = [tag["id"] for tag in vsn_tags["tags"]]
        
        vsn_contacts = await list_contacts(
            filters=[{"field": "tag_id", "operator": "in", "value": vsn_tag_ids}]
        )
        
        # 4. Get intersection of date and tag filters
        form_submissions = await collection_intersect([
            date_contacts["collection_id"],
            vsn_contacts["collection_id"]
        ])
        
        return form_submissions
    
    return date_contacts
```

## 📋 **Setup Requirements**

### 1. **Configure Form Tags**
In Keap admin, ensure forms automatically apply tags:
- Go to Marketing → Landing Pages → Web Forms
- Edit the 'VSN Website guest registration' form
- Set up automation to apply specific tags on submission
- Use descriptive tag names like "VSN Website Registration 2025"

### 2. **Custom Field Setup** (Optional)
Create custom fields to track form data:
- "Form Source" (text field)
- "Registration Date" (date field)
- "Form Name" (text field)

### 3. **Automation Setup**
Create automations that:
- Apply tags when specific forms are submitted
- Populate custom fields with form submission details
- Set specific values based on form type

## 🎯 **Finding smhanan+test6@gmail.com**

```javascript
// Direct email search
target_contact = list_contacts({
  "filters": [{"field": "email", "operator": "equals", "value": "smhanan+test6@gmail.com"}]
})

// Check contact details for tags and custom fields
contact_details = get_collection_details(target_contact.collection_id, {
  "fields": ["id", "email", "date_created", "tag_ids", "custom_fields"]
})

// Look for VSN-related tags in tag_ids array
// Check custom fields for form submission data
```

## 🔧 **Advanced Filtering Options**

### Multiple Form Types:
```javascript
// Filter by multiple form-related tags
form_tags = [5031, 4537, 3519, 4201, 3987]  // Various form tags
list_contacts({"filters": [{"field": "tag_id", "operator": "in", "value": form_tags}]})
```

### Time Range Refinement:
```javascript
// Narrow down to specific hours on 6/10/25
list_contacts({
  "filters": [
    {"field": "date_created", "operator": "after", "value": "2025-06-10T00:00:00Z"},
    {"field": "date_created", "operator": "before", "value": "2025-06-10T23:59:59Z"}
  ]
})
```

### Email Pattern Matching:
```javascript
// Find test accounts
list_contacts({"filters": [{"field": "email", "operator": "contains", "value": "smhanan+test"}]})
```

## 📊 **Expected Results**

Using these methods, you should be able to:
1. ✅ Find contacts who submitted specific forms
2. ✅ Filter by submission date ranges  
3. ✅ Identify form types through tag analysis
4. ✅ Track automation sequences triggered by forms
5. ✅ Locate specific test submissions like smhanan+test6@gmail.com

## 🚀 **Next Steps**

1. **Verify Tag Setup**: Check if VSN forms apply consistent tags
2. **Test Filtering**: Use the provided methods to search for known submissions
3. **Refine Automation**: Improve form-to-tag automation for better tracking
4. **Custom Fields**: Consider adding form tracking fields for enhanced data capture

The key is leveraging Keap's tag system and date filtering to reconstruct form submission activity, even though direct form submission APIs aren't available.
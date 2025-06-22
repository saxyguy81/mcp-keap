# Keap MCP API Reference

## Overview

The Keap MCP service provides a streamlined interface for interacting with Keap CRM data through the Model Context Protocol (MCP). This document provides comprehensive API reference for the **collection-based architecture** with **field name-first interface**.

## Key Features

- **Collection-Based Operations**: Work with logical groups of contacts using collection IDs
- **Field Name-First Interface**: Use human-readable field names instead of field IDs
- **Set Operations**: Union, intersection, and difference operations on contact collections
- **Lazy Evaluation**: Operations on collections don't fetch data until explicitly requested
- **Schema Discovery**: Runtime discovery of available fields and usage patterns

## MCP Tools Overview

The server exposes **11 streamlined MCP tools**:

### Core Contact Operations (2 tools)
1. **`list_contacts`** - Universal search with field name-based filters
2. **`get_contact_schema`** - Get available fields and usage patterns

### Collection Operations (4 tools)  
3. **`collection_union`** - Combine two collections (A ∪ B)
4. **`collection_intersect`** - Find contacts in both collections (A ∩ B)
5. **`collection_diff`** - Find contacts in first but not second collection (A - B)
6. **`collection_count`** - Get collection size without fetching data

### Collection Data Access (2 tools)
7. **`get_collection_details`** - Fetch contact data from collection
8. **`get_collection_ids`** - Get raw contact ID list from collection

### Tag Operations (2 tools)
9. **`get_tags`** - List available tags with optional filtering
10. **`apply_tags_to_collection`** - Bulk tag operations on collections

### System Operations (1 tool)
11. **`get_api_diagnostics`** - Comprehensive API diagnostics

---

## Tool Reference

### 1. list_contacts

Universal contact search that returns a collection ID for further operations.

#### Parameters

```json
{
  "filters": [
    {
      "field": "string",           // Field name (preferred) 
      "field_id": "string",        // Explicit field ID (alternative)
      "operator": "string", 
      "value": "any"
    }
  ],
  "limit": 200,
  "offset": 0,
  "order_by": "string",
  "order_direction": "ASC|DESC",
  "enable_optimization": true,
  "return_metrics": false
}
```

#### Field Specification Formats

- **Standard fields**: `"field": "email"`, `"field": "given_name"`
- **Custom fields (preferred)**: `"field": "6FN Next Date/Time"`
- **Custom fields (explicit ID)**: `"field_id": "239"`
- **Legacy format**: `"field": "custom_fields.239"` (discouraged)

#### Supported Operators

`equals`, `not_equals`, `contains`, `not_contains`, `starts_with`, `ends_with`, `greater_than`, `less_than`, `between`, `in`, `not_in`, `is_null`, `is_not_null`

#### Example Usage

```python
# Search by field name (preferred)
result = await list_contacts(
    context=context,
    filters=[
        {"field": "6FN Next Date/Time", "operator": "is_not_null", "value": ""}
    ],
    limit=50
)
# Returns: {"collection_id": "contacts_abc123", "count": 12}

# Search by explicit field ID
result = await list_contacts(
    context=context,
    filters=[
        {"field_id": "239", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000"}
    ]
)

# Complex multi-criteria search
result = await list_contacts(
    context=context,
    filters=[
        {"field": "email", "operator": "contains", "value": "@company.com"},
        {"field": "tags", "operator": "contains", "value": "VIP"},
        {"field": "Member Expire Date", "operator": "after", "value": "2024-01-01"}
    ]
)
```

### 2. get_contact_schema

Get available fields, custom fields, and usage patterns.

#### Parameters

```json
{}
```

#### Returns

```json
{
  "standard_fields": ["id", "given_name", "family_name", "email", ...],
  "custom_fields": [
    {
      "name": "6FN Next Date/Time",
      "id": 239,
      "type": "DateTime",
      "usage": {
        "preferred": "\"field\": \"6FN Next Date/Time\"",
        "explicit_id": "\"field_id\": \"239\"",
        "legacy": "\"field\": \"custom_fields.239\""
      }
    }
  ],
  "supported_operators": ["equals", "contains", ...],
  "filter_examples": [...]
}
```

#### Example Usage

```python
# Get schema to see available fields
schema = await get_contact_schema(context=context)

# Find custom fields
for field in schema['custom_fields']:
    if '6fn' in field['name'].lower():
        print(f"Field: {field['name']} -> {field['usage']['preferred']}")
```

### 3. collection_union

Combine two collections (A ∪ B).

#### Parameters

```json
{
  "collection_a": "string",
  "collection_b": "string"
}
```

#### Example Usage

```python
# Find all VIP OR company contacts
vip_result = await list_contacts(context, filters=[{"field": "tags", "operator": "contains", "value": "VIP"}])
company_result = await list_contacts(context, filters=[{"field": "email", "operator": "contains", "value": "@company.com"}])

union_result = await collection_union(
    context=context,
    collection_a=vip_result['collection_id'],
    collection_b=company_result['collection_id']
)
# Returns: {"collection_id": "contacts_union_xyz", "count": 150}
```

### 4. collection_intersect

Find contacts in both collections (A ∩ B).

#### Parameters

```json
{
  "collection_a": "string",
  "collection_b": "string"
}
```

#### Example Usage

```python
# Find VIP company contacts (both VIP AND company)
intersection_result = await collection_intersect(
    context=context,
    collection_a=vip_result['collection_id'],
    collection_b=company_result['collection_id']
)
# Returns: {"collection_id": "contacts_intersect_xyz", "count": 12}
```

### 5. collection_diff

Find contacts in first but not second collection (A - B).

#### Parameters

```json
{
  "collection_a": "string",
  "collection_b": "string"
}
```

#### Example Usage

```python
# Find company contacts who are NOT VIP
diff_result = await collection_diff(
    context=context,
    collection_a=company_result['collection_id'],
    collection_b=vip_result['collection_id']
)
# Returns: {"collection_id": "contacts_diff_xyz", "count": 138}
```

### 6. collection_count

Get collection size without fetching contact data.

#### Parameters

```json
{
  "collection_id": "string"
}
```

#### Example Usage

```python
# Get count efficiently
count_result = await collection_count(
    context=context,
    collection_id="contacts_abc123"
)
# Returns: {"collection_id": "contacts_abc123", "count": 150}
```

### 7. get_collection_details

Fetch contact data with field selection from collection.

#### Parameters

```json
{
  "collection_id": "string",
  "fields": ["field1", "field2", ...],  // Optional field selection
  "limit": 200,
  "offset": 0
}
```

#### Example Usage

```python
# Get detailed contact data
details = await get_collection_details(
    context=context,
    collection_id="contacts_abc123",
    fields=["id", "given_name", "family_name", "email", "6FN Next Date/Time"],
    limit=50
)
# Returns: {"count": 50, "contacts": [...], "collection_id": "contacts_abc123"}
```

### 8. get_collection_ids

Get raw contact ID list from collection.

#### Parameters

```json
{
  "collection_id": "string"
}
```

#### Example Usage

```python
# Get just the contact IDs
ids_result = await get_collection_ids(
    context=context,
    collection_id="contacts_abc123"
)
# Returns: {"collection_id": "contacts_abc123", "contact_ids": [123, 456, 789]}
```

### 9. get_tags

List available tags with optional filtering.

#### Parameters

```json
{
  "filters": [
    {
      "field": "string",
      "operator": "string",
      "value": "any"
    }
  ],
  "include_categories": true,
  "limit": 1000
}
```

#### Example Usage

```python
# Get all tags
tags = await get_tags(context=context, include_categories=True)

# Get filtered tags
customer_tags = await get_tags(
    context=context,
    filters=[{"field": "name", "operator": "contains", "value": "customer"}]
)
```

### 10. apply_tags_to_collection

Bulk tag operations on contact collections.

#### Parameters

```json
{
  "collection_id": "string",
  "tag_ids": [123, 456],
  "operation": "add|remove|replace",
  "return_metrics": false
}
```

#### Example Usage

```python
# Add tags to all contacts in collection
tag_result = await apply_tags_to_collection(
    context=context,
    collection_id="contacts_abc123",
    tag_ids=[456, 789],
    operation="add"
)
```

### 11. get_api_diagnostics

Get comprehensive API diagnostics and performance metrics.

#### Parameters

```json
{}
```

#### Example Usage

```python
# Get system diagnostics
diagnostics = await get_api_diagnostics(context=context)
# Returns: API performance metrics, cache stats, system info, recommendations
```

---

## Complete Workflow Examples

### Example 1: Find and Tag VIP Company Contacts

```python
# 1. Search for company contacts
company_contacts = await list_contacts(
    context=context,
    filters=[{"field": "email", "operator": "contains", "value": "@company.com"}]
)

# 2. Search for VIP contacts  
vip_contacts = await list_contacts(
    context=context,
    filters=[{"field": "tags", "operator": "contains", "value": "VIP"}]
)

# 3. Find intersection (VIP company contacts)
vip_company = await collection_intersect(
    context=context,
    collection_a=company_contacts['collection_id'],
    collection_b=vip_contacts['collection_id']
)

# 4. Add "Premium" tag to all VIP company contacts
await apply_tags_to_collection(
    context=context,
    collection_id=vip_company['collection_id'],
    tag_ids=[999],  # "Premium" tag ID
    operation="add"
)

# 5. Get detailed contact information
details = await get_collection_details(
    context=context,
    collection_id=vip_company['collection_id'],
    fields=["id", "given_name", "family_name", "email", "tags"]
)

print(f"Tagged {details['count']} VIP company contacts")
```

### Example 2: Custom Field Analysis

```python
# 1. Get schema to see available custom fields
schema = await get_contact_schema(context=context)

# 2. Find contacts with specific custom field data
contacts_with_6fn = await list_contacts(
    context=context,
    filters=[{"field": "6FN Next Date/Time", "operator": "is_not_null", "value": ""}]
)

# 3. Get detailed data including custom fields
details = await get_collection_details(
    context=context,
    collection_id=contacts_with_6fn['collection_id'],
    fields=["id", "given_name", "family_name", "6FN Next Date/Time", "6FN Next Event Category A-B"]
)

# 4. Analyze the data
for contact in details['contacts']:
    name = f"{contact['given_name']} {contact['family_name']}"
    # Custom fields are automatically resolved to names in the response
    datetime_value = contact.get('6FN Next Date/Time')
    category = contact.get('6FN Next Event Category A-B')
    print(f"{name}: {datetime_value} ({category})")
```

---

## Data Models

### Contact Model

```python
{
  "id": 123456,
  "given_name": "John",
  "family_name": "Doe", 
  "email": "john.doe@company.com",
  "phone": "555-1234",
  "tags": [
    {"id": 1, "name": "Premium Customer"},
    {"id": 2, "name": "Active"}
  ],
  "custom_fields": [
    {
      "id": 239,
      "content": "2025-06-20T18:30:00.000+0000",
      "field_name": "6FN Next Date/Time"  // Automatically resolved
    }
  ],
  // Custom fields also available directly by name:
  "6FN Next Date/Time": "2025-06-20T18:30:00.000+0000",
  "Member Expire Date": "2025-07-14"
}
```

### Collection Response Model

```python
{
  "collection_id": "contacts_abc123",
  "count": 150,
  "contacts": [...],  // Only in get_collection_details
  "contact_ids": [...],  // Only in get_collection_ids
  "performance_metrics": {...}  // Optional
}
```

---

## Performance Best Practices

### 1. Use Collections Efficiently

```python
# ✅ Good: Chain operations on collections
search_result = await list_contacts(context, filters=filters)
filtered_result = await collection_intersect(context, search_result['collection_id'], other_collection)
details = await get_collection_details(context, filtered_result['collection_id'])

# ❌ Avoid: Multiple separate searches
for email in emails:
    contacts = await list_contacts(context, filters=[{"field": "email", "operator": "equals", "value": email}])
```

### 2. Use Field Names for Readability

```python
# ✅ Good: Use field names
{"field": "6FN Next Date/Time", "operator": "equals", "value": "..."}

# ✅ Acceptable: Use explicit field_id when needed
{"field_id": "239", "operator": "equals", "value": "..."}

# ⚠️ Discouraged: Legacy format
{"field": "custom_fields.239", "operator": "equals", "value": "..."}
```

### 3. Leverage Schema Discovery

```python
# ✅ Good: Get schema once and reuse
schema = await get_contact_schema(context)
available_fields = {field['name']: field['id'] for field in schema['custom_fields']}

# Use the schema to build dynamic filters
if "6FN Next Date/Time" in available_fields:
    filters.append({"field": "6FN Next Date/Time", "operator": "is_not_null", "value": ""})
```

### 4. Optimize Data Fetching

```python
# ✅ Good: Specify only needed fields
details = await get_collection_details(
    context=context,
    collection_id=collection_id,
    fields=["id", "given_name", "family_name", "email"]  # Only what you need
)

# ✅ Good: Use pagination for large datasets
for offset in range(0, total_count, 200):
    batch = await get_collection_details(
        context=context,
        collection_id=collection_id,
        limit=200,
        offset=offset
    )
```

---

## Error Handling

### Common Error Patterns

```python
try:
    result = await list_contacts(context, filters=filters)
except ValueError as e:
    # Field name not found, API parameter error
    print(f"Invalid parameters: {e}")
except Exception as e:
    # API errors, network issues
    print(f"Operation failed: {e}")
```

### Field Name Resolution Errors

```python
# If a field name is not found, you'll see a warning in logs:
# "Unknown field name 'Invalid Field'. Check spelling or use 'field_id' for custom fields."

# Use get_contact_schema to verify available field names:
schema = await get_contact_schema(context)
available_custom_fields = [field['name'] for field in schema['custom_fields']]
print("Available custom fields:", available_custom_fields)
```

---

This API reference provides comprehensive documentation for the collection-based, field name-first Keap MCP service.
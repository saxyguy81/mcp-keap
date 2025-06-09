# Keap MCP API Schema Documentation

This document provides information about the standardized schema for the Keap MCP API.

## Overview

The Keap MCP API uses a JSON Schema-based approach for all requests and responses, providing:

- Consistent request and response formats
- Detailed validation
- Enhanced error reporting
- Self-documenting endpoints
- LLM-friendly structure

## API Endpoints

### MCP Protocol Endpoint

```
POST /mcp
```

This is the main endpoint for making requests to the MCP API. All MCP functions are invoked by sending a POST request to this endpoint with a JSON body in the following format:

```json
{
  "function": "function_name",
  "params": {
    // Function-specific parameters
  },
  "request_id": "optional-tracking-id"
}
```

### Introspection Endpoints

#### Schema Information

```
GET /api/schema
```

Returns complete schema information for all API endpoints.

#### Function-Specific Schema

```
GET /api/schema/{function_name}
```

Returns schema information for a specific function.

#### API Capabilities

```
GET /api/capabilities
```

Returns human-readable information about API capabilities.

## Common Structures

### Request Format

All requests follow the same basic structure:

```json
{
  "function": "function_name",
  "params": {
    // Function-specific parameters
  },
  "request_id": "optional-tracking-id"
}
```

### Response Format

All responses follow the same basic structure:

```json
{
  "result": {
    // Function-specific result data (null if error)
  },
  "error": {
    // Error information (null if success)
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "field.path",
        "code": "FIELD_ERROR_CODE",
        "message": "Field-specific error message",
        "suggestion": "Suggestion for how to fix the error"
      }
    ],
    "documentation_url": "URL to documentation about this error"
  },
  "request_id": "same-as-request-if-provided"
}
```

### Filter Structure

The API uses a standardized filter structure across all endpoints:

```json
{
  "field": "field_name",
  "operator": "operator_name",
  "value": "filter_value"
}
```

Common operators:
- For strings: `=`, `!=`, `pattern`, `starts_with`, `ends_with`, `contains`
- For numbers: `=`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `between`
- For dates: `=`, `!=`, `<`, `<=`, `>`, `>=`, `between`, `before`, `after`, `on`
- For booleans: `=`, `!=`

### Logical Groups

For complex conditions, logical groups can be used:

```json
{
  "operator": "AND|OR|NOT",
  "conditions": [
    // List of filter conditions or nested logical groups
  ]
}
```

## Error Handling

The API provides detailed error information:

- All errors include a `code` and `message`
- Field-specific errors include details about the specific field and issue
- When possible, suggestions for fixing errors are provided
- Documentation URLs point to relevant documentation

Example error response:

```json
{
  "result": null,
  "error": {
    "code": "SCHEMA_VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "params.filters[0].operator",
        "code": "INVALID_ENUM_VALUE",
        "message": "Value must be one of: =, !=, pattern, starts_with",
        "suggestion": "Use a valid operator for string fields"
      }
    ],
    "documentation_url": "/api/schema"
  },
  "request_id": "req-123"
}
```

## LLM Integration

The API is designed to be LLM-friendly:

- Consistent, well-documented structures
- Self-describing schema with examples
- Detailed error messages with suggestions
- Named constants for operators and field values
- Introspection capabilities for dynamic discovery

## Using the Schema API

You can use the schema endpoints to dynamically discover API capabilities:

1. `GET /api/capabilities` - Get a high-level overview of available functions
2. `GET /api/schema/{function_name}` - Get detailed schema for a specific function
3. `GET /api/schema` - Get complete schema information for all functions

This allows for dynamic integration and adaptation to API changes.

## Examples

### Query Contacts

```json
{
  "function": "query_contacts",
  "params": {
    "filters": [
      {"field": "first_name", "operator": "pattern", "value": "John*"},
      {"field": "email", "operator": "pattern", "value": "*@example.com"},
      {
        "operator": "OR",
        "conditions": [
          {"field": "tag", "operator": "=", "value": 123},
          {"field": "tag", "operator": "=", "value": 456}
        ]
      }
    ],
    "sort": [
      {"field": "last_name", "direction": "asc"}
    ],
    "max_results": 1000,
    "include_fields": ["email", "first_name", "tag"]
  },
  "request_id": "query-123"
}
```

The `include_fields` parameter is optional and allows you to specify which fields should be requested from the API. This optimization reduces data transfer and improves performance, especially for large contact databases.

### Get Contact Details

```json
{
  "function": "get_contact_details",
  "params": {
    "contact_ids": [1001, 1002, 1003],
    "include": {
      "basic_info": true,
      "dates": true,
      "tags": {
        "enabled": true,
        "include_dates": true
      }
    }
  },
  "request_id": "details-123"
}
```

### Query Tags

```json
{
  "function": "query_tags",
  "params": {
    "filters": [
      {"field": "name", "operator": "pattern", "value": "Customer*"},
      {"field": "category_id", "operator": "=", "value": 42}
    ],
    "use_cache": true
  },
  "request_id": "tags-123"
}
```

### Intersect ID Lists

```json
{
  "function": "intersect_id_lists",
  "params": {
    "lists": [
      { 
        "list_id": "active_users", 
        "item_ids": [1001, 1002, 1003, 1004] 
      },
      { 
        "list_id": "newsletter_subscribers", 
        "item_ids": [1002, 1003, 1005, 1006] 
      }
    ],
    "id_field": "item_ids"  // Optional, defaults to "item_ids"
  },
  "request_id": "intersection-123"
}
```

This generic intersection function works with any type of ID lists, not just contacts. You can use it with:
- Contact IDs
- Tag IDs  
- Category IDs
- Custom field IDs
- Any other type of ID list

Simply provide the appropriate field name in the `id_field` parameter to match your data structure.

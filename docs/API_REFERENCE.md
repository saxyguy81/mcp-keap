# Keap MCP API Reference

## Overview

The Keap MCP service provides a streamlined interface for interacting with Keap CRM data through the Model Context Protocol (MCP). This document provides comprehensive API reference and usage examples.

## MCP Tools

### 1. list_contacts

List contacts from Keap CRM with optional filtering and pagination. 

*Note: This function now uses the optimization engine internally for better performance. For detailed performance metrics, use `query_contacts_optimized` directly.*

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
  "limit": 200,
  "offset": 0,
  "order_by": "string",
  "order_direction": "ASC|DESC",
  "include": ["field1", "field2"]
}
```

#### Example Usage

```python
# Basic contact listing
result = await list_contacts(
    context=context,
    limit=50,
    offset=0
)

# Filtered contact listing
result = await list_contacts(
    context=context,
    filters=[
        {"field": "email", "operator": "contains", "value": "@company.com"}
    ],
    include=["id", "given_name", "family_name", "email"],
    limit=100
)
```

### 2. get_tags

Retrieve tags from Keap CRM with optional filtering.

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
# Get all tags with categories
tags = await get_tags(
    context=context,
    include_categories=True
)

# Get filtered tags
tags = await get_tags(
    context=context,
    filters=[
        {"field": "name", "operator": "contains", "value": "customer"}
    ],
    limit=50
)
```

### 3. search_contacts_by_email

Search for contacts by email address.

#### Parameters

```json
{
  "email": "string",
  "include": ["field1", "field2"]
}
```

#### Example Usage

```python
# Search by exact email
contacts = await search_contacts_by_email(
    context=context,
    email="john.doe@company.com",
    include=["id", "given_name", "family_name", "email", "tags"]
)
```

### 4. search_contacts_by_name

Search for contacts by name (first or last).

#### Parameters

```json
{
  "name": "string",
  "include": ["field1", "field2"]
}
```

#### Example Usage

```python
# Search by name
contacts = await search_contacts_by_name(
    context=context,
    name="John Doe",
    include=["id", "given_name", "family_name", "email"]
)
```

### 5. get_contacts_with_tag

Get contacts that have a specific tag.

#### Parameters

```json
{
  "tag_id": "string",
  "limit": 200,
  "include": ["field1", "field2"]
}
```

#### Example Usage

```python
# Get contacts with specific tag
contacts = await get_contacts_with_tag(
    context=context,
    tag_id="123",
    limit=100,
    include=["id", "given_name", "family_name", "email"]
)
```

## Data Models

### Contact Model

```python
{
  "id": 123456,
  "given_name": "John",
  "family_name": "Doe", 
  "email": "john.doe@company.com",
  "phone1": "555-1234",
  "tags": [
    {"id": 1, "name": "Premium Customer"},
    {"id": 2, "name": "Active"}
  ],
  "custom_fields": [
    {"content": "Engineering", "id": 1}
  ]
}
```

### Tag Model

```python
{
  "id": 123,
  "name": "Premium Customer",
  "description": "High-value customers",
  "category": {
    "id": 1, 
    "name": "Customer Status"
  }
}
```

### Filter Conditions

```python
# Text fields
{"field": "email", "operator": "contains", "value": "@company.com"}
{"field": "given_name", "operator": "equals", "value": "John"}

# Numeric fields  
{"field": "id", "operator": "greater_than", "value": 1000}
{"field": "id", "operator": "in", "value": [123, 456, 789]}

# Date fields
{"field": "date_created", "operator": "greater_than", "value": "2023-01-01"}
```

## API Client Integration

### Basic Setup

```python
from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from mcp.server.fastmcp import Context

# Initialize components
api_client = KeapApiService()
cache_manager = CacheManager()

# Set up context
context = Context()
context.api_client = api_client
context.cache_manager = cache_manager
```

### Direct API Usage

```python
from src.mcp.tools import list_contacts, get_tags

# Use MCP tools directly
contacts = await list_contacts(
    context=context,
    filters=[{"field": "email", "operator": "contains", "value": "@company.com"}],
    limit=50
)

tags = await get_tags(
    context=context,
    include_categories=True
)
```

## Caching

The system includes automatic caching to improve performance:

### Cache Behavior
- **Contact Data**: Cached for 1 hour
- **Tag Data**: Cached for 1 hour  
- **Search Results**: Cached for 30 minutes

### Cache Management

```python
from src.cache.persistent_manager import PersistentCacheManager

# Initialize cache manager
cache = PersistentCacheManager()

# Manual cache operations
await cache.set("key", data, ttl=3600)
cached_data = await cache.get("key")
await cache.delete("key")
await cache.cleanup_expired()
```

## Error Handling

### Common Error Patterns

```python
try:
    contacts = await list_contacts(context, filters=filters)
except KeapApiError as e:
    if e.status_code == 401:
        # Handle authentication error
        logger.error("Invalid API credentials")
    elif e.status_code == 429:
        # Handle rate limiting
        await asyncio.sleep(60)
        # Retry request
    else:
        logger.error(f"API error: {e}")
        
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### Graceful Degradation

The system automatically handles various error conditions:

- **API Failures**: Falls back to cached data when available
- **Network Issues**: Implements retry logic with exponential backoff
- **Rate Limiting**: Respects API rate limits and retry-after headers

## Configuration

### Environment Variables

```bash
# Required
KEAP_API_KEY=your_api_key_here

# Optional  
KEAP_API_BASE_URL=https://api.infusionsoft.com/crm/rest/v1
KEAP_MCP_HOST=127.0.0.1
KEAP_MCP_PORT=5000
KEAP_MCP_LOG_LEVEL=INFO
KEAP_MCP_CACHE_ENABLED=true
KEAP_MCP_CACHE_TTL=3600
```

### Programmatic Configuration

Configuration is handled through environment variables. Access them directly in your application:

```python
import os

# Access configuration
api_key = os.getenv("KEAP_API_KEY")
cache_enabled = os.getenv("KEAP_MCP_CACHE_ENABLED", "true").lower() == "true"
cache_ttl = int(os.getenv("KEAP_MCP_CACHE_TTL", "3600"))
```

## Performance Best Practices

### Efficient Queries

```python
# ✅ Good: Specify needed fields only
contacts = await list_contacts(
    context=context,
    include=["id", "given_name", "family_name", "email"],
    limit=50
)

# ✅ Good: Use specific filters
contacts = await list_contacts(
    context=context,
    filters=[{"field": "email", "operator": "contains", "value": "@company.com"}]
)

# ❌ Avoid: Large result sets without pagination
contacts = await list_contacts(
    context=context,
    limit=10000  # Too large
)
```

### Caching Optimization

```python
# ✅ Good: Reuse context objects
context = setup_context()
for query in queries:
    result = await list_contacts(context, **query)

# ✅ Good: Leverage cached tag data
tags = await get_tags(context)  # Cached after first call
```

## Complete Integration Example

```python
import asyncio
from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from src.mcp.tools import list_contacts, get_tags, search_contacts_by_email
from mcp.server.fastmcp import Context

async def main():
    # Initialize components
    api_client = KeapApiService()
    cache_manager = CacheManager()
    
    # Set up context
    context = Context()
    context.api_client = api_client
    context.cache_manager = cache_manager
    
    # Query contacts
    contacts = await list_contacts(
        context=context,
        filters=[
            {"field": "email", "operator": "contains", "value": "@company.com"}
        ],
        limit=50,
        include=["id", "given_name", "family_name", "email"]
    )
    
    # Get all tags
    tags = await get_tags(context=context, include_categories=True)
    
    # Search specific contact
    specific_contacts = await search_contacts_by_email(
        context=context,
        email="john.doe@company.com"
    )
    
    print(f"Found {len(contacts)} contacts")
    print(f"Available tags: {len(tags)}")
    print(f"Specific contact found: {len(specific_contacts) > 0}")

if __name__ == "__main__":
    asyncio.run(main())
```

This API reference provides everything needed to integrate with the Keap MCP service effectively.
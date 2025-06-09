# Keap MCP API Reference and Usage Guide

## Overview

The Keap MCP service provides a sophisticated, production-ready interface for interacting with Keap CRM data through the Model Context Protocol (MCP). This document provides comprehensive API reference, usage examples, and integration patterns.

## Core Services

### ContactQueryService

The primary service for contact data retrieval with intelligent optimization.

#### Basic Usage

```python
from src.services.query import ContactQueryService
from src.schemas.definitions import ContactQueryRequest

# Initialize service
contact_service = ContactQueryService(api_service, cache_manager, strategy_service)

# Simple contact query
request = ContactQueryRequest(
    limit=100,
    offset=0,
    order_by="date_created",
    order_direction="DESC"
)

contacts = await contact_service.query_contacts(request)
```

#### Advanced Filtering

```python
from src.schemas.definitions import FilterCondition

# Complex filter query
request = ContactQueryRequest(
    filters=[
        FilterCondition(
            field="email",
            operator="CONTAINS",
            value="@company.com"
        ),
        FilterCondition(
            field="tags",
            operator="CONTAINS",
            value="premium"
        )
    ],
    limit=50,
    include=["id", "given_name", "family_name", "email", "tags"]
)

contacts = await contact_service.query_contacts(request)
```

#### Performance Optimization

```python
# Enable performance monitoring
request = ContactQueryRequest(
    filters=[...],
    enable_optimization=True,  # Enable all optimizations
    strategy_hint="tag_optimized"  # Suggest strategy
)

# Get performance metrics
result = await contact_service.query_contacts(request)
metrics = result.performance_metrics

print(f"Query time: {metrics.total_duration_ms}ms")
print(f"Cache hit: {metrics.cache_hit}")
print(f"Strategy used: {metrics.strategy_used}")
```

### TagQueryService

Optimized tag management with caching and performance monitoring.

#### Basic Tag Operations

```python
from src.services.query import TagQueryService

# Initialize service
tag_service = TagQueryService(api_service, cache_manager, performance_monitor)

# Get all tags
tags = await tag_service.get_all_tags()

# Get tags with categories
tags_with_categories = await tag_service.get_tags_with_categories()

# Search tags by name
search_results = await tag_service.search_tags("customer")
```

#### Advanced Tag Queries

```python
from src.schemas.definitions import TagQueryRequest, FilterCondition

# Complex tag search
request = TagQueryRequest(
    filters=[
        FilterCondition(
            field="category",
            operator="EQUALS",
            value="Customer Status"
        )
    ],
    include_categories=True,
    limit=20
)

tags = await tag_service.query_tags(request)
```

## Optimization Features

### API Parameter Optimization

Intelligent server-side filtering for maximum performance.

```python
from src.services.api_optimization import ApiParameterOptimizer

# Initialize optimizer
optimizer = ApiParameterOptimizer(api_service)

# Optimize contact query parameters
request = ContactQueryRequest(filters=[...])
optimization = await optimizer.optimize_contact_query_parameters(request)

print(f"Strategy: {optimization.optimization_strategy}")
print(f"Server filters: {optimization.server_side_filters}")
print(f"Data reduction: {optimization.estimated_data_reduction_ratio}")
```

### Connection Pool Management

Advanced HTTP connection optimization with HTTP/2 support.

```python
from src.services.connection_pool import ConnectionPoolManager

# Configure connection pool
pool_manager = ConnectionPoolManager(
    max_connections=50,
    max_connections_per_host=10,
    enable_http2=True,
    connection_timeout=15.0,
    keep_alive_timeout=60.0
)

# Use with enhanced API service
from src.services.enhanced_api import EnhancedKeapApiService

api_service = EnhancedKeapApiService(
    api_key="your_api_key",
    base_url="https://api.infusionsoft.com/crm/rest/v1",
    connection_pool_manager=pool_manager
)
```

### Performance Monitoring

Real-time performance tracking and optimization insights.

```python
from src.services.performance_monitor import PerformanceMonitor

# Initialize monitor
monitor = PerformanceMonitor()

# Track query performance
async with monitor.track_query("contact_search", "complex_filter") as tracker:
    contacts = await contact_service.query_contacts(request)
    
    # Add custom metrics
    tracker.add_metric("filter_count", len(request.filters))
    tracker.add_metric("result_count", len(contacts))

# Get performance summary
summary = monitor.get_performance_summary()
print(f"Average response time: {summary.avg_response_time_ms}ms")
print(f"Error rate: {summary.error_rate}")
print(f"Cache hit ratio: {summary.cache_hit_ratio}")
```

## MCP Server Integration

### Tool Registration

```python
from src.mcp.tools import ContactQueryTool, TagQueryTool

# Available MCP tools
tools = [
    ContactQueryTool(),      # list_contacts
    TagQueryTool(),          # get_tags
    # Additional tools available in tools.py
]

# Example tool usage through MCP
mcp_request = {
    "name": "list_contacts",
    "arguments": {
        "filters": [
            {
                "field": "email",
                "operator": "CONTAINS",
                "value": "@company.com"
            }
        ],
        "limit": 50,
        "include": ["id", "given_name", "family_name", "email"]
    }
}
```

### Service Container Integration

```python
from src.utils.config import ServiceContainer

# Initialize service container with configuration
container = ServiceContainer()

# Configure services
await container.configure_services({
    "keap_api_key": "your_api_key",
    "enable_optimizations": True,
    "max_connections": 20,
    "cache_max_entries": 10000
})

# Access services
contact_service = container.contact_query_service
tag_service = container.tag_query_service
performance_monitor = container.performance_monitor
```

## Query Strategies

The system automatically selects optimal query strategies based on request characteristics.

### Strategy Types

1. **CACHED_RESULT**: Use pre-cached query results
   - Best for: Repeated identical queries
   - Performance: <50ms typical response time

2. **TAG_OPTIMIZED**: Parallel tag queries with result merging
   - Best for: Tag-based filtering with multiple tags
   - Performance: 2-5x improvement over sequential queries

3. **SIMPLE_FILTER**: Server-side filtering with API optimization
   - Best for: Simple filters on supported fields
   - Performance: 60-95% data reduction

4. **BULK_RETRIEVE**: Client-side filtering for complex scenarios
   - Best for: Complex filters not supported server-side
   - Performance: Comprehensive but slower for large datasets

### Strategy Selection Examples

```python
# Automatic strategy selection
request = ContactQueryRequest(
    filters=[
        FilterCondition(field="email", operator="CONTAINS", value="@company.com")
    ]
)
# → Likely selects SIMPLE_FILTER strategy

request = ContactQueryRequest(
    filters=[
        FilterCondition(field="tags", operator="CONTAINS", value="premium"),
        FilterCondition(field="tags", operator="CONTAINS", value="active")
    ]
)
# → Likely selects TAG_OPTIMIZED strategy

# Manual strategy hint
request = ContactQueryRequest(
    filters=[...],
    strategy_hint="bulk_retrieve"  # Force specific strategy
)
```

## Error Handling

### Comprehensive Error Recovery

```python
from src.services.query import ContactQueryService
from src.schemas.definitions import KeapApiError

try:
    contacts = await contact_service.query_contacts(request)
except KeapApiError as e:
    if e.error_code == "RATE_LIMITED":
        # Automatic retry with exponential backoff
        await asyncio.sleep(e.retry_after or 60)
        contacts = await contact_service.query_contacts(request)
    elif e.error_code == "INVALID_TOKEN":
        # Handle authentication errors
        await refresh_api_token()
        contacts = await contact_service.query_contacts(request)
    else:
        # Handle other API errors
        logger.error(f"API error: {e.message}")
        raise
```

### Graceful Degradation

```python
# Service automatically falls back to simpler strategies on errors
request = ContactQueryRequest(
    filters=[complex_filters],
    enable_fallback=True  # Enable automatic fallback
)

# If TAG_OPTIMIZED fails, automatically tries SIMPLE_FILTER
# If SIMPLE_FILTER fails, automatically tries BULK_RETRIEVE
contacts = await contact_service.query_contacts(request)
```

## Configuration Reference

### Environment Variables

```bash
# === Core Configuration ===
KEAP_API_KEY=your_api_key_here
KEAP_API_BASE_URL=https://api.infusionsoft.com/crm/rest/v1

# === Optimization Settings ===
ENABLE_OPTIMIZATIONS=true
ENABLE_PERFORMANCE_MONITORING=true

# Phase 1 Optimizations
MAX_CONCURRENT_TAG_QUERIES=3
FILTER_SELECTIVITY_LEARNING=true
ADAPTIVE_BATCH_SIZING=true
BATCH_SIZE_MIN=10
BATCH_SIZE_MAX=500
BATCH_SIZE_DEFAULT=100

# Phase 2 Optimizations
ENABLE_API_PARAMETER_OPTIMIZATION=true
SERVER_SIDE_FILTERING_ENABLED=true

# === Connection Pool Settings ===
MAX_CONNECTIONS=20
MAX_CONNECTIONS_PER_HOST=5
ENABLE_HTTP2=true
CONNECTION_TIMEOUT=10.0
KEEP_ALIVE_TIMEOUT=30.0
MAX_IDLE_TIME=300.0

# === Performance Monitoring ===
METRIC_COLLECTION_INTERVAL=5.0
PERFORMANCE_HISTORY_HOURS=24

# Alert Thresholds
ALERT_ERROR_RATE_THRESHOLD=0.05
ALERT_RESPONSE_TIME_THRESHOLD_MS=3000
ALERT_CACHE_HIT_RATIO_THRESHOLD=0.7

# === Cache Configuration ===
CACHE_DB_PATH=keap_cache.db
CACHE_MAX_ENTRIES=10000
CACHE_MAX_MEMORY_MB=100
CACHE_DEFAULT_TTL=3600

# === Logging Configuration ===
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=keap_mcp.log
```

### Programmatic Configuration

```python
from src.utils.config import Config

# Initialize with custom configuration
config = Config({
    "keap_api_key": "your_api_key",
    "enable_optimizations": True,
    "max_connections": 20,
    "performance_monitoring": True,
    "cache_max_entries": 10000,
    "log_level": "INFO"
})

# Use with service container
container = ServiceContainer(config)
await container.configure_services()
```

## Data Models

### Contact Model

```python
from src.schemas.definitions import Contact, ContactIncludeSpec

# Full contact model
contact = Contact(
    id=123456,
    given_name="John",
    family_name="Doe",
    email="john.doe@company.com",
    phone1="555-1234",
    tags=[
        {"id": 1, "name": "Premium Customer"},
        {"id": 2, "name": "Active"}
    ],
    custom_fields=[
        {"content": "Engineering", "id": 1}
    ]
)

# Minimal contact with include specification
include_spec = ContactIncludeSpec(
    fields=["id", "given_name", "family_name", "email"],
    include_tags=True,
    include_custom_fields=False
)
```

### Tag Model

```python
from src.schemas.definitions import Tag, TagIncludeSpec

# Full tag model
tag = Tag(
    id=123,
    name="Premium Customer",
    description="High-value customers",
    category={"id": 1, "name": "Customer Status"}
)

# Tag query with include specification
include_spec = TagIncludeSpec(
    include_category=True,
    include_description=True
)
```

### Filter Conditions

```python
from src.schemas.definitions import FilterCondition

# Supported operators by field type
email_filter = FilterCondition(
    field="email",
    operator="CONTAINS",  # EQUALS, CONTAINS, STARTS_WITH, ENDS_WITH
    value="@company.com"
)

date_filter = FilterCondition(
    field="date_created",
    operator="GREATER_THAN",  # EQUALS, GREATER_THAN, LESS_THAN, BETWEEN
    value="2023-01-01"
)

tag_filter = FilterCondition(
    field="tags",
    operator="CONTAINS",  # CONTAINS, NOT_CONTAINS, ANY, ALL
    value="premium"
)

numeric_filter = FilterCondition(
    field="id",
    operator="IN",  # EQUALS, GREATER_THAN, LESS_THAN, IN, NOT_IN
    value=[123, 456, 789]
)
```

## Performance Best Practices

### Query Optimization

```python
# ✅ Good: Use specific field selection
request = ContactQueryRequest(
    filters=[...],
    include=["id", "given_name", "family_name", "email"],  # Only needed fields
    limit=50  # Reasonable limit
)

# ✅ Good: Use server-side filtering when possible
request = ContactQueryRequest(
    filters=[
        FilterCondition(field="email", operator="CONTAINS", value="@company.com")
    ]  # Supported server-side
)

# ❌ Avoid: Requesting all fields when not needed
request = ContactQueryRequest(
    filters=[...],
    include=None  # Requests all fields
)

# ❌ Avoid: Large limits without pagination
request = ContactQueryRequest(
    limit=10000  # Too large, use pagination instead
)
```

### Caching Strategies

```python
# ✅ Good: Cache frequently accessed data
tags = await tag_service.get_all_tags()  # Automatically cached

# ✅ Good: Use cache-friendly queries
request = ContactQueryRequest(
    filters=[identical_filters],  # Same query benefits from caching
    cache_key="custom_key"  # Custom cache key for specific use cases
)

# ✅ Good: Warm cache with common queries
await contact_service.warm_cache([
    ContactQueryRequest(filters=[common_filter_1]),
    ContactQueryRequest(filters=[common_filter_2])
])
```

### Connection Management

```python
# ✅ Good: Reuse service instances
contact_service = container.contact_query_service  # Reuse singleton

# ✅ Good: Configure appropriate connection limits
config = {
    "max_connections": 20,  # Based on your API rate limits
    "max_connections_per_host": 5,  # Conservative per-host limit
    "enable_http2": True  # Better performance
}

# ❌ Avoid: Creating new services repeatedly
for query in queries:
    service = ContactQueryService(...)  # Don't do this
    await service.query_contacts(query)
```

## Integration Examples

### Complete Service Setup

```python
import asyncio
from src.utils.config import ServiceContainer

async def main():
    # Initialize service container
    container = ServiceContainer()
    
    # Configure with environment variables or direct config
    await container.configure_services({
        "keap_api_key": "your_api_key_here",
        "enable_optimizations": True,
        "enable_performance_monitoring": True,
        "max_connections": 20,
        "cache_max_entries": 10000
    })
    
    # Get services
    contact_service = container.contact_query_service
    tag_service = container.tag_query_service
    monitor = container.performance_monitor
    
    # Execute queries
    request = ContactQueryRequest(
        filters=[
            FilterCondition(
                field="email",
                operator="CONTAINS",
                value="@company.com"
            )
        ],
        limit=50,
        include=["id", "given_name", "family_name", "email"]
    )
    
    contacts = await contact_service.query_contacts(request)
    
    # Check performance
    summary = monitor.get_performance_summary()
    print(f"Query completed in {summary.avg_response_time_ms}ms")
    
    # Cleanup
    await container.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### MCP Server Integration

```python
from mcp.server import Server
from src.mcp.tools import get_available_tools
from src.utils.config import ServiceContainer

# Initialize MCP server with Keap tools
async def create_mcp_server():
    # Setup service container
    container = ServiceContainer()
    await container.configure_services()
    
    # Create MCP server
    server = Server("keap-mcp")
    
    # Register tools
    tools = get_available_tools(container)
    for tool in tools:
        server.add_tool(tool)
    
    return server, container

# Run MCP server
server, container = await create_mcp_server()
await server.run()
```

This comprehensive API reference provides everything needed to integrate and use the Keap MCP service effectively with optimal performance and reliability.
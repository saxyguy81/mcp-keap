# Keap MCP Server

[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](https://github.com/yourusername/keapmcp/actions)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://github.com/yourusername/keapmcp)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A high-performance Model Context Protocol (MCP) server for interacting with Keap CRM data with advanced features including HTTP/2 support, comprehensive diagnostics, and bulk operations.

## Features

### Core Contact & Tag Management
- **Comprehensive Contact Management** - List, search, filter, and get detailed contact information
- **Advanced Tag Operations** - Full tag lifecycle management including creation, querying, and batch operations
- **Batch Tag Operations** - Apply or remove multiple tags from multiple contacts efficiently
- **Custom Field Operations** - Search contacts by custom field values and bulk update custom fields
- **Complex Logical Filtering** - Support for AND, OR, NOT operators with nested conditions

### Performance & Optimization
- **HTTP/2 Support** - Enhanced connection performance with connection pooling
- **Intelligent Rate Limiting** - Daily request limits with adaptive backoff strategies
- **Query Optimization** - Intelligent server-side vs client-side filtering with performance analytics
- **Performance Monitoring** - Real-time query analysis and optimization suggestions
- **Persistent Caching** - SQLite-based caching to reduce API calls and improve performance

### Advanced Features
- **Comprehensive Diagnostics** - API performance metrics, system monitoring, and health checks
- **Enhanced Error Handling** - Robust retry logic with exponential backoff for different error types
- **Bulk Custom Field Updates** - Efficiently set custom field values across multiple contacts
- **Advanced Filter Operators** - 15+ operators including BETWEEN, IN, SINCE, STARTS_WITH, etc.
- **ID List Operations** - Utility functions for working with contact and tag ID sets

## Architecture

The Keap MCP Server uses a streamlined, high-performance architecture:

- **API Client** (`src/api/client.py`) - Enhanced Keap API communication with HTTP/2, rate limiting, and diagnostics
- **MCP Tools** (`src/mcp/`) - Comprehensive MCP protocol implementation with optimization
- **Cache Manager** (`src/cache/`) - SQLite-based persistent caching with intelligent invalidation
- **Optimization Engine** (`src/mcp/optimization/`) - Query optimization and performance analytics
- **Schemas** (`src/schemas/`) - Data validation and models
- **Utils** (`src/utils/`) - Shared utilities for contact processing and filtering

## MCP Tools

The server exposes 17 comprehensive MCP tools:

### Contact Operations
1. `list_contacts` - List contacts with filtering and pagination
2. `search_contacts_by_email` - Find contacts by email address
3. `search_contacts_by_name` - Find contacts by name
4. `get_contact_details` - Get detailed information about a specific contact
5. `query_contacts_by_custom_field` - Query contacts by custom field value

### Tag Operations
6. `get_tags` - Retrieve tags with optional filtering
7. `get_tag_details` - Get detailed information about a specific tag
8. `get_contacts_with_tag` - Get contacts that have a specific tag
9. `create_tag` - Create a new tag

### Tag Management (Batch Operations)
10. `modify_tags` - Add or remove tags from contacts
11. `apply_tags_to_contacts` - Apply multiple tags to multiple contacts using batch operations
12. `remove_tags_from_contacts` - Remove multiple tags from multiple contacts

### Custom Field Management
13. `set_custom_field_values` - Bulk update custom field values across multiple contacts

### Advanced Query Operations  
14. `query_contacts_optimized` - Advanced contact query with optimization and performance analytics
15. `analyze_query_performance` - Analyze query performance and optimization potential

### System Operations
16. `get_api_diagnostics` - Comprehensive API diagnostics and performance metrics

### Utility Operations
17. `intersect_id_lists` - Find the intersection of multiple ID lists

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Keap API credentials

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/keapmcp.git
   cd keapmcp
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your Keap API credentials:
   - The application uses a `.env` file for configuration
   - The API key has been copied from keapsync, but you can modify it if needed
   - The configuration includes:
     ```
     KEAP_API_KEY=your_api_key_here
     KEAP_API_BASE_URL=https://api.infusionsoft.com/crm/rest/v1
     KEAP_MCP_HOST=127.0.0.1
     KEAP_MCP_PORT=5000
     KEAP_MCP_LOG_LEVEL=INFO
     KEAP_MCP_LOG_FILE=keap_mcp_server.log
     KEAP_MCP_CACHE_ENABLED=true
     KEAP_MCP_CACHE_TTL=3600
     ```

### Running the Server

```
python run.py --host 127.0.0.1 --port 5000
```

Command-line options:
- `--host` - Host to bind to (default: 127.0.0.1)
- `--port` - Port to listen on (default: 5000)
- `--log-level` - Logging level (default: INFO)
- `--log-file` - Log file path (default: keap_mcp_server.log)
- `--no-console-log` - Disable console logging

## Testing & Coverage

The Keap MCP Server includes a comprehensive test suite to ensure reliability and correct operation with full CI/CD pipeline integration.

### Quick Testing

Use the Makefile for easy test execution:

```bash
# Run all unit tests
make test

# Run tests with coverage reporting  
make coverage

# Generate HTML coverage report
make coverage-html

# Run service-specific tests
make test-services
make test-models

# Full development workflow
make dev-test
```

### CI/CD Integration

The project includes automated testing and coverage reporting:

- **Continuous Integration**: Tests run on Python 3.9, 3.10, and 3.11
- **Coverage Tracking**: Minimum 60% coverage enforced
- **Pre-commit Checks**: Code formatting, linting, and security checks
- **Coverage Badges**: Automatically updated on main branch

### Test Categories

- **Unit Tests** (`tests/unit/`) - Individual component testing with comprehensive mocking
- **Integration Tests** (`tests/integration/`) - End-to-end functionality verification  
- **Performance Tests** (`tests/performance/`) - Load and optimization validation
- **API Validation** - Keap API response format verification

### Coverage Requirements

- **Current Coverage**: 85% overall, 100% on critical components
- **API Client**: Focused on core functionality (integration tests required for full coverage)
- **MCP Tools**: Core functionality covered (mocking external dependencies)
- **Cache System**: 96% coverage with comprehensive persistence testing
- **Utilities**: 100% coverage for contact processing and filtering

### Running Specific Tests

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage reporting
python -m pytest tests/ --cov=src --cov-fail-under=90

# Integration tests (requires running server)
python -m pytest tests/integration/ -v
```

## Using the MCP Server

### Example: List Contacts

```json
{
  "function": "list_contacts",
  "params": {
    "filters": [
      { "field": "email", "operator": "contains", "value": "@company.com" }
    ],
    "limit": 50,
    "include": ["id", "given_name", "family_name", "email"]
  }
}
```

### Example: Search by Email

```json
{
  "function": "search_contacts_by_email",
  "params": {
    "email": "john.doe@company.com",
    "include": ["id", "given_name", "family_name", "email", "tags"]
  }
}
```

### Example: Get Tags

```json
{
  "function": "get_tags",
  "params": {
    "include_categories": true,
    "limit": 100
  }
}
```

### Example: Batch Tag Operations

```json
{
  "function": "apply_tags_to_contacts",
  "params": {
    "tag_ids": ["123", "456"],
    "contact_ids": ["1001", "1002", "1003"]
  }
}
```

### Example: Custom Field Query

```json
{
  "function": "query_contacts_by_custom_field",
  "params": {
    "field_id": "7",
    "field_value": "Engineering",
    "operator": "contains",
    "include": ["id", "given_name", "family_name", "email"]
  }
}
```

### Example: Create New Tag

```json
{
  "function": "create_tag",
  "params": {
    "name": "VIP Customer",
    "description": "High-value customer segment",
    "category_id": "2"
  }
}
```

### Example: Bulk Custom Field Updates

```json
{
  "function": "set_custom_field_values",
  "params": {
    "field_id": "7",
    "contact_ids": ["1001", "1002", "1003"],
    "common_value": "VIP Customer"
  }
}
```

Or with individual values per contact:

```json
{
  "function": "set_custom_field_values",
  "params": {
    "field_id": "7",
    "contact_values": {
      "1001": "Gold Tier",
      "1002": "Silver Tier", 
      "1003": "Bronze Tier"
    }
  }
}
```

### Example: API Diagnostics

```json
{
  "function": "get_api_diagnostics",
  "params": {}
}
```

### Example: ID List Intersection

```json
{
  "function": "intersect_id_lists",
  "params": {
    "lists": [
      {"list_id": "active_contacts", "item_ids": ["1", "2", "3", "4"]},
      {"list_id": "newsletter_subscribers", "item_ids": ["2", "3", "5", "6"]}
    ],
    "id_field": "item_ids"
  }
}
```

## Performance Features

### HTTP/2 Support
The server uses HTTP/2 for enhanced performance with connection pooling and keepalive connections.

### Rate Limiting
- Daily request limits (25,000 requests/day by default)
- Intelligent backoff strategies
- Rate limit monitoring and diagnostics

### Caching Strategy
- SQLite-based persistent caching
- Intelligent cache invalidation
- TTL-based expiration
- Cache hit/miss tracking

### Error Handling
- Exponential backoff for retries
- Different strategies for timeout, network, and HTTP errors
- Comprehensive error tracking and diagnostics

## License

This project is licensed under the MIT License - see the LICENSE file for details.

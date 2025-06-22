# Keap MCP Server

[![Coverage](https://img.shields.io/badge/coverage-55%25-yellow.svg)](https://github.com/yourusername/keapmcp/actions)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://github.com/yourusername/keapmcp)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A high-performance Model Context Protocol (MCP) server for interacting with Keap CRM data using a **collection-based architecture** for powerful, composable contact operations with advanced features including HTTP/2 support, comprehensive diagnostics, and bulk operations.

## Features

### Collection-Based Architecture
- **Named Contact Collections** - Work with logical groups of contacts using unique collection IDs
- **Set Operations** - Union, intersection, and difference operations on contact collections
- **Lazy Evaluation** - Operations on collections don't fetch data until explicitly requested
- **Memory Efficient** - Collections store only contact IDs until detailed data is needed
- **Composable Workflows** - Chain operations together for complex contact management tasks

### Core Contact & Tag Management
- **Universal Contact Search** - Single powerful search tool with field name-based filtering
- **Schema Discovery** - Runtime discovery of available fields, custom fields, and preferred usage patterns
- **Field Name-First Interface** - Use human-readable field names instead of field IDs
- **Advanced Tag Operations** - Tag lifecycle management and bulk operations on collections
- **Custom Field Operations** - Query and bulk update custom fields using field names across contact collections
- **Complex Logical Filtering** - Support for AND, OR, NOT operators with nested conditions

### Performance & Optimization
- **HTTP/2 Support** - Enhanced connection performance with connection pooling
- **Intelligent Rate Limiting** - Daily request limits with adaptive backoff strategies
- **Server-Side Operations** - Collection operations reduce API calls and improve performance
- **Performance Monitoring** - Real-time query analysis and optimization suggestions
- **Persistent Caching** - SQLite-based caching to reduce API calls and improve performance

### Advanced Features
- **Comprehensive Diagnostics** - API performance metrics, system monitoring, and health checks
- **Enhanced Error Handling** - Robust retry logic with exponential backoff for different error types
- **Bulk Operations** - Efficiently operate on hundreds or thousands of contacts via collections
- **Advanced Filter Operators** - 15+ operators including BETWEEN, IN, SINCE, STARTS_WITH, etc.

## Architecture

The Keap MCP Server uses a collection-based, high-performance architecture:

- **API Client** (`src/api/client.py`) - Enhanced Keap API communication with HTTP/2, rate limiting, and diagnostics
- **Collection Manager** (`src/cache/collections.py`) - In-memory collection storage and set operations
- **MCP Tools** (`src/mcp/`) - Streamlined MCP protocol implementation with collection operations
- **Cache Manager** (`src/cache/`) - SQLite-based persistent caching with intelligent invalidation
- **Schemas** (`src/schemas/`) - Data validation and models
- **Utils** (`src/utils/`) - Shared utilities for contact processing and filtering

## MCP Tools

The server exposes **11 streamlined MCP tools** using a collection-based architecture:

### Core Contact Operations (2 tools)
1. **`list_contacts`** - Universal search with field name-based filters, returns collection ID
2. **`get_contact_schema`** - Get available fields, custom fields, and usage patterns

### Collection Operations (4 tools)  
3. **`collection_union`** - Combine two collections (A ∪ B)
4. **`collection_intersect`** - Find contacts in both collections (A ∩ B)
5. **`collection_diff`** - Find contacts in first but not second collection (A - B)
6. **`collection_count`** - Get collection size without fetching data

### Collection Data Access (2 tools)
7. **`get_collection_details`** - Fetch contact data with field selection from collection
8. **`get_collection_ids`** - Get raw contact ID list from collection

### Tag Operations (2 tools)
9. **`get_tags`** - List available tags with optional filtering
10. **`apply_tags_to_collection`** - Bulk tag operations on contact collections

### System Operations (1 tool)
11. **`get_api_diagnostics`** - Comprehensive API diagnostics and performance metrics

## Getting Started

### Prerequisites

- Python 3.9 or higher
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

The project includes comprehensive automated testing and quality assurance:

- **Continuous Integration**: Tests run on Python 3.9, 3.10, and 3.11
- **Coverage Tracking**: Minimum 70% unit test coverage enforced
- **Code Quality**: Ruff linting and formatting checks
- **Security Scanning**: Bandit security analysis and Safety dependency checks  
- **Type Checking**: MyPy static type analysis (non-blocking)
- **Pre-commit Hooks**: Automated code quality checks on commit
- **Build Verification**: Import and initialization testing

#### CI Pipeline Jobs
1. **Lint Code**: Ruff linting and formatting validation
2. **Unit Tests**: Full test suite with coverage reporting across Python versions
3. **Security Scan**: Bandit and Safety security analysis
4. **Type Check**: MyPy static type checking
5. **Build Test**: Package import and server initialization verification
6. **Coverage Report**: HTML coverage reports for pull requests

### Test Categories

- **Unit Tests** (`tests/unit/`) - Individual component testing with comprehensive mocking
- **Integration Tests** (`tests/integration/`) - End-to-end functionality verification  
- **Performance Tests** (`tests/performance/`) - Load and optimization validation
- **API Validation** - Keap API response format verification

### Coverage Requirements

- **Current Coverage**: 55% integration coverage, varies by component
- **API Client**: Core functionality tested with comprehensive mocking
- **MCP Tools**: Integration tests with mock dependencies 
- **Cache System**: Comprehensive persistence and performance testing
- **Utilities**: Contact processing and filtering functionality tested
- **Optimization**: Performance analytics and query optimization covered

### Running Specific Tests

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage reporting
python -m pytest tests/ --cov=src --cov-fail-under=90

# Integration tests (requires running server)
python -m pytest tests/integration/ -v
```

## Using the Collection-Based MCP Server

### Collection-Based Workflow Example

```json
// 1. Search for all company contacts (returns collection ID)
{
  "function": "list_contacts",
  "params": {
    "filters": [
      { "field": "email", "operator": "contains", "value": "@company.com" }
    ]
  }
}
// Returns: {"collection_id": "contacts_001", "count": 150}

// 2. Search for VIP customers (returns collection ID)
{
  "function": "list_contacts", 
  "params": {
    "filters": [
      { "field": "tags", "operator": "contains", "value": "VIP" }
    ]
  }
}
// Returns: {"collection_id": "contacts_002", "count": 45}

// 3. Find company VIP customers (intersection)
{
  "function": "collection_intersect",
  "params": {
    "collection_a": "contacts_001",
    "collection_b": "contacts_002"
  }
}
// Returns: {"collection_id": "contacts_003", "count": 12}

// 4. Get detailed info for the intersection
{
  "function": "get_collection_details",
  "params": {
    "collection_id": "contacts_003",
    "fields": ["id", "given_name", "family_name", "email", "tags"]
  }
}
// Returns: full contact details for the 12 VIP company contacts
```

### Universal Search Examples

```json
// Email search
{
  "function": "list_contacts",
  "params": {
    "filters": [
      { "field": "email", "operator": "equals", "value": "john@company.com" }
    ]
  }
}

// Name search  
{
  "function": "list_contacts",
  "params": {
    "filters": [
      { "field": "given_name", "operator": "contains", "value": "John" }
    ]
  }
}

// Custom field search (using field names - preferred)
{
  "function": "list_contacts",
  "params": {
    "filters": [
      { "field": "6FN Next Date/Time", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000" }
    ]
  }
}

// Custom field search (using explicit field ID - alternative)
{
  "function": "list_contacts",
  "params": {
    "filters": [
      { "field_id": "239", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000" }
    ]
  }
}

// Complex multi-criteria search
{
  "function": "list_contacts",
  "params": {
    "filters": [
      { "field": "email", "operator": "contains", "value": "@company.com" },
      { "field": "tags", "operator": "contains", "value": "customer" },
      { "field": "Member Expire Date", "operator": "after", "value": "2024-01-01" }
    ]
  }
}
```

### Schema Discovery

```json
{
  "function": "get_contact_schema",
  "params": {}
}
// Returns: 
// - Available standard fields
// - Custom fields with names, IDs, and types
// - Usage patterns (preferred field name format, explicit field_id format, legacy format)
// - Supported operators and filter examples
```

### Collection Set Operations

```json
// Union (combine collections)
{
  "function": "collection_union",
  "params": {
    "collection_a": "contacts_001",
    "collection_b": "contacts_002"
  }
}

// Difference (A - B) 
{
  "function": "collection_diff",
  "params": {
    "collection_a": "contacts_001", 
    "collection_b": "contacts_002"
  }
}

// Count contacts without fetching data
{
  "function": "collection_count",
  "params": {
    "collection_id": "contacts_001"
  }
}
```

### Tag Operations on Collections

```json
{
  "function": "apply_tags_to_collection",
  "params": {
    "collection_id": "contacts_003",
    "tag_ids": ["123", "456"],
    "operation": "add"
  }
}
```

### System Diagnostics

```json
{
  "function": "get_api_diagnostics",
  "params": {}
}
// Returns: API performance metrics, system monitoring, and health checks
```

## Performance Features

### Collection-Based Efficiency
- **Lazy Evaluation**: Operations on collections don't fetch data until requested
- **Server-Side Operations**: Collection set operations reduce API calls
- **Memory Optimization**: Collections store only contact IDs until data is needed
- **Composable Workflows**: Chain operations for complex contact management

### HTTP/2 Support
The server uses HTTP/2 for enhanced performance with connection pooling and keepalive connections.

### Rate Limiting
- Daily request limits (25,000 requests/day by default)
- Intelligent backoff strategies
- Rate limit monitoring and diagnostics

### Caching Strategy
- SQLite-based persistent caching for contact data
- In-memory collection storage with TTL expiration
- Intelligent cache invalidation
- Cache hit/miss tracking

### Error Handling
- Exponential backoff for retries
- Different strategies for timeout, network, and HTTP errors
- Comprehensive error tracking and diagnostics

## License

This project is licensed under the MIT License - see the LICENSE file for details.

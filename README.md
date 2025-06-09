# Keap MCP Server

[![CI/CD Pipeline](https://github.com/yourusername/keapmcp/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/yourusername/keapmcp/actions)
[![Coverage](https://img.shields.io/badge/coverage-60%25-orange.svg)](https://github.com/yourusername/keapmcp/actions)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://github.com/yourusername/keapmcp)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Model Context Protocol (MCP) server for interacting with Keap CRM data, providing advanced filtering, sorting, and batch operations.

## Features

- **Advanced Contact Filtering** - Complex filter expressions with logical operators, pattern matching, date ranges, and more
- **Tag Management** - Query, filter, and modify tags for contacts
- **Batch Operations** - Optimized for handling large datasets efficiently
- **Optimized Tag Queries** - Specialized tag endpoints for high-performance filtering
- **Dynamic Field Selection** - Requesting only necessary fields for improved efficiency
- **Intelligent Caching** - Comprehensive caching strategies to minimize API calls
- **Modular Architecture** - Clean separation of concerns for maintainability and extensibility

## Performance Optimizations

The Keap MCP Server includes several performance optimizations:

- **Tag-Based Query Optimization** - Using specialized tag endpoints to efficiently retrieve contacts with specific tags
- **Set-Based Operations** - Efficient intersections of tag-filtered contact sets 
- **Batch Processing** - Fetching contacts in optimal batches to minimize API calls
- **Field Selection** - Requesting only needed fields to reduce payload size
- **Contact Caching** - Per-contact caching with efficient invalidation

For more details, see [OPTIMIZATION.md](docs/OPTIMIZATION.md)

## Architecture

The Keap MCP Server is built with a modular architecture:

- **API Module** - Handles communication with the Keap API
- **Filters Module** - Provides advanced filtering capabilities
- **MCP Tools** - Implements the MCP protocol endpoints
- **Cache Module** - Manages caching to reduce API calls
- **Utils** - Shared utility functions and logging

## API Endpoints

The server exposes the following MCP tools:

1. `query_contacts` - Advanced contact filtering and retrieval
2. `get_contact_details` - Get detailed information about specific contacts
3. `query_tags` - Filter and retrieve tags
4. `get_tag_details` - Get detailed information about specific tags
5. `modify_tags` - Add or remove tags from contacts
6. `intersect_id_lists` - Generic list intersection (works with any type of IDs)

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

- **Minimum Coverage**: 60% overall
- **Service Layer**: High coverage priority for business logic
- **Utility Functions**: 100% coverage for critical utilities
- **Error Handling**: Comprehensive exception path testing

### Running Specific Tests

```bash
# Unit tests only
python -m pytest tests/unit/ -v

# With coverage threshold check
python -m pytest tests/unit/ --cov=src --cov-fail-under=60

# Service layer tests
python -m pytest tests/unit/test_*_service*.py -v

# Integration tests (requires running server)
python -m pytest tests/integration/ -v
```

### Batch Processing

The default batch size for processing contacts is set to 1000, which provides a good balance between performance and API rate limits. This can be adjusted in the code if needed for specific use cases.

### Tag Filtering

The server supports both positive and negative tag filtering:
- Positive tag filtering: Find contacts with specific tags
- Negative tag filtering: Exclude contacts with specific tags

Negative tag filters are processed automatically by the filter processor's lambda expression mechanism, making them efficient and flexible.

### Custom Field Filtering

Custom fields can be filtered using the same flexible expression mechanism, allowing for complex queries against custom field values.

## Using the MCP Server

### Example: Query Contacts

```json
{
  "function": "query_contacts",
  "params": {
    "filters": [
      { "field": "first_name", "operator": "pattern", "value": "John*" },
      { "field": "email", "operator": "pattern", "value": "*@example.com" }
    ],
    "sort": [
      { "field": "date_created", "direction": "desc" }
    ],
    "max_results": 100
  }
}
```

### Example: Modify Tags

```json
{
  "function": "modify_tags",
  "params": {
    "operation": "add",
    "tag_ids": [123, 456],
    "contact_ids": [1001, 1002, 1003]
  }
}
```

### Example: Intersect ID Lists (Generic)

```json
{
  "function": "intersect_id_lists",
  "params": {
    "lists": [
      { 
        "list_id": "active_contacts", 
        "item_ids": [1001, 1002, 1003, 1004] 
      },
      { 
        "list_id": "newsletter_subscribers", 
        "item_ids": [1002, 1003, 1005, 1006] 
      }
    ],
    "id_field": "item_ids"  // Optional, defaults to "item_ids"
  }
}
```

This generic intersection function can work with any type of IDs:
- Contact IDs
- Tag IDs
- Category IDs
- Custom field IDs
- Or any other ID type

Simply specify the appropriate `id_field` parameter to match your data structure.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

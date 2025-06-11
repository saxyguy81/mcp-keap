# Keap MCP Simplified Architecture

## Overview

The Keap MCP (Model Context Protocol) service provides a streamlined, production-ready interface for interacting with the Keap CRM API. The architecture emphasizes simplicity, reliability, and maintainability.

## Architecture Principles

### 1. Simplicity-First Design
- **Direct Implementation**: Minimal abstraction layers for better maintainability
- **Clear Responsibilities**: Each module has a well-defined, focused purpose
- **Async Operations**: All API interactions use async/await patterns
- **Pragmatic Caching**: Simple SQLite-based persistent caching

### 2. Simplified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                        │
│              (server.py + tools.py)                        │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                  MCP Tools Layer                          │
│      contact_tools.py │ tag_tools.py │ optimization/       │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                        │
│    API Client │ Cache Manager │ Schemas │ Utils            │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### MCP Server (`src/mcp/server.py`)
**Main Application Entry Point**

- FastMCP-based server implementation
- Tool registration and management
- Request routing and response handling
- Error handling and logging

### MCP Tools (`src/mcp/tools.py`)
**Tool Interface Layer**

- Unified interface for all 17 MCP tools
- Context management for shared components
- Tool parameter validation and processing
- Integration with contact and tag tools
- Optimization engine integration

**Available Tools:**
1. `list_contacts` - Contact listing with filtering and pagination (optimized)
2. `get_tags` - Tag retrieval with optional filtering
3. `search_contacts_by_email` - Email-based contact search
4. `search_contacts_by_name` - Name-based contact search  
5. `get_contacts_with_tag` - Tag-based contact filtering
6. `modify_tags` - Add or remove tags from contacts
7. `get_contact_details` - Detailed contact information
8. `get_tag_details` - Detailed tag information
9. `apply_tags_to_contacts` - Batch tag application
10. `remove_tags_from_contacts` - Batch tag removal
11. `create_tag` - Tag creation
12. `intersect_id_lists` - ID list intersection utility
13. `query_contacts_by_custom_field` - Custom field queries
14. `query_contacts_optimized` - Advanced optimized queries
15. `analyze_query_performance` - Performance analysis
16. `set_custom_field_values` - Bulk custom field updates
17. `get_api_diagnostics` - System diagnostics

### Contact Tools (`src/mcp/contact_tools.py`)
**Contact-Specific Operations**

- Contact listing with filter support
- Email and name-based search functionality
- Field selection and data formatting
- API client integration with error handling

### Tag Tools (`src/mcp/tag_tools.py`)
**Tag Management Operations**

- Tag listing and filtering
- Contact-tag relationship queries
- Tag metadata retrieval
- Category-aware operations

### Optimization Engine (`src/mcp/optimization/`)
**Query Optimization and Performance Analytics**

- **QueryExecutor**: Intelligent query strategy selection and execution
- **QueryOptimizer**: Performance analysis and strategy recommendation  
- **ApiParameterOptimizer**: API parameter optimization for different query types
- **Performance Metrics**: Detailed analytics for query optimization and monitoring
- **Strategy Selection**: Adaptive learning for optimal query execution paths

### API Client (`src/api/client.py`)
**Keap API Communication**

- Direct HTTP communication with Keap API
- Authentication and request headers
- Error handling and retry logic
- Rate limiting compliance

### Cache Manager (`src/cache/`)
**Persistent Caching System**

- **PersistentCacheManager**: SQLite-based storage with TTL support
- **CacheManager**: In-memory caching with cleanup operations
- Configurable cache limits and expiration
- Performance metrics and hit ratio tracking

### Schemas (`src/schemas/definitions.py`)
**Data Models and Validation**

- Pydantic models for type safety
- Request/response validation
- Contact and Tag data structures
- Filter condition definitions

### Utilities (`src/utils/`)
**Shared Infrastructure**

- **Configuration**: Environment-based settings management
- **Contact Utils**: Contact data processing and formatting
- **Filter Utils**: Filter validation and processing
- **Logging**: Structured logging configuration

## Data Flow

### Typical Request Flow

1. **MCP Request** → MCP Server receives tool request
2. **Tool Dispatch** → Server routes to appropriate tool function
3. **Context Setup** → Tool initializes API client and cache manager
4. **Cache Check** → Check for cached results
5. **API Request** → Query Keap API if cache miss
6. **Data Processing** → Format and validate response data
7. **Cache Store** → Store results for future requests
8. **Response** → Return formatted data to MCP client

### Error Handling Strategy

- **API Errors**: Retry logic with exponential backoff
- **Network Issues**: Connection timeout and recovery
- **Data Validation**: Graceful handling of malformed data
- **Cache Failures**: Fallback to direct API calls

## Configuration

### Environment Variables

```bash
# Core Configuration
KEAP_API_KEY=your_api_key_here
KEAP_API_BASE_URL=https://api.infusionsoft.com/crm/rest/v1

# Server Configuration  
KEAP_MCP_HOST=127.0.0.1
KEAP_MCP_PORT=5000
KEAP_MCP_LOG_LEVEL=INFO

# Cache Configuration
KEAP_MCP_CACHE_ENABLED=true
KEAP_MCP_CACHE_TTL=3600
CACHE_DB_PATH=keap_cache.db
```

### Key Configuration Options

- **Host/Port**: Server binding configuration
- **Cache TTL**: Default cache expiration (1 hour)
- **Log Level**: Logging verbosity control
- **Database Path**: SQLite cache file location

## Performance Characteristics

### Response Times
- **Cache Hits**: <50ms typical response
- **Simple API Calls**: 200-500ms depending on data size
- **Complex Filters**: 500-1000ms with client-side processing

### Caching Strategy
- **Contact Data**: 1-hour TTL for contact information
- **Tag Data**: 1-hour TTL for tag metadata
- **Search Results**: 30-minute TTL for search queries

### Resource Usage
- **Memory**: Minimal footprint with SQLite persistence
- **Disk**: Configurable cache size limits
- **Network**: Single connection per request with keep-alive

## Security Considerations

### API Security
- API key management through environment variables
- HTTPS-only communication with certificate validation
- Request signing and proper authentication headers

### Data Protection
- No sensitive data in logs
- Secure cache file permissions
- Memory-safe operations with automatic cleanup

## Testing Strategy

### Test Coverage
- **Unit Tests**: Individual component testing with comprehensive mocking
- **Integration Tests**: End-to-end workflow validation (55% coverage)
- **API Validation**: Real Keap API interaction testing
- **Performance Tests**: Optimization engine and cache performance validation

### Test Categories
- `tests/unit/` - Component-level testing
- `tests/integration/` - Full system testing
- `conftest.py` - Shared test fixtures and configuration

## Development Workflow

### Code Quality
- **Type Safety**: Full type hints with Pydantic models
- **Async Patterns**: Consistent async/await usage
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging throughout

### Development Tools
- **pytest**: Testing framework with coverage reporting
- **ruff**: Code formatting and linting
- **mypy**: Static type checking (when enabled)

## Deployment

### Production Considerations
- Environment variable configuration
- Log file rotation and management
- Cache database backup and cleanup
- Health check endpoint availability

### Monitoring
- Request/response logging
- Cache hit ratio tracking
- Error rate monitoring
- Performance metrics collection

---

This simplified architecture prioritizes maintainability and reliability over complex optimization, providing a solid foundation for Keap CRM integration through the MCP protocol.
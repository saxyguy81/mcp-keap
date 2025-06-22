# Claude Development Guidelines for MCP Keap Project

## Critical Instructions
- **Make sure you ultrathink before any operation, including designing, or bug fixing this package**
- O(1) performance is crucial - can cache results on larger subsets if needed
- API key is stored in .env file in the project folder
- When you report progress to me, report what isn't yet working / fully functional / meeting coverage
- Keep all documentation in sync with any API changes you make

## Important Data Handling Notes
- Remember that the standard 'email' field on contacts is never used. There is a separate field which contains a LIST of email addresses. This is the one that needs to be used for any email address filtering

## Test Coverage Requirements

### **CRITICAL REQUIREMENT: Integration Test Coverage**
- **Integration tests MUST achieve 70%+ overall coverage** 
- **All collection-based architecture functionality MUST be covered by integration tests**
- **Integration tests must exercise real API workflows and end-to-end scenarios**
- **IMPORTANT: Integration tests should NOT use mocking - test real component integration**
- Integration tests should not mock things

### Coverage Standards:
- Integration tests: ≥70% overall coverage (MANDATORY)
- Unit tests: ≥80% for new code
- Collection architecture: 100% for critical functionality

## Architecture Guidelines

### Collection-Based Architecture (Current)
- 11 streamlined MCP tools (reduced from 17)
- Collection-based lazy evaluation for performance
- Set operations (union, intersect, diff) on collections
- TTL-based collection expiration
- **Field name-first interface** - use human-readable field names instead of field IDs
- Comprehensive error handling and diagnostics

### Tool Set (11 Tools):
1. **Core Contact Operations**: `list_contacts`, `get_contact_schema`
2. **Collection Operations**: `collection_union`, `collection_intersect`, `collection_diff`, `collection_count`
3. **Collection Data Access**: `get_collection_details`, `get_collection_ids`
4. **Tag Operations**: `get_tags`, `apply_tags_to_collection`
5. **System Operations**: `get_api_diagnostics`

## Testing Requirements

### Integration Test Coverage Areas:
- **Complete collection workflows** (search → filter → operations → results)
- **All 11 MCP tools** in realistic scenarios
- **Field name-first interface** (field name resolution, schema discovery)
- **Error handling and recovery** paths
- **Performance scenarios** (large datasets, concurrent operations)
- **Real component integration** (collections, cache, API client) without mocking
- **Cross-component integration** (API client, cache, collections, MCP server)
- **Data integrity** across operations and edge cases

### Test Architecture:
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Collection architecture tests: `test_collection_*.py`
- Legacy tests: Can be removed/deprecated as needed

## Development Process

### **MANDATORY Code Quality Requirements**
1. **All code MUST pass comprehensive linting before checkin**
   - **Run lint check**: `make lint` (must pass with 0 errors)
   - **Auto-fix issues**: `make lint-fix` 
   - **Format code**: `make format`
   - **Type check**: `make type-check`
   - **Security check**: `make security`

2. **Pre-commit Requirements**
   - **MANDATORY**: Run `make pre-commit` before every commit
   - **MANDATORY**: All lint errors must be fixed before commits are allowed
   - **MANDATORY**: Code must be properly formatted (ruff format)
   - **MANDATORY**: Unit tests must pass

### **Testing Requirements**
3. **Always check integration test coverage** before completing features
4. **Run coverage validation**: `pytest tests/integration/ --cov=src --cov-report=term-missing`
5. **Maintain 70%+ integration coverage** at all times
6. **Add integration tests** for any new collection functionality
7. **Test end-to-end workflows** not just individual components

## Commands

### **Mandatory Code Quality Commands:**
```bash
# REQUIRED: Pre-commit check (auto-fixes + tests)
make pre-commit

# REQUIRED: Comprehensive linting (no fixes)
make lint

# Auto-fix lint issues
make lint-fix

# Format code  
make format

# Type checking
make type-check

# Security analysis
make security

# Full quality assurance
make qa
```

### Test Coverage Check:
```bash
# Check integration test coverage (must be ≥70%)
python -m pytest tests/integration/ --cov=src --cov-report=term-missing

# Run all collection architecture tests
python -m pytest tests/unit/test_collection_manager.py tests/unit/test_tools_collections.py tests/integration/test_collection_integration.py

# Full test suite
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Field Name-First Interface

### **CRITICAL: Always Use Field Names**
- **PREFERRED**: Use field names directly: `{"field": "6FN Next Date/Time"}`
- **ALTERNATIVE**: Use explicit field IDs: `{"field_id": "239"}`
- **DISCOURAGED**: Legacy format: `{"field": "custom_fields.239"}`

### Field Name Guidelines:
1. **Always start with `get_contact_schema()`** to see available field names
2. **Use human-readable field names** for filters and operations
3. **Field names are automatically resolved** to field IDs internally
4. **Schema shows usage patterns** for each field (preferred, explicit_id, legacy)

### Custom Field Examples:
```python
# ✅ PREFERRED: Field name
{"field": "6FN Next Date/Time", "operator": "equals", "value": "..."}

# ✅ ALTERNATIVE: Explicit field ID
{"field_id": "239", "operator": "equals", "value": "..."}

# ⚠️ DISCOURAGED: Legacy format
{"field": "custom_fields.239", "operator": "equals", "value": "..."}
```

## Notes

- **Collection-based architecture** is the current production approach
- **Field name-first interface** is the primary way to interact with custom fields
- **Legacy tool architecture** exists but is deprecated
- **Performance optimization** through lazy loading and caching
- **Comprehensive error handling** at all levels
- **API rate limiting and diagnostics** built-in

---

**REMINDER: Integration test coverage ≥70% is MANDATORY for all releases**
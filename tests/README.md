# Keap MCP Server - Tests Directory

This directory contains test scripts and utilities for the Keap MCP Server.

## Contents

- **Unit Tests**: Files prefixed with `test_` contain formal unit tests
- **Debug Scripts**: Files prefixed with `debug_` are for debugging specific issues
- **Search Scripts**: Files prefixed with `search_` demonstrate search functionality
- **List Scripts**: Files prefixed with `list_` are for listing various entities
- **Find Scripts**: Files prefixed with `find_` are for finding specific data
- **Check Scripts**: Files prefixed with `check_` verify various system components
- **Create Scripts**: Files prefixed with `create_` are for creating test entities
- **Utility Scripts**: Other scripts provide various utilities for testing and development

## Usage

Most scripts can be run directly from the command line:

```bash
cd /path/to/keapmcp
python -m tests.test_script_name
```

Or from the tests directory:

```bash
cd /path/to/keapmcp/tests
python test_script_name.py
```

## Test Schema API

To test the schema-based API:

```bash
python -m tests.test_schema_api
```

This will test the introspection endpoints and the schema validation.

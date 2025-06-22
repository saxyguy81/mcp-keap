"""
Keap MCP Server

Main entry point for the Model Context Protocol (MCP) server
for interacting with Keap CRM.
"""

import logging
import json
from typing import Optional, List, Dict, Any, Union

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def _parse_json_parameter(value: Union[str, List, Dict], expected_type: str = "list") -> Union[List, Dict]:
    """Parse JSON string parameter for MCP compatibility.
    
    Args:
        value: Parameter value (JSON string or already parsed)
        expected_type: Expected type ("list" or "dict")
        
    Returns:
        Parsed parameter
        
    Raises:
        ValueError: If parsing fails or type is incorrect
    """
    if isinstance(value, str):
        try:
            import json
            parsed = json.loads(value)
            if expected_type == "list" and not isinstance(parsed, list):
                raise ValueError(f"Expected list, got {type(parsed).__name__}")
            elif expected_type == "dict" and not isinstance(parsed, dict):
                raise ValueError(f"Expected dict, got {type(parsed).__name__}")
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    elif expected_type == "list" and isinstance(value, list):
        return value
    elif expected_type == "dict" and isinstance(value, dict):
        return value
    else:
        raise ValueError(f"Expected {expected_type} or JSON string, got {type(value).__name__}")


class KeapMCPServer:
    """
    Keap MCP Server implementation
    """

    def __init__(self, name: str = "keap-mcp-server"):
        """Initialize the MCP server

        Args:
            name: Server name
        """
        self.name = name
        self.version = "1.0.0"
        self.mcp = FastMCP(name)
        self._register_tools()
        self._register_resources()

    def _register_tools(self):
        """Register the 14 streamlined collection-based MCP tools.
        
        Tools Summary:
        - Core Contact Operations (2): list_contacts, get_contact_schema  
        - Collection Operations (4): union, intersect, diff, create_from_ids
        - Collection Data Access (3): get_collection_details, get_collection_fields, set_collection_fields
        - Tag Operations (2): get_tags, modify_collection_tags
        - Field Operations (1): modify_contact_fields
        - Contact Deletion Operations (1): delete_collection_contacts
        - System Operations (1): get_api_diagnostics
        
        Features:
        - JSON string and Python list filter support
        - Default 1000 contact limit (API maximum)
        - Comprehensive field selection
        - Collection-based operations for performance
        """

        # Core Contact Operations (2 tools)
        @self.mcp.tool()
        async def list_contacts(
            filters: Optional[Union[str, List[Dict[str, Any]]]] = None,
            limit: int = 1000,
            offset: int = 0,
            order_by: Optional[str] = None,
            order_direction: str = "ASC",
        ):
            """Universal contact search with comprehensive filters, returns collection ID.
            
            This is the primary contact search tool that replaces search_contacts_by_email,
            search_contacts_by_name, query_contacts_by_custom_field, etc.
            
            Args:
                filters: List of filter conditions or JSON string. Accepts both formats:
                    - Python list: [{"field": "given_name", "operator": "equals", "value": "Scott"}]
                    - JSON string: '[{"field": "given_name", "operator": "equals", "value": "Scott"}]'
                limit: Maximum contacts to return (default: 1000, API maximum)
                offset: Number of contacts to skip (default: 0)
                order_by: Field to sort by (optional)
                order_direction: Sort direction - "ASC" or "DESC" (default: "ASC")
            
            Returns:
                Dictionary with collection_id and count of contacts found
            
            Example filters (both formats supported):
                [{"field": "email", "operator": "contains", "value": "@company.com"}]
                [{"field": "given_name", "operator": "equals", "value": "John"}]
                [{"field": "family_name", "operator": "contains", "value": "Smith"}]
                [{"field": "custom_field_7", "operator": "equals", "value": "VIP"}]
                [{"field": "tags", "operator": "contains", "value": "customer"}]
                
            JSON string format (MCP client compatibility):
                '[{"field": "given_name", "operator": "equals", "value": "Scott"}]'
                
            Multiple filters (AND logic):
                [{"field": "given_name", "operator": "equals", "value": "John"},
                 {"field": "email", "operator": "contains", "value": "@company.com"}]
            """
            from src.mcp.tools_collections import list_contacts as _list_contacts
            from mcp.server.fastmcp import Context

            context = Context()
            return await _list_contacts(context, filters, limit, offset, order_by, order_direction)

        @self.mcp.tool()
        async def get_contact_schema():
            """Get available fields, custom fields, and filter examples.
            
            Returns comprehensive schema information to help construct filters
            for the list_contacts function.
            """
            from src.mcp.tools_collections import get_contact_schema as _get_schema
            from mcp.server.fastmcp import Context

            context = Context()
            return await _get_schema(context)

        # Collection Operations (4 tools)
        @self.mcp.tool()
        async def collection_union(collection_names: Union[str, List[str]]):
            """Combine multiple collections (A ∪ B ∪ C...).
            
            Args:
                collection_names: List of collection IDs to combine (or JSON string)
            """
            from src.mcp.tools_collections import collection_union as _union
            from mcp.server.fastmcp import Context

            # Parse collection_names if it's a JSON string
            collection_names = _parse_json_parameter(collection_names, "list")

            context = Context()
            return await _union(context, collection_names)

        @self.mcp.tool()
        async def collection_intersect(collection_names: Union[str, List[str]]):
            """Find contacts present in all collections (A ∩ B ∩ C...).
            
            Args:
                collection_names: List of collection IDs to intersect (or JSON string)
            """
            from src.mcp.tools_collections import collection_intersect as _intersect
            from mcp.server.fastmcp import Context

            # Parse collection_names if it's a JSON string
            collection_names = _parse_json_parameter(collection_names, "list")

            context = Context()
            return await _intersect(context, collection_names)

        @self.mcp.tool()
        async def collection_diff(base_collection: str, subtract_collections: Union[str, List[str]]):
            """Find contacts in base but not in any subtract collections (A - B - C...).
            
            Args:
                base_collection: Base collection ID
                subtract_collections: List of collection IDs to subtract (or JSON string)
            """
            from src.mcp.tools_collections import collection_diff as _diff
            from mcp.server.fastmcp import Context

            # Parse subtract_collections if it's a JSON string
            subtract_collections = _parse_json_parameter(subtract_collections, "list")

            context = Context()
            return await _diff(context, base_collection, subtract_collections)

        @self.mcp.tool()
        async def create_collection_from_ids(contact_ids: Union[str, List[Union[int, str]]], name: Optional[str] = None):
            """Create a collection from a list of contact IDs.
            
            This allows you to create collections from specific contact IDs,
            then use other collection-based tools to operate on those contacts.
            
            Args:
                contact_ids: List of contact IDs to include in collection (or JSON string)
                name: Optional name for the collection (auto-generated if not provided)
            """
            from src.mcp.tools_collections import create_collection_from_ids as _create_from_ids
            from mcp.server.fastmcp import Context

            # Parse contact_ids if it's a JSON string
            contact_ids = _parse_json_parameter(contact_ids, "list")

            context = Context()
            return await _create_from_ids(context, contact_ids, name)

        @self.mcp.tool()
        async def get_collection_details(collection_id: str, fields: Optional[Union[str, List[str]]] = None, count_only: bool = False, limit: Optional[int] = None):
            """Fetch contact data with comprehensive field selection from collection.
            
            This consolidated function replaces collection_count and get_collection_ids.
            Supports flexible field selection for efficient data retrieval.
            
            Args:
                collection_id: Collection identifier returned from list_contacts
                fields: List of fields to include. Options:
                    - None: Return all available fields (default)
                    - ["id"]: Return only contact IDs (most efficient)
                    - Standard fields: ["given_name", "family_name", "email", "email_addresses", "company", "phone1", "city", "state"]
                    - Custom fields: ["custom_field_7", "6FN Next Date/Time"] (use field names or IDs)
                    - Mixed: ["id", "given_name", "email_addresses", "custom_field_7"]
                count_only: If True, return only count information (fastest)
                limit: Maximum contacts to return (None for all in collection)
            
            Returns:
                Dictionary with 'contacts' list, 'count', and optional 'metrics'
                
            Examples:
                # Get all data for first 10 contacts
                get_collection_details("contacts_abc123", limit=10)
                
                # Get only names and emails (efficient)
                get_collection_details("contacts_abc123", ["given_name", "family_name", "email_addresses"])
                
                # Get only contact IDs (most efficient)
                get_collection_details("contacts_abc123", ["id"])
                
                # Get count only (fastest)
                get_collection_details("contacts_abc123", count_only=True)
            """
            from src.mcp.tools_collections import get_collection_details as _get_details
            from mcp.server.fastmcp import Context

            # Parse fields if it's a JSON string (for MCP compatibility)
            if isinstance(fields, str):
                try:
                    import json
                    parsed_fields = json.loads(fields)
                    if isinstance(parsed_fields, list):
                        fields = parsed_fields
                    else:
                        raise ValueError(f"Fields must be a list, got {type(parsed_fields).__name__}")
                except json.JSONDecodeError:
                    # Assume it's a single field name
                    fields = [fields]

            context = Context()
            return await _get_details(context, collection_id, fields, limit, count_only)

        # Tag Operations (2 tools)
        @self.mcp.tool()
        async def get_tags(
            filters: Optional[Union[str, List[Dict[str, Any]]]] = None,
            category_id: Optional[int] = None, 
            limit: int = 1000
        ):
            """List available tags with optional filtering (like list_contacts).
            
            Args:
                filters: List of filter objects for tag name, category, id, etc. (or JSON string)
                    Supported fields:
                    - "name" or "tag_name": Tag name
                    - "id": Tag ID
                    - "category_id": Category ID
                    - "category_name": Category name (when available)
                    
                    Examples:
                    - [{"field": "name", "operator": "contains", "value": "customer"}]
                    - [{"field": "tag_name", "operator": "equals", "value": "VIP Customer"}]
                    - [{"field": "category_name", "operator": "contains", "value": "sales"}]
                    - [{"field": "category_id", "operator": "equals", "value": 123}]
                    - [{"field": "id", "operator": "in", "value": [1, 2, 3]}]
                category_id: Optional category filter (deprecated, use filters instead)
                limit: Maximum number of tags (increased from 200 to 1000 for consistency)
            """
            from src.mcp.tools_collections import get_tags as _get_tags
            from mcp.server.fastmcp import Context

            # Parse filters if it's a JSON string (for MCP compatibility)
            if isinstance(filters, str):
                try:
                    import json
                    parsed_filters = json.loads(filters)
                    if isinstance(parsed_filters, list):
                        filters = parsed_filters
                    else:
                        raise ValueError(f"Filters must be a list, got {type(parsed_filters).__name__}")
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON format for filters")

            context = Context()
            return await _get_tags(context, filters, category_id, limit)

        @self.mcp.tool()
        async def modify_collection_tags(collection_id: str, tag_ids: Union[str, List[int]], operation: str = "add"):
            """Bulk tag operations on contact collections.
            
            Args:
                collection_id: Collection identifier
                tag_ids: List of tag IDs to apply/remove (or JSON string)
                operation: "add" or "remove"
            """
            from src.mcp.tools_collections import modify_collection_tags as _modify_tags
            from mcp.server.fastmcp import Context

            # Parse tag_ids if it's a JSON string
            tag_ids = _parse_json_parameter(tag_ids, "list")

            context = Context()
            return await _modify_tags(context, collection_id, tag_ids, operation)

        # Field Management Operations (3 tools)
        @self.mcp.tool()
        async def get_collection_fields(collection_id: str, field_names: Union[str, List[str]]):
            """Get specific field values from all contacts in a collection.
            
            Args:
                collection_id: Collection identifier
                field_names: List of field names to retrieve (or JSON string)
            """
            from src.mcp.tools_collections import get_collection_fields as _get_fields
            
            # Parse field_names if it's a JSON string (for MCP compatibility)
            if isinstance(field_names, str):
                try:
                    import json
                    parsed_fields = json.loads(field_names)
                    if isinstance(parsed_fields, list):
                        field_names = parsed_fields
                    else:
                        raise ValueError(f"Field names must be a list, got {type(parsed_fields).__name__}")
                except json.JSONDecodeError:
                    # Assume it's a single field name
                    field_names = [field_names]
            
            return await _get_fields(collection_id, field_names)

        @self.mcp.tool()
        async def set_collection_fields(collection_id: str, field_updates: Union[str, Dict[str, Any]]):
            """Set field values across all contacts in a collection.
            
            Args:
                collection_id: Collection identifier
                field_updates: Dict of field_name -> value pairs (or JSON string)
            """
            from src.mcp.tools_collections import set_collection_fields as _set_fields
            
            # Parse field_updates if it's a JSON string
            field_updates = _parse_json_parameter(field_updates, "dict")
            
            return await _set_fields(collection_id, field_updates)

        @self.mcp.tool()
        async def modify_contact_fields(collection_id: str, field_name: str, contact_values: Union[str, Dict[str, Any]]):
            """Modify specific field values for specific contacts in a collection.
            
            Args:
                collection_id: Collection identifier
                field_name: Name of the field to modify
                contact_values: Dict of contact_id -> value mappings (or JSON string)
            """
            from src.mcp.tools_collections import modify_contact_fields as _modify_fields
            from mcp.server.fastmcp import Context

            # Parse contact_values if it's a JSON string
            contact_values = _parse_json_parameter(contact_values, "dict")

            context = Context()
            return await _modify_fields(context, collection_id, field_name, contact_values)

        # Contact Deletion Operations (1 tool)
        @self.mcp.tool()
        async def delete_collection_contacts(
            collection_id: str, 
            confirm_deletion: bool = False, 
            dry_run: bool = True, 
            return_metrics: bool = False
        ):
            """Delete all contacts in a specific collection.
            
            WARNING: This is a destructive operation that permanently deletes contacts.
            Use with extreme caution and always test with dry_run=True first.
            
            Args:
                collection_id: Collection identifier from list_contacts()
                confirm_deletion: Must be True to actually delete contacts (safety check)
                dry_run: If True, only shows what would be deleted without actually deleting
                return_metrics: Include performance metrics in response
                
            Examples:
                # Preview what would be deleted (safe)
                delete_collection_contacts("contacts_abc123", dry_run=True)
                
                # Actually delete all contacts (dangerous!)
                delete_collection_contacts("contacts_abc123", confirm_deletion=True, dry_run=False)
            """
            from src.mcp.tools_collections import delete_collection_contacts as _delete_contacts
            from mcp.server.fastmcp import Context

            context = Context()
            return await _delete_contacts(context, collection_id, confirm_deletion, dry_run, return_metrics)

        # System Operations (1 tool)
        @self.mcp.tool()
        async def get_api_diagnostics():
            """Get comprehensive API diagnostics and performance metrics."""
            from src.mcp.tools_collections import get_api_diagnostics as _diag
            from mcp.server.fastmcp import Context

            context = Context()
            return await _diag(context)

    def _register_resources(self):
        """Register MCP resources"""

        @self.mcp.resource("keap://schema")
        async def get_keap_schema() -> str:
            """
            Get the Keap API schema information.

            Returns:
                JSON string with schema info
            """
            schema = {
                "contacts": {
                    "fields": {
                        "id": {"type": "integer", "description": "Contact ID"},
                        "first_name": {
                            "type": "string",
                            "description": "First name (given name)",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Last name (family name)",
                        },
                        "email": {
                            "type": "string",
                            "description": "Primary email address",
                        },
                        "date_created": {
                            "type": "string",
                            "format": "date-time",
                            "description": "When the contact was created",
                        },
                        "date_updated": {
                            "type": "string",
                            "format": "date-time",
                            "description": "When the contact was last updated",
                        },
                        "tag": {"type": "tag", "description": "Tag filter"},
                        "tag_applied": {
                            "type": "tag_date",
                            "description": "Tag application date filter",
                        },
                        "custom_field": {
                            "type": "custom",
                            "description": "Custom field filter",
                        },
                    },
                    "operators": {
                        "string": [
                            "=",
                            "!=",
                            "pattern",
                            "starts_with",
                            "ends_with",
                            "contains",
                            "in",
                        ],
                        "numeric": ["=", "!=", "<", "<=", ">", ">=", "in", "between"],
                        "date": [
                            "=",
                            "!=",
                            "<",
                            "<=",
                            ">",
                            ">=",
                            "between",
                            "before",
                            "after",
                            "on",
                        ],
                        "logical": ["AND", "OR", "NOT"],
                    },
                },
                "tags": {
                    "fields": {
                        "id": {"type": "integer", "description": "Tag ID"},
                        "name": {"type": "string", "description": "Tag name"},
                        "category_id": {
                            "type": "integer",
                            "description": "Category ID",
                        },
                        "category_name": {
                            "type": "string",
                            "description": "Category name",
                        },
                    }
                },
                "filter_examples": [
                    {"field": "first_name", "operator": "pattern", "value": "John*"},
                    {"field": "last_name", "operator": "pattern", "value": "Smith*"},
                    {"field": "email", "operator": "pattern", "value": "*@example.com"},
                    {"field": "id", "operator": "in", "value": [123, 456, 789]},
                    {
                        "field": "date_created",
                        "operator": ">=",
                        "value": "2023-01-01T00:00:00Z",
                    },
                    {
                        "field": "date_created",
                        "operator": "<=",
                        "value": "2023-12-31T23:59:59Z",
                    },
                    {
                        "operator": "OR",
                        "conditions": [
                            {
                                "field": "first_name",
                                "operator": "pattern",
                                "value": "Matt*",
                            },
                            {
                                "field": "first_name",
                                "operator": "pattern",
                                "value": "David*",
                            },
                        ],
                    },
                    {
                        "field": "tag",
                        "operator": "expression",
                        "value": {
                            "operator": "AND",
                            "conditions": [
                                {"tag_id": 123},
                                {
                                    "operator": "OR",
                                    "conditions": [
                                        {"tag_id": 456},
                                        {
                                            "operator": "NOT",
                                            "conditions": [{"tag_id": 789}],
                                        },
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        "field": "tag_applied",
                        "operator": "before",
                        "value": {"tag_id": 123, "value": "2023-06-01T00:00:00Z"},
                    },
                    {
                        "field": "custom_field",
                        "operator": "pattern",
                        "value": {"id": 1, "value": "New*Customer"},
                    },
                ],
            }

            return json.dumps(schema, indent=2)

        @self.mcp.resource("keap://capabilities")
        async def get_keap_capabilities() -> str:
            """
            Get the Keap MCP server capabilities.

            Returns:
                JSON string with capabilities info
            """
            capabilities = {
                "name": "Keap MCP Server",
                "version": "2.0.0",
                "description": "MCP server for interacting with Keap CRM data",
                "functions": [
                    {
                        "name": "query_contacts",
                        "description": "Query contacts with advanced filtering",
                    },
                    {
                        "name": "get_contact_details",
                        "description": "Get detailed information for specific contacts",
                    },
                    {
                        "name": "query_tags",
                        "description": "Query for tags with filtering",
                    },
                    {
                        "name": "get_tag_details",
                        "description": "Get detailed information for specific tags",
                    },
                    {
                        "name": "modify_tags",
                        "description": "Add or remove tags from contacts",
                    },
                    {
                        "name": "intersect_id_lists",
                        "description": "Find IDs that appear in multiple lists (generic intersection)",
                    },
                ],
                "filter_capabilities": {
                    "unified_filter_structure": True,
                    "logical_operators": ["AND", "OR", "NOT"],
                    "nested_conditions": True,
                    "pattern_matching": True,
                    "tag_expressions": True,
                    "custom_field_filtering": True,
                    "multi_field_sorting": True,
                },
            }

            return json.dumps(capabilities, indent=2)

    def list_tools(self):
        """List all registered tools"""
        # FastMCP uses get_tools() instead of list_tools()
        try:
            return list(self.mcp.get_tools().keys())
        except AttributeError:
            # Fallback - return the new streamlined tool set
            return [
                # Core Contact Operations (2 tools)
                "list_contacts",
                "get_contact_schema",
                # Collection Operations (4 tools)
                "collection_union",
                "collection_intersect", 
                "collection_diff",
                "collection_count",
                # Collection Data Access (2 tools)
                "get_collection_details",
                "get_collection_ids",
                # Tag Operations (2 tools)
                "get_tags",
                "apply_tags_to_collection",
                # System Operations (1 tool)
                "get_api_diagnostics",
            ]

    def run(self, host: str = "127.0.0.1", port: int = 5000):
        """Run the MCP server

        Args:
            host: Host to bind (ignored for stdio mode)
            port: Port to listen on (ignored for stdio mode)
        """
        # For Claude Desktop, run in stdio mode
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.mcp.run_stdio_async())

    async def run_async(self, host: str = "127.0.0.1", port: int = 5000):
        """Run the MCP server asynchronously for tests

        Args:
            host: Host to bind
            port: Port to listen on
        """
        logger.info(f"Starting Keap MCP Server asynchronously on {host}:{port}")
        await self.mcp.run_sse_async(host=host, port=port)

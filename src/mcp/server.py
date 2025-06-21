"""
Keap MCP Server

Main entry point for the Model Context Protocol (MCP) server
for interacting with Keap CRM.
"""

import logging
import json

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


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
        """Register collection-based MCP tools with proper decorators"""

        # Core Contact Operations (2 tools)
        @self.mcp.tool()
        async def list_contacts(
            filters=None,
            limit: int = 200,
            offset: int = 0,
            order_by=None,
            order_direction: str = "ASC",
        ):
            """Universal contact search with comprehensive filters, returns collection ID.
            
            This is the primary contact search tool that replaces search_contacts_by_email,
            search_contacts_by_name, query_contacts_by_custom_field, etc.
            
            Example filters:
                [{"field": "email", "operator": "contains", "value": "@company.com"}]
                [{"field": "given_name", "operator": "equals", "value": "John"}]
                [{"field": "custom_field_7", "operator": "equals", "value": "VIP"}]
                [{"field": "tags", "operator": "contains", "value": "customer"}]
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
        async def collection_union(collection_a: str, collection_b: str):
            """Combine two collections (A ∪ B).
            
            Args:
                collection_a: First collection ID
                collection_b: Second collection ID
            """
            from src.mcp.tools_collections import collection_union as _union
            from mcp.server.fastmcp import Context

            context = Context()
            return await _union(context, collection_a, collection_b)

        @self.mcp.tool()
        async def collection_intersect(collection_a: str, collection_b: str):
            """Find contacts in both collections (A ∩ B).
            
            Args:
                collection_a: First collection ID
                collection_b: Second collection ID
            """
            from src.mcp.tools_collections import collection_intersect as _intersect
            from mcp.server.fastmcp import Context

            context = Context()
            return await _intersect(context, collection_a, collection_b)

        @self.mcp.tool()
        async def collection_diff(collection_a: str, collection_b: str):
            """Find contacts in first but not second collection (A - B).
            
            Args:
                collection_a: First collection ID
                collection_b: Second collection ID
            """
            from src.mcp.tools_collections import collection_diff as _diff
            from mcp.server.fastmcp import Context

            context = Context()
            return await _diff(context, collection_a, collection_b)

        @self.mcp.tool()
        async def collection_count(collection_id: str):
            """Get collection size without fetching data.
            
            Args:
                collection_id: Collection identifier
            """
            from src.mcp.tools_collections import collection_count as _count
            from mcp.server.fastmcp import Context

            context = Context()
            return await _count(context, collection_id)

        # Collection Data Access (2 tools)
        @self.mcp.tool()
        async def get_collection_details(collection_id: str, fields=None):
            """Fetch contact data with field selection from collection.
            
            Args:
                collection_id: Collection identifier
                fields: List of fields to include (None for all fields)
            """
            from src.mcp.tools_collections import get_collection_details as _get_details
            from mcp.server.fastmcp import Context

            context = Context()
            return await _get_details(context, collection_id, fields)

        @self.mcp.tool()
        async def get_collection_ids(collection_id: str):
            """Get raw contact ID list from collection.
            
            Args:
                collection_id: Collection identifier
            """
            from src.mcp.tools_collections import get_collection_ids as _get_ids
            from mcp.server.fastmcp import Context

            context = Context()
            return await _get_ids(context, collection_id)

        # Tag Operations (2 tools)
        @self.mcp.tool()
        async def get_tags(category_id=None, limit: int = 200):
            """List available tags with optional filtering.
            
            Args:
                category_id: Optional category filter
                limit: Maximum number of tags
            """
            from src.mcp.tools_collections import get_tags as _get_tags
            from mcp.server.fastmcp import Context

            context = Context()
            return await _get_tags(context, category_id, limit)

        @self.mcp.tool()
        async def apply_tags_to_collection(collection_id: str, tag_ids, operation: str = "add"):
            """Bulk tag operations on contact collections.
            
            Args:
                collection_id: Collection identifier
                tag_ids: List of tag IDs to apply/remove
                operation: "add" or "remove"
            """
            from src.mcp.tools_collections import apply_tags_to_collection as _apply_tags
            from mcp.server.fastmcp import Context

            context = Context()
            return await _apply_tags(context, collection_id, tag_ids, operation)

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

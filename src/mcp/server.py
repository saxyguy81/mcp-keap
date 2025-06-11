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
        """Register MCP tools with proper decorators"""

        @self.mcp.tool()
        async def list_contacts(
            filters=None,
            limit: int = 200,
            offset: int = 0,
            order_by=None,
            order_direction: str = "ASC",
            include=None,
        ):
            """List contacts with optional filtering and pagination.

            This function now uses the optimized query engine for better performance.
            For advanced features like performance metrics, use query_contacts_optimized directly.
            """
            # Import here to avoid circular imports
            from src.mcp.tools import query_contacts_optimized
            from mcp.server.fastmcp import Context

            # Create a context - for now, use a basic one
            context = Context()

            # Use the optimized query function internally but maintain the simple interface
            result = await query_contacts_optimized(
                context=context,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_direction=order_direction,
                include=include,
                enable_optimization=True,
                return_metrics=False,
            )

            # Return just the contacts list for backward compatibility
            return result["contacts"]

        @self.mcp.tool()
        async def search_contacts_by_email(email: str):
            """Search for contacts by email address."""
            from src.mcp.tools import search_contacts_by_email as _search
            from mcp.server.fastmcp import Context

            context = Context()
            return await _search(context, email)

        @self.mcp.tool()
        async def search_contacts_by_name(name: str, limit: int = 50):
            """Search for contacts by name."""
            from src.mcp.tools import search_contacts_by_name as _search
            from mcp.server.fastmcp import Context

            context = Context()
            return await _search(context, name, limit)

        @self.mcp.tool()
        async def get_tags(category_id=None, limit: int = 200):
            """Get available tags, optionally filtered by category."""
            from src.mcp.tools import get_tags as _get_tags
            from mcp.server.fastmcp import Context

            context = Context()
            return await _get_tags(context, category_id, limit)

        @self.mcp.tool()
        async def get_contacts_with_tag(tag_id: int, limit: int = 200):
            """Get contacts that have a specific tag."""
            from src.mcp.tools import get_contacts_with_tag as _get
            from mcp.server.fastmcp import Context

            context = Context()
            return await _get(context, tag_id, limit)

        @self.mcp.tool()
        async def set_custom_field_values(contact_id: int, field_values):
            """Set custom field values for a contact."""
            from src.mcp.tools import set_custom_field_values as _set
            from mcp.server.fastmcp import Context

            context = Context()
            return await _set(context, contact_id, field_values)

        @self.mcp.tool()
        async def get_api_diagnostics():
            """Get API client diagnostics and health information."""
            from src.mcp.tools import get_api_diagnostics as _diag
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
            # Fallback - return a count based on what we registered
            return ["list_contacts", "search_contacts_by_email", "search_contacts_by_name", 
                   "get_tags", "get_contacts_with_tag", "set_custom_field_values", "get_api_diagnostics"]

    def run(self, host: str = "127.0.0.1", port: int = 5000):
        """Run the MCP server

        Args:
            host: Host to bind
            port: Port to listen on
        """
        logger.info(f"Starting Keap MCP Server on {host}:{port}")
        # Use SSE transport for HTTP server
        import asyncio

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_async(host, port))

    async def run_async(self, host: str = "127.0.0.1", port: int = 5000):
        """Run the MCP server asynchronously for tests

        Args:
            host: Host to bind
            port: Port to listen on
        """
        logger.info(f"Starting Keap MCP Server asynchronously on {host}:{port}")
        await self.mcp.run_sse_async(host=host, port=port)

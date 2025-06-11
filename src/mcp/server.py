"""
Keap MCP Server

Main entry point for the Model Context Protocol (MCP) server
for interacting with Keap CRM.
"""

import logging
import json

from fastmcp import FastMCP

from src.mcp.tools import (
    list_contacts,
    search_contacts_by_email,
    search_contacts_by_name,
    get_tags,
    get_contacts_with_tag,
    set_custom_field_values,
    get_api_diagnostics,
)

logger = logging.getLogger(__name__)


class KeapMCPServer:
    """
    Keap MCP Server implementation
    """

    def __init__(self, name: str = "keap-mcp"):
        """Initialize the MCP server

        Args:
            name: Server name
        """
        self.mcp = FastMCP(name)
        self._register_tools()
        self._register_resources()

    def _register_tools(self):
        """Register MCP tools"""
        # Register tools with the updated FastMCP API
        self.mcp.add_tool(list_contacts)
        self.mcp.add_tool(search_contacts_by_email)
        self.mcp.add_tool(search_contacts_by_name)
        self.mcp.add_tool(get_tags)
        self.mcp.add_tool(get_contacts_with_tag)
        self.mcp.add_tool(set_custom_field_values)
        self.mcp.add_tool(get_api_diagnostics)

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

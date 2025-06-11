
"""
Integration tests for the Keap MCP Server

These tests verify the end-to-end functionality of the MCP server
by making actual requests to it.
"""

import os
import sys
import asyncio
import logging
import pytest
import httpx
from pathlib import Path

# Load environment variables from .env file if it exists
from dotenv import load_dotenv

# Add parent directory to path to import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.mcp.server import KeapMCPServer

env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test MCP server host and port
MCP_HOST = "127.0.0.1"
MCP_PORT = 5123  # Using a different port for testing

@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def mcp_server(event_loop):
    """Start a test MCP server for the test session"""
    server = KeapMCPServer("keap-mcp-test")
    
    # Start the server in a separate task
    server_task = event_loop.create_task(
        server.run_async(host=MCP_HOST, port=MCP_PORT)
    )
    
    # Give it a moment to start
    await asyncio.sleep(1)
    
    yield server
    
    # Shutdown the server after tests
    server_task.cancel()
    
    try:
        await server_task
    except asyncio.CancelledError:
        pass

@pytest.fixture
async def mcp_client():
    """Create an HTTP client for interacting with the MCP server"""
    async with httpx.AsyncClient() as client:
        yield client

async def test_get_keap_schema(mcp_client):
    """Test retrieving the Keap API schema"""
    response = await mcp_client.get(f"http://{MCP_HOST}:{MCP_PORT}/resource/keap://schema")
    assert response.status_code == 200
    
    schema = response.json()
    assert "contacts" in schema
    assert "tags" in schema
    assert "filter_examples" in schema

async def test_get_keap_capabilities(mcp_client):
    """Test retrieving the Keap MCP server capabilities"""
    response = await mcp_client.get(f"http://{MCP_HOST}:{MCP_PORT}/resource/keap://capabilities")
    assert response.status_code == 200
    
    capabilities = response.json()
    assert "name" in capabilities
    assert "functions" in capabilities
    assert "filter_capabilities" in capabilities

async def test_query_contacts_by_name(mcp_client):
    """Test querying contacts by name pattern"""
    query = {
        "filters": [
            {"field": "first_name", "operator": "pattern", "value": "John*"}
        ],
        "max_results": 10
    }
    
    response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_contacts",
        json=query
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "contact_ids" in result
    assert "total_count" in result
    assert "metadata" in result

async def test_query_contacts_with_tag_filter(mcp_client):
    """Test querying contacts with tag filter"""
    # First, get some valid tag IDs
    tag_query = {
        "max_results": 5
    }
    
    tag_response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_tags",
        json=tag_query
    )
    assert tag_response.status_code == 200
    
    tag_result = tag_response.json()
    if not tag_result.get("tag_ids"):
        pytest.skip("No tags found for testing")
    
    # Use first tag for filtering contacts
    tag_id = tag_result["tag_ids"][0]
    
    # Query contacts with this tag
    query = {
        "filters": [
            {"field": "tag", "operator": "=", "value": tag_id}
        ],
        "max_results": 10
    }
    
    response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_contacts",
        json=query
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "contact_ids" in result
    assert "total_count" in result
    assert "metadata" in result

async def test_get_contact_details(mcp_client):
    """Test retrieving contact details"""
    # First, query some contacts
    query = {
        "filters": [],
        "max_results": 3
    }
    
    query_response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_contacts",
        json=query
    )
    assert query_response.status_code == 200
    
    query_result = query_response.json()
    if not query_result.get("contact_ids"):
        pytest.skip("No contacts found for testing")
    
    # Get details for these contacts
    details_query = {
        "contact_ids": query_result["contact_ids"],
        "include": {
            "basic_info": True,
            "dates": True,
            "tags": {"enabled": True, "include_names": True},
            "custom_fields": {"enabled": True}
        }
    }
    
    response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/get_contact_details",
        json=details_query
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "contacts" in result
    assert len(result["contacts"]) == len(query_result["contact_ids"])
    
    # Check that the contact structure is correct
    for contact in result["contacts"]:
        assert "id" in contact
        assert "basic_info" in contact
        assert "dates" in contact
        assert "tags" in contact
        
        # Check basic info
        assert "first_name" in contact["basic_info"]
        assert "last_name" in contact["basic_info"]
        assert "email" in contact["basic_info"]
        
        # Check dates
        assert "created" in contact["dates"]
        assert "updated" in contact["dates"]

async def test_negative_tag_filtering(mcp_client):
    """Test negative tag filtering (contacts without specific tags)"""
    # First, get some valid tag IDs
    tag_query = {
        "max_results": 5
    }
    
    tag_response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_tags",
        json=tag_query
    )
    assert tag_response.status_code == 200
    
    tag_result = tag_response.json()
    if not tag_result.get("tag_ids") or len(tag_result["tag_ids"]) < 2:
        pytest.skip("Not enough tags found for testing")
    
    # Use first tag for positive filtering
    positive_tag_id = tag_result["tag_ids"][0]
    
    # Use second tag for negative filtering
    negative_tag_id = tag_result["tag_ids"][1]
    
    # Query contacts that have the positive tag but not the negative tag
    query = {
        "filters": [
            {"field": "tag", "operator": "=", "value": positive_tag_id},
            {"field": "tag", "operator": "!=", "value": negative_tag_id}
        ],
        "max_results": 10
    }
    
    response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_contacts",
        json=query
    )
    assert response.status_code == 200
    
    result = response.json()
    
    # Now verify that none of the returned contacts have the negative tag
    if result.get("contact_ids"):
        details_query = {
            "contact_ids": result["contact_ids"],
            "include": {
                "basic_info": True,
                "tags": {"enabled": True, "include_names": True}
            }
        }
        
        details_response = await mcp_client.post(
            f"http://{MCP_HOST}:{MCP_PORT}/get_contact_details",
            json=details_query
        )
        assert details_response.status_code == 200
        
        details_result = details_response.json()
        
        # Check that none of the contacts have the negative tag
        for contact in details_result.get("contacts", []):
            contact_tag_ids = [tag["id"] for tag in contact.get("tags", [])]
            assert negative_tag_id not in contact_tag_ids
            assert positive_tag_id in contact_tag_ids

async def test_custom_field_filtering(mcp_client):
    """Test custom field filtering"""
    # First, query some contacts with custom fields to find a valid custom field ID
    query = {
        "filters": [],
        "max_results": 10
    }
    
    query_response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_contacts",
        json=query
    )
    assert query_response.status_code == 200
    
    query_result = query_response.json()
    if not query_result.get("contact_ids"):
        pytest.skip("No contacts found for testing")
    
    # Get details for these contacts including custom fields
    details_query = {
        "contact_ids": query_result["contact_ids"],
        "include": {
            "custom_fields": {"enabled": True}
        }
    }
    
    details_response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/get_contact_details",
        json=details_query
    )
    assert details_response.status_code == 200
    
    details_result = details_response.json()
    
    # Find a contact with custom fields
    custom_field_id = None
    custom_field_value = None
    
    for contact in details_result.get("contacts", []):
        if contact.get("custom_fields") and len(contact["custom_fields"]) > 0:
            field_id = list(contact["custom_fields"].keys())[0]
            custom_field_id = int(field_id)
            custom_field_value = contact["custom_fields"][field_id]["value"]
            break
    
    if custom_field_id is None:
        pytest.skip("No custom fields found for testing")
    
    # Query contacts with this custom field
    query = {
        "filters": [
            {
                "field": "custom_field", 
                "operator": "=", 
                "value": {
                    "id": custom_field_id,
                    "value": custom_field_value
                }
            }
        ],
        "max_results": 10
    }
    
    response = await mcp_client.post(
        f"http://{MCP_HOST}:{MCP_PORT}/query_contacts",
        json=query
    )
    assert response.status_code == 200
    
    result = response.json()
    assert "contact_ids" in result
    assert "total_count" in result
    
    # At least one contact should match
    assert result["total_count"] > 0

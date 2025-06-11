#!/usr/bin/env python
"""
Simple test for MCP server
"""

import requests
import json

# Test the MCP endpoint with a simple request
response = requests.post(
    "http://localhost:5007/mcp",
    json={"function": "search_tags", "params": {"name": "Member"}},
)

print(f"Status code: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"Error: {response.text}")

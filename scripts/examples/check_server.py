#!/usr/bin/env python
"""
Check if the MCP server is running
"""

import requests

print('Checking server status...')
try:
    response = requests.get('http://localhost:5004/health', timeout=2)
    print(f'Server responded with status code: {response.status_code}')
    if response.status_code == 200:
        print('Server is running!')
        print(response.json())
    else:
        print('Server is not responding correctly.')
except Exception as e:
    print(f'Error connecting to server: {e}')
    print('The server may not be running or is not accessible.')

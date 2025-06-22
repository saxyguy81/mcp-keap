#!/usr/bin/env python3
"""
Verify MCP Configuration

This script helps verify that your MCP-Keap server is properly configured
for Claude Desktop integration.
"""

import json
import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("🔍 Checking .env file...")
    
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    required_vars = ['KEAP_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env file looks good!")
    return True

def check_claude_desktop_config():
    """Check Claude Desktop configuration paths"""
    print("\n🔍 Checking Claude Desktop configuration...")
    
    # Common paths for Claude Desktop config
    possible_paths = [
        Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",  # macOS
        Path(os.getenv('APPDATA', '')) / "Claude/claude_desktop_config.json",  # Windows
    ]
    
    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break
    
    if not config_path:
        print("⚠️  Claude Desktop config file not found at standard locations:")
        for path in possible_paths:
            print(f"   - {path}")
        print("\n📋 You may need to create the config file manually.")
        return False
    
    print(f"✅ Found Claude Desktop config at: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'mcpServers' not in config:
            print("⚠️  No mcpServers section found in config")
            return False
        
        keap_servers = [name for name in config['mcpServers'] if 'keap' in name.lower()]
        
        if not keap_servers:
            print("⚠️  No Keap MCP server found in configuration")
            return False
        
        print(f"✅ Found Keap MCP server(s): {', '.join(keap_servers)}")
        
        # Check the configuration details
        for server_name in keap_servers:
            server_config = config['mcpServers'][server_name]
            print(f"\n📋 {server_name} configuration:")
            print(f"   Command: {server_config.get('command', 'Not specified')}")
            print(f"   Args: {server_config.get('args', 'Not specified')}")
            
            env_config = server_config.get('env', {})
            if 'KEAP_API_KEY' in env_config:
                api_key = env_config['KEAP_API_KEY']
                masked_key = api_key[:8] + '*' * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else '*' * len(api_key)
                print(f"   API Key: {masked_key}")
            else:
                print("   ⚠️  No KEAP_API_KEY found in environment")
        
        return True
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in Claude Desktop config file")
        return False
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False

def test_server_import():
    """Test if the MCP server can be imported"""
    print("\n🔍 Testing server import...")
    
    try:
        # Add the project root to Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.mcp.server import KeapMCPServer
        print("✅ KeapMCPServer can be imported successfully")
        
        # Try to create a server instance
        server = KeapMCPServer()
        print("✅ KeapMCPServer instance created successfully")
        
        # Check number of tools
        tools = len(server.mcp._tools)
        print(f"✅ Server has {tools} MCP tools registered")
        
        if tools != 11:
            print(f"⚠️  Expected 11 tools, found {tools}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Server creation error: {e}")
        return False

def generate_config_template():
    """Generate a configuration template for Claude Desktop"""
    print("\n📋 Claude Desktop Configuration Template:")
    print("=" * 50)
    
    project_path = Path(__file__).parent.parent
    
    config_template = {
        "mcpServers": {
            "keap-mcp-server": {
                "command": "python3",
                "args": [str(project_path / "run.py")],
                "env": {
                    "KEAP_API_KEY": "your-keap-api-key-here",
                    "LOG_LEVEL": "INFO",
                    "LOG_FILE": str(project_path / "mcp-server.log")
                }
            }
        }
    }
    
    print(json.dumps(config_template, indent=2))
    print("=" * 50)

def main():
    """Main verification function"""
    print("🚀 MCP-Keap Configuration Verification")
    print("=" * 40)
    
    all_good = True
    
    # Check .env file
    if not check_env_file():
        all_good = False
    
    # Check Claude Desktop config
    if not check_claude_desktop_config():
        all_good = False
    
    # Test server import
    if not test_server_import():
        all_good = False
    
    # Generate config template
    generate_config_template()
    
    print("\n" + "=" * 40)
    if all_good:
        print("🎉 All checks passed! Your MCP-Keap server should be ready to use.")
    else:
        print("⚠️  Some issues found. Please review the output above.")
        print("\n💡 Next steps:")
        print("1. Ensure your .env file has a valid KEAP_API_KEY")
        print("2. Add the configuration template to your Claude Desktop config")
        print("3. Restart Claude Desktop")
        print("4. Test the connection in Claude")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
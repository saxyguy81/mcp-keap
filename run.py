#!/usr/bin/env python3
"""
Keap MCP Server Launcher

Provides a convenient way to start the Keap MCP server.
"""

import argparse
import logging
import os
import sys

# Load .env file first
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file")
except ImportError:
    print("Warning: python-dotenv not installed, cannot load .env file automatically")
    print("Environment variables must be set manually.")

from src.mcp.server import KeapMCPServer
from src.utils.logging_utils import setup_logging
from src.utils.config import Config

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Keap MCP Server")
    parser.add_argument("--host", type=str, help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to listen on")
    parser.add_argument("--log-level", type=str, 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    parser.add_argument("--log-file", type=str, help="Log file path")
    parser.add_argument("--no-console-log", action="store_true", 
                        help="Disable console logging")
    parser.add_argument("--env-file", type=str, help="Path to .env file")
    
    args = parser.parse_args()
    
    # Load configuration with environment file if provided
    config = Config(args.env_file)
    
    # Override config with command line arguments
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.log_level:
        config.log_level = args.log_level
    if args.log_file:
        config.log_file = args.log_file
    
    # Setup logging
    logger = setup_logging(
        log_level=config.get_log_level_int(),
        log_file=config.log_file,
        console=not args.no_console_log
    )
    
    # Log configuration
    logger.info("Starting Keap MCP Server with configuration:")
    for key, value in config.as_dict().items():
        logger.info(f"  {key}: {value}")
    
    # Create and run the server
    try:
        server = KeapMCPServer()
        server.run(host=config.host, port=config.port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

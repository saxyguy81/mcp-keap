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
except ImportError:
    pass

# Change to the script's directory to ensure relative imports work
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from src.mcp.server import KeapMCPServer


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup basic logging"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Setup handlers
    handlers = []

    # Only add file handler for MCP mode to avoid stdout interference
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        handlers.append(file_handler)

    # Configure root logger
    if handlers:
        logging.basicConfig(level=level, handlers=handlers, force=True)
    else:
        # Disable logging if no file handler
        logging.basicConfig(level=logging.CRITICAL, force=True)

    return logging.getLogger(__name__)


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Keap MCP Server")
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", "127.0.0.1"),
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", 5000)),
        help="Port to listen on",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument(
        "--log-file", type=str, default=os.getenv("LOG_FILE"), help="Log file path"
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(log_level=args.log_level, log_file=args.log_file)

    # Log configuration only to file, not console for MCP
    if args.log_file:
        logger.info("Starting Keap MCP Server with configuration:")
        logger.info(f"  host: {args.host}")
        logger.info(f"  port: {args.port}")
        logger.info(f"  log_level: {args.log_level}")
        logger.info(f"  log_file: {args.log_file}")

    # Create and run the server
    try:
        server = KeapMCPServer()
        server.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        if args.log_file:
            logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        if args.log_file:
            logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

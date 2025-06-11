
#!/usr/bin/env python3
"""
Keap MCP Server Test Runner

This script provides a simple way to run different tests for the Keap MCP server.
"""

import os
import sys
import argparse
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_api_validation():
    """Run the Keap API validation tests"""
    logger.info("Running Keap API validation tests...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "tests.validate_keap_api"],
            check=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"API validation tests failed with code {e.returncode}")
        return False

def run_integration_tests():
    """Run the MCP server integration tests"""
    logger.info("Running MCP server integration tests...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-xvs", "tests/integration"],
            check=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Integration tests failed with code {e.returncode}")
        return False

def run_unit_tests():
    """Run unit tests"""
    logger.info("Running unit tests...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-xvs", "tests/unit"],
            check=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Unit tests failed with code {e.returncode}")
        return False

def run_mcp_server():
    """Run the MCP server for manual testing"""
    logger.info("Starting the MCP server for manual testing...")
    
    try:
        result = subprocess.run(
            [sys.executable, "run.py"],
            check=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"MCP server failed with code {e.returncode}")
        return False
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Keap MCP Server Test Runner")
    
    parser.add_argument(
        "command",
        choices=["api", "integration", "unit", "all", "server"],
        help="Test command to run"
    )
    
    args = parser.parse_args()
    
    if args.command == "api":
        success = run_api_validation()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "unit":
        success = run_unit_tests()
    elif args.command == "server":
        success = run_mcp_server()
    elif args.command == "all":
        api_success = run_api_validation()
        unit_success = run_unit_tests()
        integration_success = run_integration_tests()
        
        success = api_success and unit_success and integration_success
        
        logger.info(f"API Validation: {'PASS' if api_success else 'FAIL'}")
        logger.info(f"Unit Tests: {'PASS' if unit_success else 'FAIL'}")
        logger.info(f"Integration Tests: {'PASS' if integration_success else 'FAIL'}")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

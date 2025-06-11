#!/usr/bin/env python3
"""
Script to run integration tests using the .env file configuration.

This script demonstrates how the integration tests now load the Keap API key
from the .env file automatically.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run integration tests with .env file support."""

    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ No .env file found!")
        print("Create a .env file with your Keap API key:")
        print("KEAP_API_KEY=your_api_key_here")
        return 1

    print("🔧 Running integration tests with .env file configuration...")
    print(f"📁 Found .env file at: {env_file.absolute()}")

    # Run a simple integration test to verify .env loading
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/test_cache_integration.py::TestCacheAPIIntegration::test_cache_with_real_api_calls",
        "-v",
        "--tb=short",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Integration test passed!")
            print("🎉 The .env file is working correctly with integration tests!")
            if "HTTP Request:" in result.stdout:
                print("🌐 Real API calls were made successfully")
        else:
            print("❌ Integration test failed:")
            print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            print("STDERR:", result.stderr[-500:])  # Last 500 chars

        return result.returncode

    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Setup script for Keap MCP service.
Provides installation, configuration, and maintenance utilities.
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List


def run_command(
    cmd: List[str], description: str, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command with error handling."""
    print(f"→ {description}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"  {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error: {e}")
        if e.stderr:
            print(f"  {e.stderr.strip()}")
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")

    if sys.version_info < (3, 10):
        print("  ✗ Python 3.10 or higher is required")
        print(f"  Current version: {sys.version}")
        sys.exit(1)

    print(
        f"  ✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )


def install_dependencies(dev: bool = False):
    """Install Python dependencies."""
    print("Installing dependencies...")

    # Upgrade pip first
    run_command(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip"
    )

    # Install core dependencies
    run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Installing core dependencies",
    )

    # Install development dependencies if requested
    if dev:
        run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"],
            "Installing development dependencies",
        )


def setup_environment():
    """Set up environment configuration."""
    print("Setting up environment configuration...")

    env_file = Path(".env")
    env_template = Path(".env.template")

    if not env_file.exists() and env_template.exists():
        print("  Creating .env file from template...")
        with open(env_template, "r") as template:
            content = template.read()

        with open(env_file, "w") as env:
            env.write(content)

        print("  ✓ Created .env file")
        print("  ⚠ Please update .env with your actual configuration values")
    elif env_file.exists():
        print("  ✓ .env file already exists")
    else:
        print("  ⚠ No .env.template found, skipping environment setup")


def create_directories():
    """Create necessary directories."""
    print("Creating directories...")

    directories = ["data", "logs", "config", "cache", "reports", "tests/load/reports"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")


def setup_git_hooks():
    """Set up Git pre-commit hooks."""
    print("Setting up Git hooks...")

    try:
        # Check if we're in a git repository
        run_command(["git", "status"], "Checking git repository", check=False)

        # Install pre-commit if available
        result = run_command(
            [sys.executable, "-m", "pip", "show", "pre-commit"],
            "Checking pre-commit installation",
            check=False,
        )

        if result.returncode == 0:
            run_command(["pre-commit", "install"], "Installing pre-commit hooks")
            print("  ✓ Pre-commit hooks installed")
        else:
            print("  ⚠ pre-commit not installed, skipping hooks setup")
            print("  Install with: pip install pre-commit")

    except Exception as e:
        print(f"  ⚠ Could not set up git hooks: {e}")


def generate_api_key():
    """Generate a new API key for testing."""
    print("Generating API key...")

    try:
        # Import security utilities
        sys.path.insert(0, str(Path.cwd()))
        from src.utils.security import get_api_key_manager

        manager = get_api_key_manager()
        key = manager.generate_key("development", expires_days=365)

        print(f"  ✓ Generated API key: {key}")
        print("  ⚠ Store this key securely - it won't be shown again")

        return key

    except Exception as e:
        print(f"  ✗ Could not generate API key: {e}")
        return None


def run_health_check():
    """Run a basic health check."""
    print("Running health check...")

    try:
        # Import and run basic checks
        sys.path.insert(0, str(Path.cwd()))

        # Check if we can import main modules
        try:
            import src.api.client

            print("  ✓ API client module")
        except ImportError as e:
            print(f"  ✗ API client module: {e}")

        try:
            import src.cache.manager

            print("  ✓ Cache manager module")
        except ImportError as e:
            print(f"  ✗ Cache manager module: {e}")

        try:
            import src.mcp.server  # noqa: F401

            print("  ✓ MCP server module")
        except ImportError as e:
            print(f"  ✗ MCP server module: {e}")

        print("  ✓ Basic module imports successful")

    except Exception as e:
        print(f"  ✗ Health check failed: {e}")


def run_tests():
    """Run the test suite."""
    print("Running tests...")

    test_commands = [
        ([sys.executable, "-m", "pytest", "tests/unit/", "-v"], "Unit tests"),
        (
            [sys.executable, "-m", "pytest", "tests/integration/", "-v"],
            "Integration tests",
        ),
    ]

    for cmd, description in test_commands:
        try:
            run_command(cmd, description, check=False)
        except Exception as e:
            print(f"  ⚠ {description} failed: {e}")


def setup_monitoring():
    """Set up monitoring configuration."""
    print("Setting up monitoring...")

    monitoring_dir = Path("monitoring")
    if monitoring_dir.exists():
        print("  ✓ Monitoring configuration already exists")
        return

    print("  ⚠ Monitoring directory not found")
    print("  Run the full setup to create monitoring configuration")


def create_docker_env():
    """Create Docker environment file."""
    print("Creating Docker environment file...")

    docker_env = Path(".env.docker")
    if docker_env.exists():
        print("  ✓ .env.docker already exists")
        return

    # Create Docker-specific environment
    docker_config = """# Docker Environment Configuration
KEAP_API_KEY=your_api_key_here
ENABLE_OPTIMIZATIONS=true
ENABLE_PERFORMANCE_MONITORING=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# Docker-specific settings
CACHE_DB_PATH=/app/data/keap_cache.db
LOG_FILE=/app/logs/keap_mcp.log

# Connection settings
MAX_CONNECTIONS=20
ENABLE_HTTP2=true

# Redis settings (if using)
REDIS_HOST=redis
REDIS_PORT=6379
"""

    with open(docker_env, "w") as f:
        f.write(docker_config)

    print("  ✓ Created .env.docker")


def setup_production():
    """Set up production configuration."""
    print("Setting up production configuration...")

    # Create production directories
    prod_dirs = [
        "data",
        "logs",
        "config",
        "monitoring/grafana/dashboards",
        "monitoring/prometheus",
        "ssl",
    ]

    for directory in prod_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Create production environment file
    prod_env = Path(".env.production")
    if not prod_env.exists():
        with open(".env.template", "r") as template:
            content = template.read()

        # Modify for production
        content = content.replace("LOG_LEVEL=INFO", "LOG_LEVEL=WARNING")
        content = content.replace("MAX_CONNECTIONS=20", "MAX_CONNECTIONS=50")
        content = content.replace(
            "ENABLE_OPTIMIZATIONS=true", "ENABLE_OPTIMIZATIONS=true"
        )

        with open(prod_env, "w") as f:
            f.write(content)

        print("  ✓ Created .env.production")

    print("  ✓ Production configuration ready")
    print("  ⚠ Remember to update .env.production with actual values")


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Keap MCP Service Setup")
    parser.add_argument(
        "command",
        choices=[
            "install",
            "dev",
            "test",
            "check",
            "docker",
            "production",
            "keygen",
            "all",
        ],
        help="Setup command to run",
    )

    parser.add_argument(
        "--skip-deps", action="store_true", help="Skip dependency installation"
    )
    parser.add_argument(
        "--skip-env", action="store_true", help="Skip environment setup"
    )

    args = parser.parse_args()

    print("🚀 Keap MCP Service Setup")
    print("=" * 40)

    # Always check Python version
    check_python_version()

    if args.command == "install":
        if not args.skip_deps:
            install_dependencies()
        if not args.skip_env:
            setup_environment()
        create_directories()

    elif args.command == "dev":
        if not args.skip_deps:
            install_dependencies(dev=True)
        if not args.skip_env:
            setup_environment()
        create_directories()
        setup_git_hooks()

    elif args.command == "test":
        run_tests()

    elif args.command == "check":
        run_health_check()

    elif args.command == "docker":
        create_directories()
        create_docker_env()

    elif args.command == "production":
        setup_production()

    elif args.command == "keygen":
        generate_api_key()

    elif args.command == "all":
        if not args.skip_deps:
            install_dependencies(dev=True)
        if not args.skip_env:
            setup_environment()
        create_directories()
        setup_git_hooks()
        create_docker_env()
        run_health_check()

    print("\n✅ Setup completed!")

    # Show next steps
    if args.command in ["install", "dev", "all"]:
        print("\n📋 Next steps:")
        print("1. Update .env with your Keap API key")
        print("2. Run: python run.py")
        print("3. Test: curl http://localhost:8000/health")

        if args.command in ["dev", "all"]:
            print("4. Run tests: python -m pytest")
            print("5. Load test: cd tests/load && ./run_load_tests.sh -t quick")


if __name__ == "__main__":
    main()

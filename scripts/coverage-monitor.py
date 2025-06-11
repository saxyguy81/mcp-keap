#!/usr/bin/env python3
"""
Coverage Monitor Script

Provides detailed coverage analysis and monitoring for the Keap MCP Server.
Helps identify coverage gaps and track improvements over time.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_command(command):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def generate_coverage_data():
    """Generate coverage data by running tests."""
    print("🧪 Running tests to generate coverage data...")

    success, stdout, stderr = run_command(
        "python -m pytest tests/unit/ --cov=src --cov-report=json --cov-report=xml --cov-report=term-missing"
    )

    if not success:
        print(f"❌ Failed to generate coverage data: {stderr}")
        return False

    print("✅ Coverage data generated successfully")
    return True


def analyze_coverage():
    """Analyze coverage data and provide detailed report."""
    coverage_file = Path("coverage.json")

    if not coverage_file.exists():
        print("❌ No coverage.json file found. Run tests first.")
        return None

    with open(coverage_file) as f:
        data = json.load(f)

    totals = data["totals"]
    files = data["files"]

    # Overall coverage
    coverage_percent = totals["percent_covered"]

    print(f"\n📊 Overall Coverage: {coverage_percent:.1f}%")
    print(f"   Lines Covered: {totals['covered_lines']}")
    print(f"   Total Lines: {totals['num_statements']}")
    print(f"   Missing Lines: {totals['missing_lines']}")

    # Coverage by module
    print("\n📁 Coverage by Module:")
    print("=" * 50)

    module_coverage = {}
    for file_path, file_data in files.items():
        if file_path.startswith("src/"):
            module = file_path.split("/")[1] if "/" in file_path else "root"
            if module not in module_coverage:
                module_coverage[module] = {"covered": 0, "total": 0, "files": []}

            module_coverage[module]["covered"] += file_data["summary"]["covered_lines"]
            module_coverage[module]["total"] += file_data["summary"]["num_statements"]
            module_coverage[module]["files"].append(
                {"file": file_path, "coverage": file_data["summary"]["percent_covered"]}
            )

    for module, data in sorted(module_coverage.items()):
        if data["total"] > 0:
            module_percent = (data["covered"] / data["total"]) * 100
            print(
                f"  {module:<20} {module_percent:>6.1f}% ({data['covered']}/{data['total']})"
            )

    # Low coverage files
    print("\n⚠️  Files with Low Coverage (< 50%):")
    print("=" * 50)

    low_coverage_files = []
    for file_path, file_data in files.items():
        if file_path.startswith("src/"):
            coverage = file_data["summary"]["percent_covered"]
            if coverage < 50:
                low_coverage_files.append((file_path, coverage))

    if low_coverage_files:
        for file_path, coverage in sorted(low_coverage_files, key=lambda x: x[1]):
            print(f"  {file_path:<40} {coverage:>6.1f}%")
    else:
        print("  ✅ No files with coverage below 50%")

    # High coverage files
    print("\n🎯 Files with Excellent Coverage (≥ 90%):")
    print("=" * 50)

    high_coverage_files = []
    for file_path, file_data in files.items():
        if file_path.startswith("src/"):
            coverage = file_data["summary"]["percent_covered"]
            if coverage >= 90:
                high_coverage_files.append((file_path, coverage))

    if high_coverage_files:
        for file_path, coverage in sorted(
            high_coverage_files, key=lambda x: x[1], reverse=True
        ):
            print(f"  {file_path:<40} {coverage:>6.1f}%")
    else:
        print("  📈 No files with coverage ≥ 90% yet")

    return coverage_percent


def track_coverage_history():
    """Track coverage history over time."""
    history_file = Path("coverage_history.json")

    if not Path("coverage.json").exists():
        return

    with open("coverage.json") as f:
        current_data = json.load(f)

    current_coverage = current_data["totals"]["percent_covered"]
    timestamp = datetime.now().isoformat()

    # Load existing history
    history = []
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)

    # Add current data point
    history.append(
        {
            "timestamp": timestamp,
            "coverage": current_coverage,
            "covered_lines": current_data["totals"]["covered_lines"],
            "total_lines": current_data["totals"]["num_statements"],
        }
    )

    # Keep only last 50 entries
    history = history[-50:]

    # Save updated history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    print(f"\n📈 Coverage history updated: {current_coverage:.1f}%")

    # Show trend if we have previous data
    if len(history) > 1:
        previous = history[-2]["coverage"]
        change = current_coverage - previous
        trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        print(f"   Trend: {trend} {change:+.1f}% from last run")


def generate_recommendations():
    """Generate recommendations for improving coverage."""
    print("\n💡 Coverage Improvement Recommendations:")
    print("=" * 50)

    if not Path("coverage.json").exists():
        return

    with open("coverage.json") as f:
        data = json.load(f)

    files = data["files"]
    recommendations = []

    # Find files with low coverage but high importance
    for file_path, file_data in files.items():
        if file_path.startswith("src/"):
            coverage = file_data["summary"]["percent_covered"]
            lines = file_data["summary"]["num_statements"]

            # High-impact files (many lines, low coverage)
            if lines > 50 and coverage < 60:
                recommendations.append(
                    f"📋 {file_path}: {coverage:.1f}% coverage, {lines} lines - High impact target"
                )

            # Service files should have high coverage
            elif "service" in file_path and coverage < 80:
                recommendations.append(
                    f"⚙️  {file_path}: {coverage:.1f}% coverage - Service layer priority"
                )

            # Utility files should be fully tested
            elif "utils" in file_path and coverage < 90:
                recommendations.append(
                    f"🔧 {file_path}: {coverage:.1f}% coverage - Utility functions need complete testing"
                )

    if recommendations:
        for rec in recommendations[:10]:  # Top 10 recommendations
            print(f"  {rec}")
    else:
        print("  🎉 No specific recommendations - coverage looks good!")

    print("\n📚 General Improvement Tips:")
    print("  • Focus on service layer tests (business logic)")
    print("  • Add error path testing (try/except blocks)")
    print("  • Test edge cases and validation logic")
    print("  • Mock external dependencies for isolated testing")
    print("  • Add integration tests for complete workflows")


def main():
    """Main coverage monitoring function."""
    print("🔍 Keap MCP Server - Coverage Monitor")
    print("=" * 50)

    # Generate fresh coverage data
    if not generate_coverage_data():
        sys.exit(1)

    # Analyze current coverage
    coverage_percent = analyze_coverage()

    if coverage_percent is None:
        sys.exit(1)

    # Track history
    track_coverage_history()

    # Generate recommendations
    generate_recommendations()

    # Summary
    print("\n🎯 Coverage Summary:")
    print(f"   Current: {coverage_percent:.1f}%")
    print("   Target:  60.0% (minimum)")
    print("   Goal:    80.0% (excellent)")

    if coverage_percent >= 80:
        print("   Status:  🎉 Excellent coverage!")
    elif coverage_percent >= 60:
        print("   Status:  ✅ Good coverage")
    else:
        print("   Status:  ⚠️  Needs improvement")

    print("\n💻 Run 'make coverage-html' to view detailed HTML report")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Advanced Filter Examples for Keap MCP Server

This script demonstrates the advanced filtering capabilities that have been restored,
including complex logical operations, optimization analysis, and performance monitoring.
"""

import asyncio
import json
from typing import Any

# Import MCP tools (would normally be called via MCP protocol)
from src.utils.filter_utils import validate_filter_conditions
from src.mcp.optimization.api_optimization import ApiParameterOptimizer


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print("=" * 60)


def print_example(title: str, data: Any):
    """Print a formatted example."""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))


async def main():
    """Demonstrate advanced filtering capabilities."""

    print_section("KEAP MCP ADVANCED FILTERING EXAMPLES")

    # Example 1: Complex Logical Filters
    print_section("1. Complex Logical Filter Operations")

    complex_filter_example = [
        {
            "operator": "OR",
            "conditions": [
                {
                    "operator": "AND",
                    "conditions": [
                        {
                            "field": "email",
                            "operator": "CONTAINS",
                            "value": "@company.com",
                        },
                        {
                            "field": "given_name",
                            "operator": "STARTS_WITH",
                            "value": "John",
                        },
                    ],
                },
                {
                    "field": "family_name",
                    "operator": "IN",
                    "value": ["Smith", "Johnson", "Williams"],
                },
            ],
        },
        {"field": "date_created", "operator": "SINCE", "value": "2024-01-01"},
    ]

    print_example("Complex Filter Structure", complex_filter_example)

    try:
        validate_filter_conditions(complex_filter_example)
        print("✓ Complex filter validation: PASSED")
    except Exception as e:
        print(f"✗ Complex filter validation: FAILED - {e}")

    # Example 2: Query Optimization Analysis
    print_section("2. Query Optimization Analysis")

    # Simple optimizable filters
    optimizable_filters = [
        {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
        {"field": "given_name", "operator": "EQUALS", "value": "John"},
        {"field": "id", "operator": "GREATER_THAN", "value": 1000},
    ]

    # Complex client-side filters
    complex_filters = [
        {"field": "custom_field_7", "operator": "CONTAINS", "value": "Engineering"},
        {
            "operator": "OR",
            "conditions": [
                {"field": "tags", "operator": "CONTAINS", "value": "VIP"},
                {"field": "tags", "operator": "CONTAINS", "value": "Premium"},
            ],
        },
    ]

    optimizer = ApiParameterOptimizer()

    print_example("Optimizable Filters", optimizable_filters)
    optimizable_result = optimizer.optimize_contact_query_parameters(
        optimizable_filters
    )
    print(f"Server-side filters: {optimizable_result.server_side_filters}")
    print(f"Optimization score: {optimizable_result.optimization_score:.2f}")
    print(f"Strategy: {optimizable_result.optimization_strategy}")
    print(
        f"Estimated data reduction: {optimizable_result.estimated_data_reduction_ratio:.1%}"
    )

    print_example("Complex Filters", complex_filters)
    complex_result = optimizer.optimize_contact_query_parameters(complex_filters)
    print(f"Server-side filters: {complex_result.server_side_filters}")
    print(f"Client-side filters: {len(complex_result.client_side_filters)} conditions")
    print(f"Optimization score: {complex_result.optimization_score:.2f}")
    print(f"Strategy: {complex_result.optimization_strategy}")

    # Example 3: Advanced Filter Operators
    print_section("3. Advanced Filter Operators")

    advanced_operators = [
        {"field": "email", "operator": "STARTS_WITH", "value": "admin"},
        {"field": "phone1", "operator": "NOT_CONTAINS", "value": "555"},
        {
            "field": "date_created",
            "operator": "BETWEEN",
            "value": ["2024-01-01", "2024-12-31"],
        },
        {"field": "id", "operator": "IN", "value": [123, 456, 789]},
        {"field": "city", "operator": "NOT_IN", "value": ["New York", "Los Angeles"]},
        {"field": "last_updated", "operator": "SINCE", "value": "yesterday"},
    ]

    print_example("Advanced Operators", advanced_operators)

    try:
        validate_filter_conditions(advanced_operators)
        print("✓ Advanced operators validation: PASSED")
    except Exception as e:
        print(f"✗ Advanced operators validation: FAILED - {e}")

    # Example 4: Nested Logical Groups
    print_section("4. Nested Logical Groups")

    nested_logical_example = [
        {
            "operator": "AND",
            "conditions": [
                {
                    "operator": "OR",
                    "conditions": [
                        {"field": "given_name", "operator": "EQUALS", "value": "John"},
                        {"field": "given_name", "operator": "EQUALS", "value": "Jane"},
                    ],
                },
                {
                    "operator": "NOT",
                    "conditions": [
                        {"field": "email", "operator": "CONTAINS", "value": "spam"}
                    ],
                },
                {"field": "date_created", "operator": "SINCE", "value": "2024-01-01"},
            ],
        }
    ]

    print_example("Nested Logical Groups", nested_logical_example)

    try:
        validate_filter_conditions(nested_logical_example)
        print("✓ Nested logical groups validation: PASSED")
    except Exception as e:
        print(f"✗ Nested logical groups validation: FAILED - {e}")

    # Example 5: Field Optimization Capabilities
    print_section("5. Field Optimization Capabilities")

    contact_capabilities = optimizer.get_field_optimization_info("contact")
    tag_capabilities = optimizer.get_field_optimization_info("tag")

    print("Contact Field Optimization:")
    for field, info in contact_capabilities.items():
        print(
            f"  {field}: {info['supported_operators']} (reduces data by {info['estimated_reduction']:.1%})"
        )

    print("\nTag Field Optimization:")
    for field, info in tag_capabilities.items():
        print(
            f"  {field}: {info['supported_operators']} (reduces data by {info['estimated_reduction']:.1%})"
        )

    # Example 6: Performance Analysis
    print_section("6. Performance Analysis Examples")

    performance_examples = [
        {
            "name": "High Performance Query",
            "filters": [
                {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
                {"field": "given_name", "operator": "EQUALS", "value": "John"},
            ],
        },
        {
            "name": "Medium Performance Query",
            "filters": [
                {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
                {"field": "custom_field_7", "operator": "EQUALS", "value": "VIP"},
            ],
        },
        {
            "name": "Complex Performance Query",
            "filters": [
                {
                    "operator": "OR",
                    "conditions": [
                        {"field": "tags", "operator": "CONTAINS", "value": "premium"},
                        {
                            "field": "custom_field_5",
                            "operator": "GREATER_THAN",
                            "value": 1000,
                        },
                    ],
                }
            ],
        },
    ]

    for example in performance_examples:
        print(f"\n{example['name']}:")
        analysis = optimizer.analyze_filter_performance(example["filters"])
        print(f"  Performance Rating: {analysis['performance_rating']}")
        print(f"  Optimization Score: {analysis['optimization_score']:.2f}")
        print(f"  Server-side filters: {analysis['server_side_filters']}")
        print(f"  Client-side filters: {analysis['client_side_filters']}")

    # Example 7: MCP Tool Usage Examples
    print_section("7. MCP Tool Usage Examples")

    mcp_examples = {
        "optimized_query_with_metrics": {
            "function": "query_contacts_optimized",
            "params": {
                "filters": [
                    {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
                    {
                        "operator": "OR",
                        "conditions": [
                            {
                                "field": "given_name",
                                "operator": "STARTS_WITH",
                                "value": "John",
                            },
                            {
                                "field": "given_name",
                                "operator": "STARTS_WITH",
                                "value": "Jane",
                            },
                        ],
                    },
                ],
                "limit": 50,
                "enable_optimization": True,
                "return_metrics": True,
                "include": ["id", "given_name", "family_name", "email"],
            },
        },
        "performance_analysis": {
            "function": "analyze_query_performance",
            "params": {
                "filters": [
                    {
                        "field": "custom_field_7",
                        "operator": "CONTAINS",
                        "value": "Engineering",
                    },
                    {
                        "field": "date_created",
                        "operator": "SINCE",
                        "value": "2024-01-01",
                    },
                ],
                "query_type": "contact",
            },
        },
        "id_list_intersection": {
            "function": "intersect_id_lists",
            "params": {
                "lists": [
                    {
                        "list_id": "premium_customers",
                        "item_ids": ["1", "2", "3", "4", "5"],
                    },
                    {
                        "list_id": "recent_purchases",
                        "item_ids": ["3", "4", "5", "6", "7"],
                    },
                    {
                        "list_id": "email_subscribers",
                        "item_ids": ["1", "3", "5", "7", "9"],
                    },
                ],
                "id_field": "item_ids",
            },
        },
    }

    for name, example in mcp_examples.items():
        print_example(f"MCP Tool: {name}", example)

    print_section("SUMMARY: ADVANCED FEATURES RESTORED")
    print("""
    ✓ Complex Logical Operators (AND, OR, NOT)
    ✓ Nested Filter Groups  
    ✓ Advanced Filter Operators (15+ operators)
    ✓ Query Optimization Framework
    ✓ Performance Analysis & Metrics
    ✓ Server-side vs Client-side Optimization
    ✓ Intelligent Caching with Optimization
    ✓ Field Capability Analysis
    ✓ Optimization Suggestions
    ✓ Performance Rating System
    
    Total MCP Tools: 15 (up from 5)
    - 5 Contact Operations
    - 4 Tag Operations  
    - 3 Batch Tag Operations
    - 2 Advanced Query Operations
    - 1 Utility Operation
    """)


if __name__ == "__main__":
    asyncio.run(main())

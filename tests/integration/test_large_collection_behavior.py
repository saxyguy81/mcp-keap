"""
Integration Tests for Large Collection Behavior and Edge Cases

Tests specific scenarios around large collections that were causing issues:
1. Large limit values (200+) returning 0 contacts when they shouldn't
2. Collection behavior consistency across different limit sizes
3. Performance with large datasets
4. Edge cases around pagination and collection creation
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    collection_union,
    collection_intersect,
    get_api_diagnostics,
    create_collection_from_ids,
)


class TestLargeCollectionBehavior:
    """Test large collection behavior and consistency."""

    @pytest.mark.asyncio
    async def test_large_limit_consistency(self):
        """Test that large limit values work consistently with smaller limits."""
        context = Context()
        
        # Test different limit sizes with the same broad filter
        test_limits = [10, 50, 100, 200]
        broad_filters = [{"field": "email", "operator": "contains", "value": "@"}]
        
        results = {}
        for limit in test_limits:
            result = await list_contacts(context, filters=broad_filters, limit=limit)
            results[limit] = result
            
            print(f"\n🔍 Limit {limit}: {result['count']} contacts")
            
            # Basic validation
            assert "collection_id" in result
            assert "count" in result
            assert isinstance(result["count"], int)
            assert result["count"] >= 0
            
            # The count should not exceed the limit
            assert result["count"] <= limit
        
        # Test consistency: larger limits should generally have >= smaller limits
        # (unless the database has fewer total contacts than the smaller limit)
        prev_count = 0
        for limit in test_limits:
            current_count = results[limit]["count"]
            
            # If previous result was less than its limit, then current should be >= previous
            # (unless we've exhausted all contacts in the database)
            if prev_count < limit // 2:  # Only compare if previous wasn't likely hitting database limit
                assert current_count >= prev_count, \
                    f"Limit {limit} returned {current_count} contacts, but limit {test_limits[test_limits.index(limit)-1] if test_limits.index(limit) > 0 else 0} returned {prev_count}"
            
            prev_count = current_count
        
        print("\n✅ Large limit consistency test passed")
        print(f"   Results: {[(limit, results[limit]['count']) for limit in test_limits]}")

    @pytest.mark.asyncio
    async def test_empty_vs_populated_collections_large_limits(self):
        """Test the difference between truly empty results and populated results with large limits."""
        context = Context()
        
        # Test 1: Truly restrictive filter that should return 0 contacts
        empty_filters = [{"field": "email", "operator": "equals", "value": "impossible_email_that_does_not_exist_12345@nowhere.invalid"}]
        empty_result = await list_contacts(context, filters=empty_filters, limit=200)
        
        print(f"\n🔍 Empty filter test (limit=200): {empty_result['count']} contacts")
        assert empty_result["count"] == 0
        assert "collection_id" in empty_result
        
        # Verify empty collection details work
        empty_details = await get_collection_details(context, empty_result["collection_id"])
        assert empty_details["count"] == 0
        assert empty_details["contacts"] == []
        
        # Test 2: Broad filter that should return many contacts
        broad_filters = [{"field": "email", "operator": "contains", "value": "@"}]
        broad_result = await list_contacts(context, filters=broad_filters, limit=200)
        
        print(f"🔍 Broad filter test (limit=200): {broad_result['count']} contacts")
        assert "collection_id" in broad_result
        assert isinstance(broad_result["count"], int)
        
        # If there are contacts in the system, broad filter should find some
        if broad_result["count"] > 0:
            # Verify we can get details
            broad_details = await get_collection_details(context, broad_result["collection_id"])
            assert broad_details["count"] == broad_result["count"]
            assert len(broad_details["contacts"]) == broad_result["count"]
            
            # Verify contacts have email addresses with @ symbol
            for contact in broad_details["contacts"][:5]:  # Check first 5
                email = contact.get("email", "")
                if email:  # If email exists, should contain @
                    assert "@" in email, f"Contact {contact.get('id')} email '{email}' doesn't contain @"
        
        print("✅ Empty vs populated collections test passed")

    @pytest.mark.asyncio
    async def test_progressive_limit_scaling(self):
        """Test that progressively larger limits work correctly."""
        context = Context()
        
        # Use broad filter that should find contacts
        base_filters = [{"field": "email", "operator": "contains", "value": "@"}]
        
        limits_to_test = [5, 10, 25, 50]  # Reduced limits based on actual database size
        previous_count = 0
        
        for limit in limits_to_test:
            result = await list_contacts(context, filters=base_filters, limit=limit)
            current_count = result["count"]
            
            print(f"\n🔍 Progressive test - Limit {limit}: {current_count} contacts")
            
            # Basic validation
            assert current_count >= 0
            assert current_count <= limit
            
            # Progressive validation: count should generally increase or stay same
            # (unless we've exhausted all available contacts)
            if previous_count > 0 and previous_count < limit:
                # Only assert increase if previous wasn't hitting database limit
                if previous_count == limits_to_test[limits_to_test.index(limit)-1]:
                    # Previous hit its limit, so current should be >= previous
                    assert current_count >= previous_count, \
                        f"Count decreased from {previous_count} to {current_count} when limit increased to {limit}"
            
            # Test collection details for collections with contacts
            if current_count > 0:
                details = await get_collection_details(context, result["collection_id"], limit=min(3, current_count))
                assert len(details["contacts"]) <= min(3, current_count)
                assert details["count"] == current_count
            
            previous_count = current_count
        
        print("✅ Progressive limit scaling test passed")

    @pytest.mark.asyncio
    async def test_large_collection_operations(self):
        """Test collection operations (union, intersect) with large collections."""
        context = Context()
        
        # Create two collections with different but overlapping filters
        collection1_result = await list_contacts(
            context, 
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=25
        )
        
        collection2_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": ".com"}],
            limit=20
        )
        
        print("\n🔍 Large collection operations:")
        print(f"  Collection 1 (@ emails): {collection1_result['count']} contacts")
        print(f"  Collection 2 (.com emails): {collection2_result['count']} contacts")
        
        if collection1_result["count"] > 0 and collection2_result["count"] > 0:
            # Test union operation
            union_result = await collection_union(context, [
                collection1_result["collection_id"],
                collection2_result["collection_id"]
            ])
            
            print(f"  Union result: {union_result['count']} contacts")
            assert union_result["count"] >= max(collection1_result["count"], collection2_result["count"])
            
            # Test intersection operation  
            intersect_result = await collection_intersect(context, [
                collection1_result["collection_id"],
                collection2_result["collection_id"]
            ])
            
            print(f"  Intersection result: {intersect_result['count']} contacts")
            assert intersect_result["count"] <= min(collection1_result["count"], collection2_result["count"])
            
            # Test that we can get details from operation results
            if union_result["count"] > 0:
                union_details = await get_collection_details(context, union_result["collection_id"], limit=3)
                assert len(union_details["contacts"]) <= min(3, union_result["count"])
                assert union_details["count"] == union_result["count"]
            
            print("✅ Large collection operations test passed")
        else:
            print("⚠️  Skipped collection operations test - insufficient contacts")

    @pytest.mark.asyncio
    async def test_large_collection_performance_tracking(self):
        """Test performance characteristics of large collections."""
        context = Context()
        
        import time
        
        # Test different collection sizes and track performance
        test_scenarios = [
            (10, "Small collection"),
            (50, "Medium collection"),
            (100, "Large collection"),
            (200, "Very large collection")
        ]
        
        performance_data = []
        
        for limit, description in test_scenarios:
            start_time = time.time()
            
            # Create collection
            result = await list_contacts(context, limit=limit)
            collection_create_time = time.time() - start_time
            
            # Get details
            details_start = time.time()
            if result["count"] > 0:
                await get_collection_details(context, result["collection_id"], limit=min(5, result["count"]))
                details_time = time.time() - details_start
            else:
                details_time = 0
            
            total_time = time.time() - start_time
            
            performance_data.append({
                "limit": limit,
                "description": description,
                "count": result["count"],
                "collection_create_time": collection_create_time,
                "details_time": details_time,
                "total_time": total_time
            })
            
            print(f"\n🔍 {description} (limit={limit}):")
            print(f"  Contacts found: {result['count']}")
            print(f"  Collection creation: {collection_create_time:.2f}s")
            print(f"  Details retrieval: {details_time:.2f}s")
            print(f"  Total time: {total_time:.2f}s")
        
        # Verify performance doesn't degrade unreasonably
        # (This is a basic check - in production you'd have more sophisticated metrics)
        largest_scenario = performance_data[-1]
        smallest_scenario = performance_data[0]
        
        if largest_scenario["count"] > 0 and smallest_scenario["count"] > 0:
            time_ratio = largest_scenario["total_time"] / smallest_scenario["total_time"]
            count_ratio = largest_scenario["count"] / smallest_scenario["count"]
            
            print("\n📊 Performance analysis:")
            print(f"  Count ratio (large/small): {count_ratio:.1f}x")
            print(f"  Time ratio (large/small): {time_ratio:.1f}x")
            
            # Time should not increase dramatically faster than count
            # (This is a loose check - real performance testing would be more rigorous)
            assert time_ratio < count_ratio * 3, f"Performance degradation too high: {time_ratio:.1f}x time for {count_ratio:.1f}x contacts"
        
        print("✅ Large collection performance tracking test passed")

    @pytest.mark.asyncio
    async def test_diagnostics_accuracy_with_large_collections(self):
        """Test that diagnostics remain accurate with large collections."""
        context = Context()
        
        # Create several large collections
        collections = []
        total_expected_contacts = 0
        
        for i, limit in enumerate([50, 75, 100], 1):
            result = await list_contacts(context, limit=limit)
            collections.append(result)
            total_expected_contacts += result["count"]
            
            print(f"\n🔍 Created collection {i}: {result['count']} contacts (limit={limit})")
        
        # Get diagnostics
        diagnostics = await get_api_diagnostics(context)
        
        print("\n📊 Diagnostics analysis:")
        print(f"  Total expected contacts: {total_expected_contacts}")
        
        if "collection_diagnostics" in diagnostics:
            reported_total = diagnostics["collection_diagnostics"].get("total_contacts_across_collections", 0)
            print(f"  Diagnostics reported: {reported_total}")
            
            # Diagnostics should be at least as large as our known collections
            assert reported_total >= total_expected_contacts, \
                f"Diagnostics reported {reported_total} but we created {total_expected_contacts} contacts"
            
            # But shouldn't be wildly inaccurate (more than 10x off)
            assert reported_total <= total_expected_contacts * 10, \
                f"Diagnostics reported {reported_total} which is suspiciously high vs {total_expected_contacts}"
        
        print("✅ Diagnostics accuracy test passed")

    @pytest.mark.asyncio
    async def test_create_large_collection_from_ids(self):
        """Test creating large collections from contact ID lists."""
        context = Context()
        
        # Get available contact IDs from the system
        source_result = await list_contacts(context, limit=50)
        if source_result["count"] < 3:
            pytest.skip("Need at least 3 contacts for collection ID test")
        
        source_details = await get_collection_details(context, source_result["collection_id"])
        available_ids = [contact["id"] for contact in source_details["contacts"]]
        
        if not available_ids:
            pytest.skip("No contact IDs available for testing")
        
        # Test creating collection from available ID list
        test_id_list = available_ids[:min(20, len(available_ids))]  # Use up to 20 available IDs
        
        large_collection = await create_collection_from_ids(
            context,
            test_id_list,
            name="Large ID Collection Test"
        )
        
        print("\n🔍 Large ID collection test:")
        print(f"  Requested IDs: {len(test_id_list)}")
        print(f"  Collection count: {large_collection['count']}")
        
        assert large_collection["count"] == len(test_id_list)
        assert large_collection["contact_ids"] == test_id_list
        
        # Verify we can get details efficiently
        details = await get_collection_details(context, large_collection["collection_id"], limit=5)
        assert len(details["contacts"]) <= min(5, len(test_id_list))
        assert details["count"] == len(test_id_list)
        
        print("✅ Large collection from IDs test passed")
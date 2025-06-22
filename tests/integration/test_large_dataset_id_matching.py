"""
Integration Tests for Large Dataset ID Matching

Tests that verify the ID matching fixes work correctly with large datasets
and various pagination scenarios, ensuring no contacts are lost due to
type conversion issues in different query strategies.
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    collection_union,
    collection_intersect,
    create_collection_from_ids
)


class TestLargeDatasetIDMatching:
    """Test ID matching accuracy with large datasets and pagination."""

    @pytest.mark.asyncio
    async def test_large_id_list_accuracy(self):
        """
        Test that large ID lists (100+ IDs) are handled correctly
        without the previous bug where only the first ID was used.
        """
        context = Context()
        
        print("\n🔍 Testing large ID list accuracy...")
        
        # Get a substantial number of contact IDs from the system
        source_result = await list_contacts(context, limit=150)
        if source_result["count"] < 10:
            pytest.skip("Need at least 10 contacts for large ID list test")
        
        source_details = await get_collection_details(context, source_result["collection_id"])
        available_ids = [contact["id"] for contact in source_details["contacts"]]
        
        if len(available_ids) < 10:
            pytest.skip("Need at least 10 contact IDs for testing")
        
        # Test with increasingly large ID lists
        test_sizes = [5, 10, 20, 50, min(100, len(available_ids))]
        
        for size in test_sizes:
            if size > len(available_ids):
                continue
                
            test_ids = available_ids[:size]
            
            print(f"\nTesting ID list of size {size}:")
            
            # Create collection from IDs
            id_collection = await create_collection_from_ids(
                context,
                test_ids,
                name=f"ID Test Collection {size}"
            )
            
            print(f"  Requested IDs: {len(test_ids)}")
            print(f"  Collection count: {id_collection['count']}")
            print(f"  Collection IDs: {len(id_collection['contact_ids'])}")
            
            # CRITICAL: All requested IDs should be found
            assert id_collection["count"] == len(test_ids), \
                f"Expected {len(test_ids)} contacts, got {id_collection['count']}"
            
            assert len(id_collection["contact_ids"]) == len(test_ids), \
                f"Expected {len(test_ids)} IDs in collection, got {len(id_collection['contact_ids'])}"
            
            # Verify the IDs match exactly (accounting for type differences)
            expected_ids = set(int(id) for id in test_ids)
            actual_ids = set(int(id) for id in id_collection["contact_ids"])
            
            assert expected_ids == actual_ids, \
                f"ID mismatch - Expected: {sorted(expected_ids)}, Got: {sorted(actual_ids)}"
            
            # Verify we can get details for all contacts
            details = await get_collection_details(context, id_collection["collection_id"])
            assert details["count"] == len(test_ids)
            assert len(details["contacts"]) == len(test_ids)
            
            print(f"  ✅ Successfully handled {size} IDs")
        
        print("✅ Large ID list accuracy test passed")

    @pytest.mark.asyncio
    async def test_mixed_type_id_handling(self):
        """
        Test that mixed string/integer ID types are handled correctly
        in all query strategies.
        """
        context = Context()
        
        print("\n🔍 Testing mixed type ID handling...")
        
        # Get some contact IDs
        source_result = await list_contacts(context, limit=20)
        if source_result["count"] < 5:
            pytest.skip("Need at least 5 contacts for mixed type test")
        
        source_details = await get_collection_details(context, source_result["collection_id"])
        available_ids = [contact["id"] for contact in source_details["contacts"]]
        
        if len(available_ids) < 5:
            pytest.skip("Need at least 5 contact IDs for testing")
        
        # Test with mixed types - some as strings, some as integers
        test_ids_mixed = []
        for i, contact_id in enumerate(available_ids[:5]):
            if i % 2 == 0:
                test_ids_mixed.append(str(contact_id))  # String
            else:
                test_ids_mixed.append(int(contact_id))   # Integer
        
        print(f"Testing mixed type IDs: {test_ids_mixed}")
        print(f"Types: {[type(id).__name__ for id in test_ids_mixed]}")
        
        # Create collection from mixed type IDs
        mixed_collection = await create_collection_from_ids(
            context,
            test_ids_mixed,
            name="Mixed Type ID Test"
        )
        
        print(f"  Requested: {len(test_ids_mixed)} IDs")
        print(f"  Found: {mixed_collection['count']} contacts")
        
        # Should find all contacts regardless of input type
        assert mixed_collection["count"] == len(test_ids_mixed), \
            f"Expected {len(test_ids_mixed)} contacts, got {mixed_collection['count']}"
        
        # Verify the ID sets match (normalized to integers)
        expected_ids = set(int(id) for id in test_ids_mixed)
        actual_ids = set(int(id) for id in mixed_collection["contact_ids"])
        
        assert expected_ids == actual_ids, \
            f"Mixed type ID mismatch - Expected: {sorted(expected_ids)}, Got: {sorted(actual_ids)}"
        
        print("✅ Mixed type ID handling test passed")

    @pytest.mark.asyncio
    async def test_id_matching_across_strategies(self):
        """
        Test that ID matching works correctly across different query strategies
        (individual calls, bulk strategy, optimization engine).
        """
        context = Context()
        
        print("\n🔍 Testing ID matching across query strategies...")
        
        # Get contact IDs for testing
        source_result = await list_contacts(context, limit=100)
        if source_result["count"] < 10:
            pytest.skip("Need at least 10 contacts for strategy comparison test")
        
        source_details = await get_collection_details(context, source_result["collection_id"])
        available_ids = [contact["id"] for contact in source_details["contacts"]]
        
        if len(available_ids) < 10:
            pytest.skip("Need at least 10 contact IDs for testing")
        
        # Test different collection sizes to trigger different strategies
        strategy_tests = [
            (available_ids[:5], "Small collection (individual calls)"),
            (available_ids[:50], "Medium collection (optimization engine)"), 
            (available_ids[:min(100, len(available_ids))], "Large collection (bulk strategy)")
        ]
        
        strategy_results = []
        
        for test_ids, description in strategy_tests:
            print(f"\n{description}:")
            
            # Create collection and verify accuracy
            collection = await create_collection_from_ids(
                context,
                test_ids,
                name=f"Strategy Test - {len(test_ids)} IDs"
            )
            
            success_rate = collection["count"] / len(test_ids)
            print(f"  Requested: {len(test_ids)} IDs")
            print(f"  Found: {collection['count']} contacts")
            print(f"  Success rate: {success_rate:.1%}")
            
            # All strategies should achieve 100% accuracy
            assert success_rate == 1.0, \
                f"{description} failed - only found {collection['count']}/{len(test_ids)} contacts"
            
            strategy_results.append({
                "description": description,
                "requested": len(test_ids),
                "found": collection["count"],
                "success_rate": success_rate
            })
        
        print("\n📊 Strategy comparison summary:")
        for result in strategy_results:
            print(f"  {result['description']}: {result['success_rate']:.1%} success")
        
        print("✅ ID matching across strategies test passed")

    @pytest.mark.asyncio
    async def test_pagination_id_consistency(self):
        """
        Test that contact IDs are consistent across different pagination offsets
        and that no IDs are duplicated or lost during large dataset operations.
        """
        context = Context()
        
        print("\n🔍 Testing pagination ID consistency...")
        
        # Get contacts from different pagination windows
        pagination_tests = [
            (0, 50, "First batch"),
            (50, 50, "Second batch"),
            (100, 50, "Third batch"),
        ]
        
        all_found_ids = set()
        batch_results = []
        
        for offset, limit, description in pagination_tests:
            print(f"\n{description} (offset={offset}, limit={limit}):")
            
            try:
                result = await list_contacts(
                    context,
                    limit=limit,
                    offset=offset,
                    enable_optimization=False  # Force consistent strategy
                )
                
                print(f"  Found: {result['count']} contacts")
                
                if result["count"] > 0:
                    details = await get_collection_details(context, result["collection_id"])
                    batch_ids = set(int(contact["id"]) for contact in details["contacts"])
                    
                    # Check for ID overlaps between batches
                    overlaps = all_found_ids.intersection(batch_ids)
                    if overlaps:
                        print(f"  ⚠️  Found {len(overlaps)} duplicate IDs: {sorted(overlaps)}")
                    else:
                        print("  ✅ No duplicate IDs found")
                    
                    all_found_ids.update(batch_ids)
                    
                    batch_results.append({
                        "description": description,
                        "count": result["count"],
                        "ids": batch_ids,
                        "duplicates": len(overlaps)
                    })
                    
                    # Sample a few IDs for detailed verification
                    sample_ids = list(batch_ids)[:3]
                    verification_collection = await create_collection_from_ids(
                        context,
                        sample_ids,
                        name=f"Verification - {description}"
                    )
                    
                    assert verification_collection["count"] == len(sample_ids), \
                        f"ID verification failed for {description} - expected {len(sample_ids)}, got {verification_collection['count']}"
                    
                    print(f"  ✅ Verified {len(sample_ids)} sample IDs")
                
            except Exception as e:
                print(f"  ❌ Error in {description}: {e}")
        
        total_unique_ids = len(all_found_ids)
        total_contacts_found = sum(batch["count"] for batch in batch_results)
        
        print("\n📊 Pagination consistency summary:")
        print(f"  Total contacts found: {total_contacts_found}")
        print(f"  Unique IDs found: {total_unique_ids}")
        print(f"  Duplication rate: {(total_contacts_found - total_unique_ids) / max(total_contacts_found, 1):.1%}")
        
        # Should have minimal duplication (ideally none)
        duplication_rate = (total_contacts_found - total_unique_ids) / max(total_contacts_found, 1)
        assert duplication_rate < 0.1, f"High duplication rate detected: {duplication_rate:.1%}"
        
        print("✅ Pagination ID consistency test passed")

    @pytest.mark.asyncio
    async def test_large_dataset_collection_operations(self):
        """
        Test that collection operations (union, intersect) work correctly
        with large datasets and maintain ID matching accuracy.
        """
        context = Context()
        
        print("\n🔍 Testing large dataset collection operations...")
        
        # Get a substantial number of contacts for testing
        base_result = await list_contacts(context, limit=100)
        if base_result["count"] < 20:
            pytest.skip("Need at least 20 contacts for collection operations test")
        
        base_details = await get_collection_details(context, base_result["collection_id"])
        all_available_ids = [contact["id"] for contact in base_details["contacts"]]
        
        if len(all_available_ids) < 20:
            pytest.skip("Need at least 20 contact IDs for testing")
        
        # Create two overlapping collections
        set_a_ids = all_available_ids[:15]  # First 15 contacts
        set_b_ids = all_available_ids[10:]   # Last N-10 contacts (overlap with A)
        
        print(f"Set A: {len(set_a_ids)} contacts")
        print(f"Set B: {len(set_b_ids)} contacts")
        print(f"Expected overlap: {len(set(set_a_ids).intersection(set(set_b_ids)))} contacts")
        
        # Create collections
        collection_a = await create_collection_from_ids(context, set_a_ids, name="Large Dataset Test A")
        collection_b = await create_collection_from_ids(context, set_b_ids, name="Large Dataset Test B")
        
        assert collection_a["count"] == len(set_a_ids)
        assert collection_b["count"] == len(set_b_ids)
        
        # Test union operation
        union_result = await collection_union(context, [
            collection_a["collection_id"],
            collection_b["collection_id"]
        ])
        
        expected_union_size = len(set(set_a_ids).union(set(set_b_ids)))
        print("\nUnion operation:")
        print(f"  Expected: {expected_union_size} contacts")
        print(f"  Actual: {union_result['count']} contacts")
        
        assert union_result["count"] == expected_union_size, \
            f"Union operation failed - expected {expected_union_size}, got {union_result['count']}"
        
        # Test intersection operation
        intersect_result = await collection_intersect(context, [
            collection_a["collection_id"], 
            collection_b["collection_id"]
        ])
        
        expected_intersect_size = len(set(set_a_ids).intersection(set(set_b_ids)))
        print("\nIntersection operation:")
        print(f"  Expected: {expected_intersect_size} contacts")
        print(f"  Actual: {intersect_result['count']} contacts")
        
        assert intersect_result["count"] == expected_intersect_size, \
            f"Intersection operation failed - expected {expected_intersect_size}, got {intersect_result['count']}"
        
        # Verify the actual IDs in intersection match expectations
        if intersect_result["count"] > 0:
            intersect_details = await get_collection_details(context, intersect_result["collection_id"])
            actual_intersect_ids = set(int(contact["id"]) for contact in intersect_details["contacts"])
            expected_intersect_ids = set(int(id) for id in set(set_a_ids).intersection(set(set_b_ids)))
            
            assert actual_intersect_ids == expected_intersect_ids, \
                f"Intersection IDs mismatch - Expected: {sorted(expected_intersect_ids)}, Got: {sorted(actual_intersect_ids)}"
        
        print("✅ Large dataset collection operations test passed")

    @pytest.mark.asyncio
    async def test_id_matching_performance_at_scale(self):
        """
        Test ID matching performance with large datasets to ensure
        the fixes don't introduce significant performance regressions.
        """
        context = Context()
        
        print("\n🔍 Testing ID matching performance at scale...")
        
        import time
        
        # Get a large number of contact IDs
        large_result = await list_contacts(context, limit=200)
        if large_result["count"] < 50:
            pytest.skip("Need at least 50 contacts for performance test")
        
        large_details = await get_collection_details(context, large_result["collection_id"])
        available_ids = [contact["id"] for contact in large_details["contacts"]]
        
        performance_tests = [
            (available_ids[:10], "Small batch"),
            (available_ids[:50], "Medium batch"),
            (available_ids[:min(100, len(available_ids))], "Large batch")
        ]
        
        performance_results = []
        
        for test_ids, description in performance_tests:
            print(f"\n{description} ({len(test_ids)} IDs):")
            
            start_time = time.time()
            
            # Create collection (tests ID matching accuracy)
            collection = await create_collection_from_ids(
                context,
                test_ids,
                name=f"Performance Test - {description}"
            )
            
            # Get details (tests retrieval performance)
            await get_collection_details(
                context,
                collection["collection_id"],
                limit=min(5, len(test_ids))
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            throughput = len(test_ids) / duration if duration > 0 else 0
            
            print(f"  Accuracy: {collection['count']}/{len(test_ids)} contacts found")
            print(f"  Time: {duration:.2f} seconds")
            print(f"  Throughput: {throughput:.1f} IDs/second")
            
            # Verify 100% accuracy
            assert collection["count"] == len(test_ids), \
                f"Performance test failed accuracy check - {collection['count']}/{len(test_ids)}"
            
            # Reasonable performance (should process at least 10 IDs per second)
            assert throughput >= 10, f"Performance too slow: {throughput:.1f} IDs/second"
            
            performance_results.append({
                "description": description,
                "ids_count": len(test_ids),
                "duration": duration,
                "throughput": throughput,
                "accuracy": collection["count"] / len(test_ids)
            })
        
        print("\n📊 Performance summary:")
        for result in performance_results:
            print(f"  {result['description']}: {result['throughput']:.1f} IDs/sec, {result['accuracy']:.1%} accuracy")
        
        print("✅ ID matching performance test passed")
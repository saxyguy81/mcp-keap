"""
Test ID matching logic to verify the fix works.
"""

def test_id_matching():
    """Test the ID matching logic with various ID types."""
    
    # Simulate the _contact_matches_filters function for ID matching
    def contact_matches_id_filter(contact_value, operator, value, field="id"):
        """Test the ID matching logic."""
        if operator == "in":
            if isinstance(value, (list, tuple)):
                # CRITICAL FIX: For ID fields, use numeric comparison to avoid string/int mismatches
                if field == "id":
                    try:
                        # Convert both contact_value and list values to integers for accurate comparison
                        contact_id = int(contact_value)
                        target_ids = [int(v) for v in value]
                        return contact_id in target_ids
                    except (ValueError, TypeError):
                        # Fallback to string comparison if conversion fails
                        return str(contact_value) in [str(v) for v in value]
                else:
                    # For non-ID fields, use case-insensitive string comparison
                    return str(contact_value).lower() in [str(v).lower() for v in value]
            return False
        return False
    
    # Test cases that were likely failing before the fix
    test_cases = [
        # Contact ID is int, target list contains ints
        (123, "in", [123, 456, 789], True, "Int contact_id with int list"),
        
        # Contact ID is int, target list contains strings
        (123, "in", ["123", "456", "789"], True, "Int contact_id with string list"),
        
        # Contact ID is string, target list contains ints  
        ("123", "in", [123, 456, 789], True, "String contact_id with int list"),
        
        # Contact ID is string, target list contains strings
        ("123", "in", ["123", "456", "789"], True, "String contact_id with string list"),
        
        # ID not in list
        (999, "in", [123, 456, 789], False, "ID not in list"),
        
        # Edge case: mixed types in list
        (123, "in", [123, "456", 789], True, "Mixed types in target list"),
    ]
    
    print("🔍 Testing ID matching logic:")
    print()
    
    all_passed = True
    
    for contact_value, operator, target_list, expected, description in test_cases:
        result = contact_matches_id_filter(contact_value, operator, target_list, "id")
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result != expected:
            all_passed = False
        
        print(f"{status} {description}")
        print(f"     Contact ID: {contact_value} ({type(contact_value).__name__})")
        print(f"     Target list: {target_list}")
        print(f"     Expected: {expected}, Got: {result}")
        print()
    
    if all_passed:
        print("🎉 All ID matching tests passed! The fix should work.")
    else:
        print("❌ Some tests failed - the fix needs adjustment.")
    
    return all_passed

if __name__ == "__main__":
    test_id_matching()
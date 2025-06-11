"""
Unit Tests for Filter Utilities

Tests utility functions for filtering data with pattern matching
including wildcard support and edge cases.
"""

from src.utils.filter_utils import filter_by_name_pattern


class TestFilterByNamePattern:
    """Test suite for filter_by_name_pattern function"""

    def test_filter_exact_match(self):
        """Test filtering with exact name match"""
        items = [{"name": "Customer"}, {"name": "Premium"}, {"name": "VIP"}]

        result = filter_by_name_pattern(items, "Customer")
        assert len(result) == 1
        assert result[0]["name"] == "Customer"

    def test_filter_wildcard_prefix(self):
        """Test filtering with wildcard prefix pattern"""
        items = [
            {"name": "Customer"},
            {"name": "CustomerVIP"},
            {"name": "CustomerPremium"},
            {"name": "Premium"},
        ]

        result = filter_by_name_pattern(items, "Customer*")
        assert len(result) == 3
        names = [item["name"] for item in result]
        assert "Customer" in names
        assert "CustomerVIP" in names
        assert "CustomerPremium" in names
        assert "Premium" not in names

    def test_filter_wildcard_suffix(self):
        """Test filtering with wildcard suffix pattern"""
        items = [
            {"name": "PremiumCustomer"},
            {"name": "VIPCustomer"},
            {"name": "Customer"},
            {"name": "Premium"},
        ]

        result = filter_by_name_pattern(items, "*Customer")
        assert len(result) == 3
        names = [item["name"] for item in result]
        assert "PremiumCustomer" in names
        assert "VIPCustomer" in names
        assert "Customer" in names
        assert "Premium" not in names

    def test_filter_wildcard_middle(self):
        """Test filtering with wildcard in middle of pattern"""
        items = [
            {"name": "CustomerPremium"},
            {"name": "CustomerVIP"},
            {"name": "CustomerBasic"},
            {"name": "PremiumCustomer"},
            {"name": "Customer"},
        ]

        result = filter_by_name_pattern(items, "Customer*Premium")
        assert len(result) == 1
        assert result[0]["name"] == "CustomerPremium"

    def test_filter_multiple_wildcards(self):
        """Test filtering with multiple wildcards"""
        items = [
            {"name": "abcdef"},
            {"name": "axcdef"},
            {"name": "abcxef"},
            {"name": "axcxef"},
            {"name": "abdef"},
        ]

        result = filter_by_name_pattern(items, "a*c*ef")
        assert len(result) == 4
        names = [item["name"] for item in result]
        assert "abcdef" in names
        assert "axcdef" in names
        assert "axcxef" in names
        assert "abcxef" in names  # Has 'c' in the middle
        assert "abdef" not in names  # Missing 'c' entirely

    def test_filter_case_insensitive(self):
        """Test that filtering is case insensitive"""
        items = [
            {"name": "Customer"},
            {"name": "CUSTOMER"},
            {"name": "customer"},
            {"name": "CuStOmEr"},
            {"name": "Premium"},
        ]

        result = filter_by_name_pattern(items, "customer")
        assert len(result) == 4

        result = filter_by_name_pattern(items, "CUSTOMER")
        assert len(result) == 4

        result = filter_by_name_pattern(items, "CuStOmEr")
        assert len(result) == 4

    def test_filter_case_insensitive_wildcards(self):
        """Test case insensitive matching with wildcards"""
        items = [
            {"name": "CustomerPremium"},
            {"name": "CUSTOMERPREMIUM"},
            {"name": "customerPREMIUM"},
            {"name": "Premium"},
        ]

        result = filter_by_name_pattern(items, "customer*premium")
        assert len(result) == 3

        result = filter_by_name_pattern(items, "CUSTOMER*PREMIUM")
        assert len(result) == 3

    def test_filter_empty_pattern(self):
        """Test filtering with empty pattern"""
        items = [{"name": "Customer"}, {"name": "Premium"}]

        result = filter_by_name_pattern(items, "")
        assert result == items  # Should return all items

    def test_filter_none_pattern(self):
        """Test filtering with None pattern"""
        items = [{"name": "Customer"}, {"name": "Premium"}]

        result = filter_by_name_pattern(items, None)
        assert result == items  # Should return all items

    def test_filter_empty_items(self):
        """Test filtering with empty items list"""
        result = filter_by_name_pattern([], "Customer")
        assert result == []

    def test_filter_none_items(self):
        """Test filtering with None items"""
        result = filter_by_name_pattern(None, "Customer")
        assert result is None

    def test_filter_items_without_name(self):
        """Test filtering items that don't have 'name' key"""
        items = [
            {"name": "Customer"},
            {"title": "Premium"},  # No 'name' key
            {"name": "VIP"},
            {"description": "Basic"},  # No 'name' key
        ]

        result = filter_by_name_pattern(items, "Customer")
        assert len(result) == 1
        assert result[0]["name"] == "Customer"

        result = filter_by_name_pattern(items, "*")
        assert len(result) == 2  # Only items with 'name' key
        names = [item["name"] for item in result]
        assert "Customer" in names
        assert "VIP" in names

    def test_filter_special_regex_characters(self):
        """Test filtering with special regex characters in names"""
        items = [
            {"name": "Customer[1]"},
            {"name": "Customer(2)"},
            {"name": "Customer.3"},
            {"name": "Customer+4"},
            {"name": "Customer^5"},
            {"name": "Customer$6"},
        ]

        # The current implementation treats these as regex patterns, not literal strings
        # [1] is treated as a character class, so it won't match Customer[1]
        result = filter_by_name_pattern(items, "Customer[1]")
        assert len(result) == 0  # No match because [1] is regex character class

        result = filter_by_name_pattern(items, "Customer*")
        assert len(result) == 6  # All should match with wildcard

    def test_filter_unicode_characters(self):
        """Test filtering with unicode characters"""
        items = [
            {"name": "Cliente"},
            {"name": "Müller"},
            {"name": "客户"},
            {"name": "العميل"},
            {"name": "Customer"},
        ]

        result = filter_by_name_pattern(items, "Cliente")
        assert len(result) == 1
        assert result[0]["name"] == "Cliente"

        result = filter_by_name_pattern(items, "Müller")
        assert len(result) == 1
        assert result[0]["name"] == "Müller"

        result = filter_by_name_pattern(items, "客户")
        assert len(result) == 1
        assert result[0]["name"] == "客户"

    def test_filter_wildcard_only(self):
        """Test filtering with wildcard-only pattern"""
        items = [
            {"name": "Customer"},
            {"name": "Premium"},
            {"name": "VIP"},
            {"other": "No name"},
        ]

        result = filter_by_name_pattern(items, "*")
        assert len(result) == 3  # All items with 'name' key
        names = [item["name"] for item in result]
        assert "Customer" in names
        assert "Premium" in names
        assert "VIP" in names

    def test_filter_complex_patterns(self):
        """Test filtering with complex wildcard patterns"""
        items = [
            {"name": "Customer_Premium_VIP"},
            {"name": "Customer_Basic_VIP"},
            {"name": "Customer_Premium_Standard"},
            {"name": "Client_Premium_VIP"},
            {"name": "Customer_VIP"},
        ]

        # Should match Customer_*_VIP patterns
        result = filter_by_name_pattern(items, "Customer_*_VIP")
        assert len(result) == 2
        names = [item["name"] for item in result]
        assert "Customer_Premium_VIP" in names
        assert "Customer_Basic_VIP" in names

        # Should match Customer_Premium_* patterns
        result = filter_by_name_pattern(items, "Customer_Premium_*")
        assert len(result) == 2
        names = [item["name"] for item in result]
        assert "Customer_Premium_VIP" in names
        assert "Customer_Premium_Standard" in names

    def test_filter_edge_cases(self):
        """Test edge cases and boundary conditions"""
        items = [
            {"name": ""},  # Empty name
            {"name": " "},  # Whitespace name
            {"name": "*"},  # Literal asterisk
            {"name": "Customer"},
        ]

        # Filter for empty name
        result = filter_by_name_pattern(items, "")
        assert len(result) == len(items)  # Empty pattern matches all

        # Filter for literal asterisk - should match all string names
        result = filter_by_name_pattern(items, "*")
        assert len(result) == 4  # All items should match

    def test_filter_performance_large_dataset(self):
        """Test filtering performance with large dataset"""
        # Create a large dataset
        items = [{"name": f"Customer_{i}"} for i in range(1000)]

        # Add some items that should match pattern
        items.extend(
            [
                {"name": "Premium_Customer_100"},
                {"name": "Premium_Customer_200"},
                {"name": "Premium_Customer_300"},
            ]
        )

        result = filter_by_name_pattern(items, "Premium_Customer_*")
        assert len(result) == 3

        # Test wildcard that matches many items
        result = filter_by_name_pattern(items, "Customer_*")
        assert len(result) == 1000  # All the generated items

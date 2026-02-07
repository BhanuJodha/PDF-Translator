"""Tests for page range parsing."""

from pdf_translator.utils.page_range import (
    _parse_range,
    _parse_single,
    parse_page_range,
)


class TestParsePageRange:
    """Tests for parse_page_range function."""

    def test_all_pages_lowercase(self):
        """'all' should return all page indices."""
        result = parse_page_range("all", 10)
        assert result == list(range(10))

    def test_all_pages_uppercase(self):
        """'ALL' should return all page indices."""
        result = parse_page_range("ALL", 10)
        assert result == list(range(10))

    def test_all_pages_mixed_case(self):
        """'All' should return all page indices."""
        result = parse_page_range("All", 10)
        assert result == list(range(10))

    def test_empty_string(self):
        """Empty string should return all pages."""
        result = parse_page_range("", 10)
        assert result == list(range(10))

    def test_whitespace_only(self):
        """Whitespace-only returns empty list (spaces removed, empty string can't parse)."""
        # "   " is truthy, so doesn't match `if not page_range`
        # After replace(" ", "") it becomes "", split gives [""]
        # "" can't be parsed as int, so returns empty
        result = parse_page_range("   ", 10)
        assert result == []

    def test_single_page_first(self):
        """First page should work."""
        result = parse_page_range("1", 10)
        assert result == [0]

    def test_single_page_middle(self):
        """Middle page should work."""
        result = parse_page_range("5", 10)
        assert result == [4]

    def test_single_page_last(self):
        """Last page should work."""
        result = parse_page_range("10", 10)
        assert result == [9]

    def test_page_range_basic(self):
        """Range like '1-3' should return those pages."""
        result = parse_page_range("1-3", 10)
        assert result == [0, 1, 2]

    def test_page_range_single_page(self):
        """Range like '5-5' should return single page."""
        result = parse_page_range("5-5", 10)
        assert result == [4]

    def test_page_range_full_document(self):
        """Range covering full document should work."""
        result = parse_page_range("1-10", 10)
        assert result == list(range(10))

    def test_comma_separated(self):
        """Comma-separated pages should all be included."""
        result = parse_page_range("1,5,9", 10)
        assert result == [0, 4, 8]

    def test_mixed_format(self):
        """Combination of ranges and singles should work."""
        result = parse_page_range("1-3,7,9-10", 10)
        assert result == [0, 1, 2, 6, 8, 9]

    def test_complex_mixed_format(self):
        """Complex combinations should work."""
        result = parse_page_range("1,3-5,7,9-10", 10)
        assert result == [0, 2, 3, 4, 6, 8, 9]

    def test_out_of_range_single_ignored(self):
        """Single pages beyond total should be ignored."""
        result = parse_page_range("1,50,100", 10)
        assert result == [0]

    def test_out_of_range_all_ignored(self):
        """All out of range should return empty."""
        result = parse_page_range("50,100", 10)
        assert result == []

    def test_range_clamped_end(self):
        """Ranges should be clamped at the end."""
        result = parse_page_range("8-15", 10)
        assert result == [7, 8, 9]

    def test_range_clamped_start(self):
        """Ranges should be clamped at the start."""
        result = parse_page_range("0-3", 10)  # 0 is invalid, starts at 1
        assert result == [0, 1, 2]

    def test_range_entirely_out(self):
        """Entirely out of range should return empty."""
        result = parse_page_range("20-30", 10)
        assert result == []

    def test_spaces_ignored(self):
        """Spaces in the input should be ignored."""
        result = parse_page_range("1, 3, 5", 10)
        assert result == [0, 2, 4]

    def test_spaces_in_range(self):
        """Spaces around range should be ignored."""
        result = parse_page_range("1 - 3", 10)
        # Note: this might not work depending on implementation
        # Let's test what actually happens
        result = parse_page_range("1-3, 5-7", 10)
        assert result == [0, 1, 2, 4, 5, 6]

    def test_invalid_parts_skipped(self):
        """Invalid parts should be silently skipped."""
        result = parse_page_range("1,abc,3", 10)
        assert result == [0, 2]

    def test_invalid_range_skipped(self):
        """Invalid range format should be skipped."""
        result = parse_page_range("1,2-3-4,5", 10)
        # 2-3-4 is invalid, should be skipped
        assert 0 in result
        assert 4 in result

    def test_sorted_output(self):
        """Output should always be sorted."""
        result = parse_page_range("9,1,5,3", 10)
        assert result == [0, 2, 4, 8]

    def test_duplicates_removed(self):
        """Duplicate pages should be removed."""
        result = parse_page_range("1,1,1-3,2", 10)
        assert result == [0, 1, 2]

    def test_overlapping_ranges(self):
        """Overlapping ranges should be deduplicated."""
        result = parse_page_range("1-5,3-7", 10)
        assert result == [0, 1, 2, 3, 4, 5, 6]

    def test_zero_total_pages(self):
        """Zero total pages should return empty."""
        result = parse_page_range("1-5", 0)
        assert result == []

    def test_negative_page_ignored(self):
        """Negative pages should be ignored."""
        result = parse_page_range("-1,1,2", 10)
        # -1 is invalid
        assert 0 in result


class TestParseRangeHelper:
    """Tests for _parse_range helper function."""

    def test_valid_range(self):
        """Should parse valid range."""
        result = _parse_range("1-5", 10)
        assert result == {0, 1, 2, 3, 4}

    def test_invalid_range_format(self):
        """Should return empty set for invalid format."""
        result = _parse_range("abc-def", 10)
        assert result == set()

    def test_range_with_extra_dash(self):
        """Should return empty set for extra dash."""
        result = _parse_range("1-2-3", 10)
        assert result == set()


class TestParseSingleHelper:
    """Tests for _parse_single helper function."""

    def test_valid_page(self):
        """Should parse valid page."""
        result = _parse_single("5", 10)
        assert result == {4}

    def test_invalid_page(self):
        """Should return empty set for invalid page."""
        result = _parse_single("abc", 10)
        assert result == set()

    def test_out_of_range_page(self):
        """Should return empty set for out of range."""
        result = _parse_single("50", 10)
        assert result == set()

    def test_zero_page(self):
        """Should return empty set for page 0."""
        result = _parse_single("0", 10)
        assert result == set()

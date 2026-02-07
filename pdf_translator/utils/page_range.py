"""Page range parsing utilities."""

from __future__ import annotations


def parse_page_range(page_range: str, total_pages: int) -> list[int]:
    """
    Parse a human-friendly page range string into 0-based page indices.

    Args:
        page_range: String like "1-5", "1,3,5", "all", or combinations
        total_pages: Total number of pages in the document

    Returns:
        Sorted list of 0-based page indices

    Examples:
        >>> parse_page_range("all", 10)
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> parse_page_range("1-3", 10)
        [0, 1, 2]
        >>> parse_page_range("1,5,9", 10)
        [0, 4, 8]
        >>> parse_page_range("1-3,7-9", 10)
        [0, 1, 2, 6, 7, 8]
    """
    if not page_range or page_range.lower().strip() == "all":
        return list(range(total_pages))

    pages: set[int] = set()
    parts = page_range.replace(" ", "").split(",")

    for part in parts:
        if "-" in part:
            pages.update(_parse_range(part, total_pages))
        else:
            pages.update(_parse_single(part, total_pages))

    return sorted(pages)


def _parse_range(part: str, total_pages: int) -> set[int]:
    """Parse a range like '1-5' into page indices."""
    try:
        start_str, end_str = part.split("-", 1)
        start = int(start_str)
        end = int(end_str)

        # Clamp to valid range and convert to 0-based
        start = max(1, start)
        end = min(total_pages, end)

        return {p - 1 for p in range(start, end + 1)}
    except ValueError:
        return set()


def _parse_single(part: str, total_pages: int) -> set[int]:
    """Parse a single page number."""
    try:
        page = int(part)
        if 1 <= page <= total_pages:
            return {page - 1}
    except ValueError:
        pass
    return set()

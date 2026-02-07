"""PDF text extraction for digitally-born PDFs using PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fitz


@dataclass
class TextBlock:
    """Represents an extracted text block with its properties."""

    text: str
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1
    font_name: str
    font_size: float
    color: int  # RGB as integer
    flags: int  # font flags (bold, italic, etc.)

    @property
    def is_bold(self) -> bool:
        """Check if text is bold (flag bit 4)."""
        return bool(self.flags & (1 << 4))

    @property
    def is_italic(self) -> bool:
        """Check if text is italic (flag bit 1)."""
        return bool(self.flags & (1 << 1))


class PDFExtractor:
    """
    Extracts text from digitally-born PDFs using PyMuPDF.

    This class handles text extraction with position and formatting
    information, and can detect whether a PDF contains extractable
    text or is a scanned image.
    """

    # Minimum text density (chars per page) to consider a page as having text
    MIN_TEXT_DENSITY = 50

    def __init__(self, path: str | Path):
        """
        Initialize the extractor with a PDF file.

        Args:
            path: Path to the PDF file
        """
        import fitz

        self.path = Path(path)
        self._doc: fitz.Document = fitz.open(str(self.path))

    def __enter__(self) -> PDFExtractor:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit - close the document."""
        self.close()

    def close(self) -> None:
        """Close the PDF document."""
        if self._doc:
            self._doc.close()

    @property
    def page_count(self) -> int:
        """Get the total number of pages."""
        return len(self._doc)

    def is_digital_pdf(self, sample_pages: int = 3) -> bool:
        """
        Detect if the PDF has extractable text (digital) or is scanned.

        Samples a few pages and checks if they contain sufficient text.
        A PDF is considered digital if most sampled pages have text.

        Args:
            sample_pages: Number of pages to sample for detection

        Returns:
            True if PDF appears to be digitally-born with extractable text
        """
        if self.page_count == 0:
            return False

        # Sample pages evenly distributed through the document
        pages_to_check = min(sample_pages, self.page_count)
        step = max(1, self.page_count // pages_to_check)
        indices = [i * step for i in range(pages_to_check)]

        pages_with_text = 0
        for idx in indices:
            if self.has_text_on_page(idx):
                pages_with_text += 1

        # Consider digital if majority of sampled pages have text
        return pages_with_text > pages_to_check // 2

    def has_text_on_page(self, page_num: int) -> bool:
        """
        Check if a specific page has extractable text.

        Args:
            page_num: 0-based page number

        Returns:
            True if page has sufficient extractable text
        """
        if page_num < 0 or page_num >= self.page_count:
            return False

        page = self._doc[page_num]
        text = page.get_text("text")

        # Check if there's meaningful text content
        cleaned = text.strip()
        return len(cleaned) >= self.MIN_TEXT_DENSITY

    def extract_text_blocks(self, page_num: int) -> list[TextBlock]:
        """
        Extract all text blocks from a page with formatting information.

        Args:
            page_num: 0-based page number

        Returns:
            List of TextBlock objects with text, position, and formatting
        """
        if page_num < 0 or page_num >= self.page_count:
            return []

        page = self._doc[page_num]
        blocks: list[TextBlock] = []

        # Get detailed text information
        text_dict = page.get_text("dict", flags=11)  # Include all text info

        for block in text_dict.get("blocks", []):
            # Skip image blocks
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue

                    blocks.append(
                        TextBlock(
                            text=text,
                            bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                            font_name=span.get("font", ""),
                            font_size=span.get("size", 12.0),
                            color=span.get("color", 0),
                            flags=span.get("flags", 0),
                        )
                    )

        return blocks

    def extract_page_text(self, page_num: int) -> str:
        """
        Extract plain text from a page.

        Args:
            page_num: 0-based page number

        Returns:
            Plain text content of the page
        """
        if page_num < 0 or page_num >= self.page_count:
            return ""

        page = self._doc[page_num]
        return page.get_text("text")

    def get_page_dimensions(self, page_num: int) -> tuple[float, float]:
        """
        Get the dimensions of a page.

        Args:
            page_num: 0-based page number

        Returns:
            Tuple of (width, height) in points
        """
        if page_num < 0 or page_num >= self.page_count:
            return (0.0, 0.0)

        page = self._doc[page_num]
        rect = page.rect
        return (rect.width, rect.height)

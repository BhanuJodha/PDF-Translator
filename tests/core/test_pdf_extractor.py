"""Tests for the PDF extractor module."""

import sys
from unittest.mock import MagicMock, patch

from pdf_translator.core.pdf_extractor import TextBlock


class TestTextBlock:
    """Tests for the TextBlock dataclass."""

    def test_basic_attributes(self):
        """Should store basic text block attributes."""
        block = TextBlock(
            text="Hello World",
            bbox=(10.0, 20.0, 100.0, 40.0),
            font_name="Helvetica",
            font_size=12.0,
            color=0x000000,
            flags=0,
        )

        assert block.text == "Hello World"
        assert block.bbox == (10.0, 20.0, 100.0, 40.0)
        assert block.font_name == "Helvetica"
        assert block.font_size == 12.0
        assert block.color == 0x000000

    def test_is_bold_flag(self):
        """Should detect bold text from flags."""
        bold_block = TextBlock(
            text="Bold",
            bbox=(0, 0, 0, 0),
            font_name="",
            font_size=12.0,
            color=0,
            flags=16,
        )
        assert bold_block.is_bold is True

        normal_block = TextBlock(
            text="Normal",
            bbox=(0, 0, 0, 0),
            font_name="",
            font_size=12.0,
            color=0,
            flags=0,
        )
        assert normal_block.is_bold is False

    def test_is_italic_flag(self):
        """Should detect italic text from flags."""
        italic_block = TextBlock(
            text="Italic",
            bbox=(0, 0, 0, 0),
            font_name="",
            font_size=12.0,
            color=0,
            flags=2,
        )
        assert italic_block.is_italic is True

    def test_bold_and_italic(self):
        """Should detect both bold and italic."""
        block = TextBlock(
            text="Bold Italic",
            bbox=(0, 0, 0, 0),
            font_name="",
            font_size=12.0,
            color=0,
            flags=18,
        )
        assert block.is_bold is True
        assert block.is_italic is True


class TestPDFExtractorInit:
    """Tests for PDFExtractor initialization."""

    def test_opens_document(self, tmp_path):
        """Should open the PDF document."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)

            mock_fitz.open.assert_called_once_with(str(pdf_path))
            assert extractor._doc == mock_doc

    def test_context_manager(self, tmp_path):
        """Should work as context manager."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            with PDFExtractor(pdf_path) as extractor:
                assert extractor._doc == mock_doc

            mock_doc.close.assert_called_once()


class TestPDFExtractorPageCount:
    """Tests for page count property."""

    def test_returns_page_count(self, tmp_path):
        """Should return correct page count."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=5)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            assert extractor.page_count == 5


class TestPDFExtractorIsDigital:
    """Tests for digital PDF detection."""

    def test_empty_pdf_not_digital(self, tmp_path):
        """Empty PDF should not be detected as digital."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=0)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            assert extractor.is_digital_pdf() is False

    def test_pdf_with_text_is_digital(self, tmp_path):
        """PDF with extractable text should be detected as digital."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "A" * 100

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=3)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            assert extractor.is_digital_pdf() is True

    def test_pdf_without_text_not_digital(self, tmp_path):
        """PDF without extractable text should not be detected as digital."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "   "

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=3)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            assert extractor.is_digital_pdf() is False


class TestPDFExtractorHasTextOnPage:
    """Tests for page text detection."""

    def test_page_with_text(self, tmp_path):
        """Should detect page with sufficient text."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "X" * 100

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            assert extractor.has_text_on_page(0) is True

    def test_page_without_text(self, tmp_path):
        """Should detect page without sufficient text."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hi"

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            assert extractor.has_text_on_page(0) is False

    def test_invalid_page_number(self, tmp_path):
        """Should return False for invalid page numbers."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            assert extractor.has_text_on_page(-1) is False
            assert extractor.has_text_on_page(10) is False


class TestPDFExtractorExtractTextBlocks:
    """Tests for text block extraction."""

    def test_extracts_text_blocks(self, tmp_path):
        """Should extract text blocks with formatting."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {
                                    "text": "Hello World",
                                    "bbox": (10, 20, 100, 40),
                                    "font": "Helvetica",
                                    "size": 12.0,
                                    "color": 0x000000,
                                    "flags": 0,
                                }
                            ]
                        }
                    ],
                }
            ]
        }

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            blocks = extractor.extract_text_blocks(0)

            assert len(blocks) == 1
            assert blocks[0].text == "Hello World"
            assert blocks[0].font_name == "Helvetica"

    def test_skips_image_blocks(self, tmp_path):
        """Should skip image blocks (type != 0)."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {"type": 1},
                {
                    "type": 0,
                    "lines": [{"spans": [{"text": "Text", "bbox": (0, 0, 0, 0)}]}],
                },
            ]
        }

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            blocks = extractor.extract_text_blocks(0)

            assert len(blocks) == 1

    def test_invalid_page_returns_empty(self, tmp_path):
        """Should return empty list for invalid page."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            blocks = extractor.extract_text_blocks(99)

            assert blocks == []


class TestPDFExtractorExtractPageText:
    """Tests for plain text extraction."""

    def test_extracts_plain_text(self, tmp_path):
        """Should extract plain text from page."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello World"

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            text = extractor.extract_page_text(0)

            assert text == "Hello World"

    def test_invalid_page_returns_empty(self, tmp_path):
        """Should return empty string for invalid page."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            text = extractor.extract_page_text(99)

            assert text == ""


class TestPDFExtractorGetPageDimensions:
    """Tests for page dimension retrieval."""

    def test_returns_dimensions(self, tmp_path):
        """Should return page width and height."""
        mock_fitz = MagicMock()
        mock_rect = MagicMock()
        mock_rect.width = 612.0
        mock_rect.height = 792.0

        mock_page = MagicMock()
        mock_page.rect = mock_rect

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            width, height = extractor.get_page_dimensions(0)

            assert width == 612.0
            assert height == 792.0

    def test_invalid_page_returns_zero(self, tmp_path):
        """Should return (0, 0) for invalid page."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            from pdf_translator.core.pdf_extractor import PDFExtractor

            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            extractor = PDFExtractor(pdf_path)
            width, height = extractor.get_page_dimensions(99)

            assert width == 0.0
            assert height == 0.0

"""Tests for the PDF renderer module."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from pdf_translator.core.pdf_extractor import TextBlock
from pdf_translator.core.pdf_renderer import PDFRenderer


class TestPDFRendererInit:
    """Tests for PDFRenderer initialization."""

    def test_default_language(self):
        """Should default to Hindi."""
        renderer = PDFRenderer()
        assert renderer.target_lang == "hi"

    def test_custom_language(self):
        """Should accept custom target language."""
        renderer = PDFRenderer(target_lang="zh")
        assert renderer.target_lang == "zh"

    def test_initial_state(self):
        """Should start with no document open."""
        renderer = PDFRenderer()
        assert renderer._doc is None


class TestPDFRendererFontMapping:
    """Tests for font selection."""

    def test_chinese_simplified_font(self):
        """Should return Chinese font for zh."""
        renderer = PDFRenderer(target_lang="zh")
        font = renderer._get_font_for_language("zh")
        assert font == "china-s"

    def test_chinese_traditional_font(self):
        """Should return Traditional Chinese font for zh-tw."""
        renderer = PDFRenderer()
        font = renderer._get_font_for_language("zh-tw")
        assert font == "china-t"

    def test_japanese_font(self):
        """Should return Japanese font for ja."""
        renderer = PDFRenderer()
        font = renderer._get_font_for_language("ja")
        assert font == "japan"

    def test_korean_font(self):
        """Should return Korean font for ko."""
        renderer = PDFRenderer()
        font = renderer._get_font_for_language("ko")
        assert font == "korea"

    def test_default_font(self):
        """Should return Helvetica for unknown languages."""
        renderer = PDFRenderer()
        font = renderer._get_font_for_language("unknown")
        assert font == "helv"

    def test_indic_script_fallback(self):
        """Should return fallback for Indic scripts."""
        renderer = PDFRenderer()
        for lang in ["hi", "bn", "ta", "te", "mr"]:
            font = renderer._get_font_for_language(lang)
            assert font == "helv"

    def test_arabic_script_fallback(self):
        """Should return fallback for Arabic scripts."""
        renderer = PDFRenderer()
        for lang in ["ar", "fa", "ur"]:
            font = renderer._get_font_for_language(lang)
            assert font == "helv"


class TestPDFRendererColorConversion:
    """Tests for color conversion."""

    def test_black_color(self):
        """Should convert black correctly."""
        renderer = PDFRenderer()
        r, g, b = renderer._int_to_rgb(0x000000)
        assert r == 0.0
        assert g == 0.0
        assert b == 0.0

    def test_white_color(self):
        """Should convert white correctly."""
        renderer = PDFRenderer()
        r, g, b = renderer._int_to_rgb(0xFFFFFF)
        assert r == 1.0
        assert g == 1.0
        assert b == 1.0

    def test_red_color(self):
        """Should convert red correctly."""
        renderer = PDFRenderer()
        r, g, b = renderer._int_to_rgb(0xFF0000)
        assert r == 1.0
        assert g == 0.0
        assert b == 0.0

    def test_green_color(self):
        """Should convert green correctly."""
        renderer = PDFRenderer()
        r, g, b = renderer._int_to_rgb(0x00FF00)
        assert r == 0.0
        assert g == 1.0
        assert b == 0.0

    def test_blue_color(self):
        """Should convert blue correctly."""
        renderer = PDFRenderer()
        r, g, b = renderer._int_to_rgb(0x0000FF)
        assert r == 0.0
        assert g == 0.0
        assert b == 1.0

    def test_mixed_color(self):
        """Should convert mixed colors correctly."""
        renderer = PDFRenderer()
        r, g, b = renderer._int_to_rgb(0x808080)
        assert abs(r - 0.502) < 0.01
        assert abs(g - 0.502) < 0.01
        assert abs(b - 0.502) < 0.01


class TestPDFRendererOpenClose:
    """Tests for document open/close operations."""

    def test_open_document(self, tmp_path):
        """Should open PDF document."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            renderer = PDFRenderer()
            renderer.open(pdf_path)

            mock_fitz.open.assert_called_once_with(str(pdf_path))
            assert renderer._doc == mock_doc

    def test_close_document(self, tmp_path):
        """Should close PDF document."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            renderer = PDFRenderer()
            renderer.open(pdf_path)
            renderer.close()

            mock_doc.close.assert_called_once()
            assert renderer._doc is None

    def test_close_without_open(self):
        """Should handle close when no document is open."""
        renderer = PDFRenderer()
        renderer.close()  # Should not raise


class TestPDFRendererSave:
    """Tests for document saving."""

    def test_save_document(self, tmp_path):
        """Should save PDF document."""
        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")
            output_path = tmp_path / "output.pdf"

            renderer = PDFRenderer()
            renderer.open(pdf_path)
            result = renderer.save(output_path)

            mock_doc.save.assert_called_once()
            assert result == output_path

    def test_save_without_open(self):
        """Should raise error when saving without open document."""
        renderer = PDFRenderer()

        with pytest.raises(RuntimeError, match="No document open"):
            renderer.save("output.pdf")


class TestPDFRendererReplaceText:
    """Tests for text replacement."""

    def test_replace_text_on_page(self, tmp_path):
        """Should replace text blocks on a page."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc
        mock_fitz.Rect.return_value = MagicMock(is_empty=False, is_infinite=False)

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            blocks = [
                TextBlock(
                    text="Hello",
                    bbox=(10, 20, 100, 40),
                    font_name="Helvetica",
                    font_size=12.0,
                    color=0x000000,
                    flags=0,
                )
            ]
            translations = ["नमस्ते"]

            renderer = PDFRenderer(target_lang="hi")
            renderer.open(pdf_path)
            renderer.replace_text_on_page(0, blocks, translations)

            mock_page.add_redact_annot.assert_called_once()
            mock_page.apply_redactions.assert_called_once_with(images=0)

    def test_skips_empty_translation(self, tmp_path):
        """Should skip blocks with empty translations."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            blocks = [
                TextBlock(
                    text="Hello",
                    bbox=(10, 20, 100, 40),
                    font_name="Helvetica",
                    font_size=12.0,
                    color=0x000000,
                    flags=0,
                )
            ]
            translations = [""]

            renderer = PDFRenderer()
            renderer.open(pdf_path)
            renderer.replace_text_on_page(0, blocks, translations)

            mock_page.add_redact_annot.assert_not_called()

    def test_skips_whitespace_translation(self, tmp_path):
        """Should skip blocks with whitespace-only translations."""
        mock_fitz = MagicMock()
        mock_page = MagicMock()
        mock_doc = MagicMock()
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_fitz.open.return_value = mock_doc

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            blocks = [
                TextBlock(
                    text="Hello",
                    bbox=(10, 20, 100, 40),
                    font_name="Helvetica",
                    font_size=12.0,
                    color=0x000000,
                    flags=0,
                )
            ]
            translations = ["   "]

            renderer = PDFRenderer()
            renderer.open(pdf_path)
            renderer.replace_text_on_page(0, blocks, translations)

            mock_page.add_redact_annot.assert_not_called()

    def test_mismatched_blocks_translations(self):
        """Should raise error when blocks and translations don't match."""
        renderer = PDFRenderer()
        renderer._doc = MagicMock()

        blocks = [
            TextBlock(
                text="Hello",
                bbox=(0, 0, 0, 0),
                font_name="",
                font_size=12.0,
                color=0,
                flags=0,
            )
        ]
        translations = ["One", "Two"]

        with pytest.raises(ValueError, match="must match"):
            renderer.replace_text_on_page(0, blocks, translations)

    def test_replace_without_open(self):
        """Should raise error when replacing without open document."""
        renderer = PDFRenderer()

        with pytest.raises(RuntimeError, match="No document open"):
            renderer.replace_text_on_page(0, [], [])


class TestPDFRendererReplaceSingleBlock:
    """Tests for single block replacement."""

    def test_skips_empty_rect(self):
        """Should skip blocks with empty rectangles."""
        mock_fitz = MagicMock()
        mock_rect = MagicMock()
        mock_rect.is_empty = True
        mock_rect.is_infinite = False
        mock_fitz.Rect.return_value = mock_rect

        mock_page = MagicMock()

        block = TextBlock(
            text="Hello",
            bbox=(0, 0, 0, 0),
            font_name="Helvetica",
            font_size=12.0,
            color=0x000000,
            flags=0,
        )

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            renderer = PDFRenderer()
            renderer._replace_single_block(mock_page, block, "Translation")

            mock_page.add_redact_annot.assert_not_called()

    def test_skips_infinite_rect(self):
        """Should skip blocks with infinite rectangles."""
        mock_fitz = MagicMock()
        mock_rect = MagicMock()
        mock_rect.is_empty = False
        mock_rect.is_infinite = True
        mock_fitz.Rect.return_value = mock_rect

        mock_page = MagicMock()

        block = TextBlock(
            text="Hello",
            bbox=(0, 0, 100, 100),
            font_name="Helvetica",
            font_size=12.0,
            color=0x000000,
            flags=0,
        )

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            renderer = PDFRenderer()
            renderer._replace_single_block(mock_page, block, "Translation")

            mock_page.add_redact_annot.assert_not_called()

    def test_scales_font_for_longer_translation(self):
        """Should add redaction for text replacement."""
        mock_fitz = MagicMock()
        mock_rect = MagicMock()
        mock_rect.is_empty = False
        mock_rect.is_infinite = False
        mock_fitz.Rect.return_value = mock_rect

        mock_page = MagicMock()

        block = TextBlock(
            text="Hi",
            bbox=(0, 0, 100, 20),
            font_name="Helvetica",
            font_size=12.0,
            color=0x000000,
            flags=0,
        )

        with patch.dict(sys.modules, {"fitz": mock_fitz}):
            renderer = PDFRenderer()
            renderer._replace_single_block(
                mock_page, block, "This is a much longer translation"
            )

            # Should add redaction annotation to remove original text
            mock_page.add_redact_annot.assert_called_once()
            call_kwargs = mock_page.add_redact_annot.call_args[1]
            # Fill should be white to cover original text
            assert call_kwargs["fill"] == (1, 1, 1)

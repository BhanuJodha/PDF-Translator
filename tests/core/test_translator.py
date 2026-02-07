"""Tests for the main PDF translator module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from pdf_translator.core.config import TranslationConfig
from pdf_translator.core.translator import PDFTranslator


class TestPDFTranslatorInit:
    """Tests for PDFTranslator initialization."""

    def test_init_with_default_config(self):
        """Should create translator with default config."""
        translator = PDFTranslator()

        assert translator.config is not None
        assert translator.config.source_lang == "en"
        assert translator.config.target_lang == "hi"
        assert translator._ocr is not None
        assert translator._text_translator is None
        assert translator._renderer is None

    def test_init_with_custom_config(self):
        """Should accept custom configuration."""
        config = TranslationConfig(
            source_lang="es",
            target_lang="fr",
            device="cpu",
        )
        translator = PDFTranslator(config)

        assert translator.config.source_lang == "es"
        assert translator.config.target_lang == "fr"
        assert translator.config.device == "cpu"

    def test_init_applies_environment(self):
        """Should apply config to environment on init."""
        config = TranslationConfig(device="cpu")

        with patch.object(config, "apply_environment") as mock_apply:
            # Re-init to trigger apply
            config.apply_environment()
            mock_apply.assert_called_once()


class TestPDFTranslatorPageRange:
    """Tests for page range parsing in PDFTranslator."""

    def test_parse_all_pages(self):
        """'all' should return all pages."""
        translator = PDFTranslator()
        result = translator._parse_page_range("all", 10)
        assert result == list(range(10))

    def test_parse_empty_string(self):
        """Empty string should return all pages."""
        translator = PDFTranslator()
        result = translator._parse_page_range("", 5)
        assert result == [0, 1, 2, 3, 4]

    def test_parse_single_page(self):
        """Single page number should work."""
        translator = PDFTranslator()
        result = translator._parse_page_range("3", 10)
        assert result == [2]  # 0-indexed

    def test_parse_page_range(self):
        """Range format should work."""
        translator = PDFTranslator()
        result = translator._parse_page_range("2-5", 10)
        assert result == [1, 2, 3, 4]

    def test_parse_comma_separated(self):
        """Comma-separated pages should work."""
        translator = PDFTranslator()
        result = translator._parse_page_range("1,3,5", 10)
        assert result == [0, 2, 4]

    def test_parse_mixed_format(self):
        """Mixed ranges and singles should work."""
        translator = PDFTranslator()
        result = translator._parse_page_range("1-2,5,8-10", 10)
        assert result == [0, 1, 4, 7, 8, 9]

    def test_parse_out_of_range(self):
        """Out of range pages should be ignored."""
        translator = PDFTranslator()
        result = translator._parse_page_range("1,100", 10)
        assert result == [0]

    def test_parse_invalid_range(self, capsys):
        """Invalid range should print warning and skip."""
        translator = PDFTranslator()
        result = translator._parse_page_range("1,abc,3", 10)
        assert result == [0, 2]

        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_parse_invalid_range_format(self, capsys):
        """Invalid range format should print warning."""
        translator = PDFTranslator()
        translator._parse_page_range("1-2-3", 10)

        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_parse_with_spaces(self):
        """Spaces should be ignored."""
        translator = PDFTranslator()
        result = translator._parse_page_range("1, 3, 5", 10)
        assert result == [0, 2, 4]


class TestPDFTranslatorTranslate:
    """Tests for the translate method."""

    def test_translate_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        translator = PDFTranslator()

        with pytest.raises(FileNotFoundError):
            translator.translate("/nonexistent/path.pdf")

    def test_translate_default_output_path(self, tmp_path):
        """Should generate default output path."""
        translator = PDFTranslator()
        input_path = tmp_path / "document.pdf"
        input_path.write_bytes(b"%PDF-1.4")

        # Mock the heavy operations
        with (
            patch.object(translator, "_load_pdf") as mock_load,
            patch.object(translator, "_run_ocr") as mock_ocr,
            patch.object(translator, "_process_pages") as mock_process,
        ):

            mock_load.return_value = ([Image.new("RGB", (100, 100))], [0])
            mock_ocr.return_value = [[]]
            mock_process.return_value = [np.zeros((100, 100, 3), dtype=np.uint8)]

            result = translator.translate(input_path)

            assert result == tmp_path / "document_translated.pdf"

    def test_translate_custom_output_path(self, tmp_path):
        """Should use custom output path when provided."""
        translator = PDFTranslator()
        input_path = tmp_path / "input.pdf"
        output_path = tmp_path / "custom_output.pdf"
        input_path.write_bytes(b"%PDF-1.4")

        with (
            patch.object(translator, "_load_pdf") as mock_load,
            patch.object(translator, "_run_ocr") as mock_ocr,
            patch.object(translator, "_process_pages") as mock_process,
        ):

            mock_load.return_value = ([Image.new("RGB", (100, 100))], [0])
            mock_ocr.return_value = [[]]
            mock_process.return_value = [np.zeros((100, 100, 3), dtype=np.uint8)]

            result = translator.translate(input_path, output_path=output_path)

            assert result == output_path

    def test_translate_overrides_languages(self, tmp_path):
        """Should use provided languages over config."""
        translator = PDFTranslator()
        input_path = tmp_path / "test.pdf"
        input_path.write_bytes(b"%PDF-1.4")

        with (
            patch.object(translator, "_load_pdf") as mock_load,
            patch.object(translator, "_run_ocr") as mock_ocr,
            patch.object(translator, "_process_pages") as mock_process,
        ):

            mock_load.return_value = ([Image.new("RGB", (100, 100))], [0])
            mock_ocr.return_value = [[]]
            mock_process.return_value = [np.zeros((100, 100, 3), dtype=np.uint8)]

            translator.translate(
                input_path,
                source_lang="es",
                target_lang="fr",
            )

            # Check that translators were created with overridden languages
            assert translator._text_translator.source_lang == "es"
            assert translator._text_translator.target_lang == "fr"

    def test_translate_progress_callback(self, tmp_path):
        """Should call progress callback at each stage."""
        translator = PDFTranslator()
        input_path = tmp_path / "test.pdf"
        input_path.write_bytes(b"%PDF-1.4")

        callback = MagicMock()

        with (
            patch.object(translator, "_load_pdf") as mock_load,
            patch.object(translator, "_run_ocr") as mock_ocr,
            patch.object(translator, "_process_pages") as mock_process,
        ):

            mock_load.return_value = ([Image.new("RGB", (100, 100))], [0])
            mock_ocr.return_value = [[]]
            mock_process.return_value = [np.zeros((100, 100, 3), dtype=np.uint8)]

            translator.translate(input_path, progress_callback=callback)

            # Should be called 5 times (0-4)
            assert callback.call_count == 5
            callback.assert_any_call("Converting PDF", 0, 4)
            callback.assert_any_call("Running OCR", 1, 4)
            callback.assert_any_call("Translating", 2, 4)
            callback.assert_any_call("Saving PDF", 3, 4)
            callback.assert_any_call("Done", 4, 4)


class TestPDFTranslatorProcessing:
    """Tests for internal processing methods."""

    def test_process_single_page_empty_regions(self):
        """Should return original image when no regions."""
        translator = PDFTranslator()
        translator._text_translator = MagicMock()
        translator._renderer = MagicMock()

        image = Image.new("RGB", (100, 100), color="white")
        result = translator._process_single_page((image, []))

        assert result.shape == (100, 100, 3)
        translator._text_translator.translate_batch.assert_not_called()

    def test_process_single_page_with_regions(self):
        """Should translate and render when regions exist."""
        translator = PDFTranslator()
        translator._text_translator = MagicMock()
        translator._text_translator.translate_batch.return_value = ["translated"]
        translator._renderer = MagicMock()
        translator._renderer.render_translations.return_value = np.zeros((100, 100, 3))

        image = Image.new("RGB", (100, 100))
        regions = [{"text": "hello", "box": [0, 0, 50, 20], "formatting": {}}]

        translator._process_single_page((image, regions))

        translator._text_translator.translate_batch.assert_called_once_with(["hello"])
        translator._renderer.render_translations.assert_called_once()

    def test_report_with_callback(self):
        """Should call callback when provided."""
        translator = PDFTranslator()
        callback = MagicMock()

        translator._report(callback, "Testing", 1, 5)

        callback.assert_called_once_with("Testing", 1, 5)

    def test_report_without_callback(self):
        """Should not fail when callback is None."""
        translator = PDFTranslator()
        # Should not raise
        translator._report(None, "Testing", 1, 5)


class TestPDFTranslatorLogging:
    """Tests for logging methods."""

    def test_log_start(self, capsys, tmp_path):
        """Should print startup information."""
        translator = PDFTranslator()
        input_path = tmp_path / "input.pdf"
        output_path = tmp_path / "output.pdf"

        translator._log_start(input_path, output_path, "en", "hi", "all")

        captured = capsys.readouterr()
        assert "PDF Translator" in captured.out
        assert str(input_path) in captured.out
        assert str(output_path) in captured.out
        assert "en" in captured.out
        assert "hi" in captured.out

    def test_log_complete(self, capsys, tmp_path):
        """Should print completion summary."""
        translator = PDFTranslator()
        import time

        start_time = time.time() - 10  # 10 seconds ago

        translator._log_complete(start_time, 5, tmp_path / "output.pdf")

        captured = capsys.readouterr()
        assert "Complete!" in captured.out
        assert "Total time:" in captured.out

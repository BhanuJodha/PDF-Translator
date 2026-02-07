"""Tests for the CLI module."""

from unittest.mock import MagicMock, patch

import pytest

from pdf_translator.cli import create_parser, main


class TestCLIParser:
    """Tests for CLI argument parser."""

    def test_parser_requires_pdf_path(self):
        """Parser should require a PDF path."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parser_accepts_pdf_path(self):
        """Parser should accept a PDF path."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.pdf_path == "test.pdf"

    def test_parser_default_values(self):
        """Parser should have correct defaults."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf"])

        assert args.source == "en"
        assert args.target == "hi"
        assert args.pages == "all"
        assert args.dpi == 200
        assert args.batch_size == 4
        assert args.device == "auto"
        assert args.output is None

    def test_parser_custom_output(self):
        """Parser should accept custom output path."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "-o", "output.pdf"])
        assert args.output == "output.pdf"

    def test_parser_long_output(self):
        """Parser should accept --output flag."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "--output", "output.pdf"])
        assert args.output == "output.pdf"

    def test_parser_custom_languages(self):
        """Parser should accept custom language codes."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "-s", "es", "-t", "fr"])
        assert args.source == "es"
        assert args.target == "fr"

    def test_parser_long_language_flags(self):
        """Parser should accept --source and --target flags."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "--source", "de", "--target", "it"])
        assert args.source == "de"
        assert args.target == "it"

    def test_parser_page_range(self):
        """Parser should accept page range."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "-p", "1-5"])
        assert args.pages == "1-5"

    def test_parser_page_range_complex(self):
        """Parser should accept complex page ranges."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "-p", "1,3,5-10"])
        assert args.pages == "1,3,5-10"

    def test_parser_dpi(self):
        """Parser should accept DPI setting."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "-d", "300"])
        assert args.dpi == 300

    def test_parser_batch_size(self):
        """Parser should accept batch size."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "-b", "8"])
        assert args.batch_size == 8

    def test_parser_device_auto(self):
        """Parser should accept auto device."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "--device", "auto"])
        assert args.device == "auto"

    def test_parser_device_cuda(self):
        """Parser should accept cuda device."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "--device", "cuda"])
        assert args.device == "cuda"

    def test_parser_device_mps(self):
        """Parser should accept mps device."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "--device", "mps"])
        assert args.device == "mps"

    def test_parser_device_cpu(self):
        """Parser should accept cpu device."""
        parser = create_parser()
        args = parser.parse_args(["test.pdf", "--device", "cpu"])
        assert args.device == "cpu"

    def test_parser_device_invalid(self):
        """Parser should reject invalid device."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["test.pdf", "--device", "invalid"])

    def test_parser_all_options(self):
        """Parser should accept all options together."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "test.pdf",
                "-o",
                "out.pdf",
                "-s",
                "en",
                "-t",
                "hi",
                "-p",
                "1-5",
                "-d",
                "300",
                "-b",
                "8",
                "--device",
                "cpu",
            ]
        )

        assert args.pdf_path == "test.pdf"
        assert args.output == "out.pdf"
        assert args.source == "en"
        assert args.target == "hi"
        assert args.pages == "1-5"
        assert args.dpi == 300
        assert args.batch_size == 8
        assert args.device == "cpu"


class TestCLIMain:
    """Tests for CLI main function."""

    def test_file_not_found(self):
        """Should return error code for missing file."""
        result = main(["nonexistent.pdf"])
        assert result == 1

    def test_file_not_found_message(self, capsys):
        """Should print error message for missing file."""
        main(["nonexistent.pdf"])
        captured = capsys.readouterr()
        assert "Error" in captured.err or "not found" in captured.err.lower()

    def test_keyboard_interrupt(self, tmp_path):
        """Should handle keyboard interrupt gracefully."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        with patch("pdf_translator.cli.PDFTranslator") as mock_translator:
            mock_translator.return_value.translate.side_effect = KeyboardInterrupt()
            result = main([str(pdf_file)])
            assert result == 130

    def test_keyboard_interrupt_message(self, tmp_path, capsys):
        """Should print interrupted message."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        with patch("pdf_translator.cli.PDFTranslator") as mock_translator:
            mock_translator.return_value.translate.side_effect = KeyboardInterrupt()
            main([str(pdf_file)])

        captured = capsys.readouterr()
        assert "Interrupted" in captured.out

    @patch("pdf_translator.cli.PDFTranslator")
    def test_successful_translation(self, mock_translator_class, tmp_path):
        """Should return 0 on successful translation."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_instance = MagicMock()
        mock_instance.translate.return_value = tmp_path / "output.pdf"
        mock_translator_class.return_value = mock_instance

        result = main([str(pdf_file)])
        assert result == 0

    @patch("pdf_translator.cli.PDFTranslator")
    def test_successful_translation_message(
        self, mock_translator_class, tmp_path, capsys
    ):
        """Should print success message."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_instance = MagicMock()
        output_path = tmp_path / "output.pdf"
        mock_instance.translate.return_value = output_path
        mock_translator_class.return_value = mock_instance

        main([str(pdf_file)])

        captured = capsys.readouterr()
        assert "Translated" in captured.out or str(output_path) in captured.out

    @patch("pdf_translator.cli.PDFTranslator")
    def test_value_error_handling(self, mock_translator_class, tmp_path):
        """Should handle ValueError gracefully."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_instance = MagicMock()
        mock_instance.translate.side_effect = ValueError("No valid pages")
        mock_translator_class.return_value = mock_instance

        result = main([str(pdf_file)])
        assert result == 1

    @patch("pdf_translator.cli.PDFTranslator")
    def test_generic_exception_handling(self, mock_translator_class, tmp_path):
        """Should handle generic exceptions gracefully."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_instance = MagicMock()
        mock_instance.translate.side_effect = RuntimeError("Something went wrong")
        mock_translator_class.return_value = mock_instance

        result = main([str(pdf_file)])
        assert result == 1

    @patch("pdf_translator.cli.PDFTranslator")
    def test_passes_correct_config(self, mock_translator_class, tmp_path):
        """Should pass correct config to translator."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_instance = MagicMock()
        mock_instance.translate.return_value = tmp_path / "output.pdf"
        mock_translator_class.return_value = mock_instance

        main(
            [
                str(pdf_file),
                "-s",
                "es",
                "-t",
                "fr",
                "-d",
                "300",
                "-b",
                "8",
                "--device",
                "cpu",
            ]
        )

        # Check config was created correctly
        call_args = mock_translator_class.call_args
        config = call_args[0][0]
        assert config.source_lang == "es"
        assert config.target_lang == "fr"
        assert config.dpi == 300
        assert config.ocr_batch_size == 8
        assert config.device == "cpu"

    @patch("pdf_translator.cli.PDFTranslator")
    def test_passes_page_range(self, mock_translator_class, tmp_path):
        """Should pass page range to translate method."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_instance = MagicMock()
        mock_instance.translate.return_value = tmp_path / "output.pdf"
        mock_translator_class.return_value = mock_instance

        main([str(pdf_file), "-p", "1-5"])

        mock_instance.translate.assert_called_once()
        call_kwargs = mock_instance.translate.call_args[1]
        assert call_kwargs["page_range"] == "1-5"

    def test_non_pdf_warning(self, tmp_path, capsys):
        """Should warn about non-PDF extension."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")

        with patch("pdf_translator.cli.PDFTranslator") as mock_translator:
            mock_instance = MagicMock()
            mock_instance.translate.return_value = tmp_path / "output.pdf"
            mock_translator.return_value = mock_instance

            main([str(txt_file)])

        captured = capsys.readouterr()
        assert "Warning" in captured.out


class TestCLIMainFunction:
    """Tests for main function edge cases."""

    def test_main_with_empty_list(self, capsys):
        """Should handle empty argument list gracefully."""
        # Empty list should trigger argparse error, which we catch
        with pytest.raises(SystemExit) as exc_info:
            # argparse calls sys.exit(2) for missing required args
            main([])
        # argparse exits with 2 for argument errors
        assert exc_info.value.code == 2

    @patch("pdf_translator.cli.PDFTranslator")
    def test_main_with_custom_output(self, mock_translator_class, tmp_path):
        """Should use custom output path."""
        pdf_file = tmp_path / "input.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        output_file = tmp_path / "custom_output.pdf"

        mock_instance = MagicMock()
        mock_instance.translate.return_value = output_file
        mock_translator_class.return_value = mock_instance

        main([str(pdf_file), "-o", str(output_file)])

        call_kwargs = mock_instance.translate.call_args[1]
        assert call_kwargs["output_path"] == str(output_file)

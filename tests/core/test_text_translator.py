"""Tests for text translation module."""

from unittest.mock import MagicMock, patch

from pdf_translator.core.text_translator import TextTranslator


class TestTextTranslatorInit:
    """Tests for TextTranslator initialization."""

    def test_default_languages(self):
        """Should default to English -> Hindi."""
        translator = TextTranslator()
        assert translator.source_lang == "en"
        assert translator.target_lang == "hi"

    def test_custom_languages(self):
        """Should accept custom languages."""
        translator = TextTranslator(source_lang="es", target_lang="fr")
        assert translator.source_lang == "es"
        assert translator.target_lang == "fr"


class TestTextTranslatorShouldSkip:
    """Tests for the _should_skip method."""

    def test_skip_empty_string(self):
        """Empty string should be skipped."""
        translator = TextTranslator()
        assert translator._should_skip("")

    def test_skip_whitespace_only(self):
        """Whitespace-only should be skipped."""
        translator = TextTranslator()
        assert translator._should_skip(" ")
        assert translator._should_skip("  ")
        assert translator._should_skip("\t")

    def test_skip_single_char(self):
        """Single character should be skipped."""
        translator = TextTranslator()
        assert translator._should_skip("a")
        assert translator._should_skip("1")

    def test_skip_pure_numbers(self):
        """Pure numbers should be skipped."""
        translator = TextTranslator()
        assert translator._should_skip("123")
        assert translator._should_skip("42")
        assert translator._should_skip("0")

    def test_not_skip_alphanumeric(self):
        """Alphanumeric text should not be skipped."""
        translator = TextTranslator()
        assert not translator._should_skip("123abc")
        assert not translator._should_skip("test123")

    def test_not_skip_normal_text(self):
        """Normal text should not be skipped."""
        translator = TextTranslator()
        assert not translator._should_skip("hello")
        assert not translator._should_skip("Hello World")
        assert not translator._should_skip("ab")


class TestTextTranslatorBatch:
    """Tests for batch translation."""

    def test_empty_batch(self):
        """Empty input should return empty output."""
        translator = TextTranslator()
        result = translator.translate_batch([])
        assert result == []

    def test_all_skippable_batch(self):
        """Batch with only skippable items should return them unchanged."""
        translator = TextTranslator()
        result = translator.translate_batch(["1", "2", "a", ""])
        assert result == ["1", "2", "a", ""]

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_batch_translation_success(self, mock_translator_class):
        """Batch translation should call the API correctly."""
        mock_instance = MagicMock()
        mock_instance.translate_batch.return_value = ["hola", "mundo"]
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator(source_lang="en", target_lang="es")
        result = translator.translate_batch(["hello", "world"])

        assert result == ["hola", "mundo"]
        mock_instance.translate_batch.assert_called_once_with(["hello", "world"])

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_mixed_batch(self, mock_translator_class):
        """Batch with skippable items should handle them correctly."""
        mock_instance = MagicMock()
        mock_instance.translate_batch.return_value = ["hola"]
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator(source_lang="en", target_lang="es")
        result = translator.translate_batch(["hello", "5", ""])

        assert result[0] == "hola"
        assert result[1] == "5"
        assert result[2] == ""

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_batch_with_none_result(self, mock_translator_class):
        """Should handle None results from API."""
        mock_instance = MagicMock()
        mock_instance.translate_batch.return_value = [None, "mundo"]
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator()
        result = translator.translate_batch(["hello", "world"])

        # None should fall back to original
        assert result[0] == "hello"
        assert result[1] == "mundo"

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_fallback_on_batch_failure(self, mock_translator_class, capsys):
        """Should fall back to individual translation if batch fails."""
        mock_instance = MagicMock()
        mock_instance.translate_batch.side_effect = Exception("API error")
        mock_instance.translate.side_effect = ["hola", "mundo"]
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator()
        translator.translate_batch(["hello", "world"])

        assert mock_instance.translate.call_count == 2
        captured = capsys.readouterr()
        assert "Batch translation failed" in captured.out

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_individual_fallback_handles_errors(self, mock_translator_class):
        """Individual fallback should handle per-item errors."""
        mock_instance = MagicMock()
        mock_instance.translate_batch.side_effect = Exception("API error")
        mock_instance.translate.side_effect = [Exception("fail"), "mundo"]
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator()
        result = translator.translate_batch(["hello", "world"])

        # First should fall back to original, second should translate
        assert result[0] == "hello"
        assert result[1] == "mundo"


class TestTextTranslatorSingle:
    """Tests for single text translation."""

    def test_translate_skippable(self):
        """Skippable text should be returned unchanged."""
        translator = TextTranslator()
        assert translator.translate("1") == "1"
        assert translator.translate("") == ""

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_translate_success(self, mock_translator_class):
        """Single translation should work."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "hola"
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator()
        result = translator.translate("hello")

        assert result == "hola"

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_translate_returns_none(self, mock_translator_class):
        """Should handle None result from API."""
        mock_instance = MagicMock()
        mock_instance.translate.return_value = None
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator()
        result = translator.translate("hello")

        assert result == "hello"  # Falls back to original

    @patch("pdf_translator.core.text_translator.GoogleTranslator")
    def test_translate_handles_error(self, mock_translator_class):
        """Should handle API errors gracefully."""
        mock_instance = MagicMock()
        mock_instance.translate.side_effect = Exception("API error")
        mock_translator_class.return_value = mock_instance

        translator = TextTranslator()
        result = translator.translate("hello")

        assert result == "hello"  # Falls back to original

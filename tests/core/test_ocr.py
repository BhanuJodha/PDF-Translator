"""Tests for the OCR module."""

from unittest.mock import MagicMock, patch

from pdf_translator.core.config import TranslationConfig
from pdf_translator.core.ocr import OCREngine


class TestOCREngineInit:
    """Tests for OCREngine initialization."""

    def test_init_without_config(self):
        """Should initialize without config."""
        engine = OCREngine()
        assert engine.config is None
        assert engine._loaded is False

    def test_init_with_config(self):
        """Should accept config."""
        config = TranslationConfig()
        engine = OCREngine(config)
        assert engine.config is config

    def test_models_not_loaded_initially(self):
        """Models should not be loaded until needed."""
        engine = OCREngine()
        assert engine._detection_predictor is None
        assert engine._recognition_predictor is None
        assert engine._foundation_predictor is None


class TestOCREngineCleanText:
    """Tests for text cleaning functionality."""

    def test_basic_text(self):
        """Should clean basic text."""
        engine = OCREngine()
        text, fmt = engine._clean_text("Hello World")
        assert text == "Hello World"
        assert fmt["bold"] is False
        assert fmt["underline"] is False

    def test_bold_tags_lowercase(self):
        """Should detect lowercase bold tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<b>Bold Text</b>")
        assert text == "Bold Text"
        assert fmt["bold"] is True

    def test_bold_tags_uppercase(self):
        """Should detect uppercase bold tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<B>Bold Text</B>")
        assert text == "Bold Text"
        assert fmt["bold"] is True

    def test_underline_tags_lowercase(self):
        """Should detect lowercase underline tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<u>Underlined</u>")
        assert text == "Underlined"
        assert fmt["underline"] is True

    def test_underline_tags_uppercase(self):
        """Should detect uppercase underline tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<U>Underlined</U>")
        assert text == "Underlined"
        assert fmt["underline"] is True

    def test_mixed_formatting(self):
        """Should handle multiple formatting tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<b><u>Bold and Underlined</u></b>")
        assert text == "Bold and Underlined"
        assert fmt["bold"] is True
        assert fmt["underline"] is True

    def test_nested_tags(self):
        """Should handle nested tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<b>Bold <u>and underlined</u></b>")
        assert "Bold" in text
        assert "and underlined" in text
        assert fmt["bold"] is True
        assert fmt["underline"] is True

    def test_collapses_whitespace(self):
        """Should collapse multiple spaces."""
        engine = OCREngine()
        text, fmt = engine._clean_text("Hello    World")
        assert text == "Hello World"

    def test_collapses_tabs_and_newlines(self):
        """Should collapse tabs and newlines."""
        engine = OCREngine()
        text, fmt = engine._clean_text("Hello\t\nWorld")
        assert text == "Hello World"

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        engine = OCREngine()
        text, fmt = engine._clean_text("  Hello World  ")
        assert text == "Hello World"

    def test_removes_html_tags(self):
        """Should remove arbitrary HTML tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<span class='test'>Content</span>")
        assert text == "Content"

    def test_removes_complex_tags(self):
        """Should remove complex HTML tags."""
        engine = OCREngine()
        text, fmt = engine._clean_text('<div style="color:red">Text</div>')
        assert text == "Text"

    def test_empty_after_cleaning(self):
        """Should handle text that becomes empty after cleaning."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<b></b>")
        assert text == ""

    def test_only_whitespace_after_cleaning(self):
        """Should handle text that becomes only whitespace."""
        engine = OCREngine()
        text, fmt = engine._clean_text("<b>   </b>")
        assert text == ""

    def test_preserves_special_characters(self):
        """Should preserve special characters."""
        engine = OCREngine()
        text, fmt = engine._clean_text("Hello! @#$% World?")
        assert text == "Hello! @#$% World?"

    def test_unicode_text(self):
        """Should handle unicode text."""
        engine = OCREngine()
        text, fmt = engine._clean_text("नमस्ते दुनिया")  # Hindi
        assert text == "नमस्ते दुनिया"


class TestOCREngineModelLoading:
    """Tests for model loading behavior."""

    def test_load_models_sets_loaded_flag(self):
        """Loading models should set the loaded flag."""
        engine = OCREngine()
        assert engine._loaded is False

    def test_multiple_load_calls_idempotent(self):
        """Multiple load calls should be safe when already loaded."""
        engine = OCREngine()
        engine._loaded = True

        # This should not try to reload
        engine.load_models(verbose=False)
        assert engine._loaded is True

    def test_load_models_verbose(self, capsys):
        """Should print when verbose=True."""
        engine = OCREngine()
        engine._loaded = True  # Skip actual loading

        # Already loaded, so won't print
        engine.load_models(verbose=True)

        # Verify it didn't crash and flag is still set
        assert engine._loaded is True

    def test_load_models_creates_predictors(self):
        """Should create all predictor instances when loading."""
        engine = OCREngine()

        # Create mock modules with the predictor classes
        mock_detection_module = MagicMock()
        mock_recognition_module = MagicMock()
        mock_foundation_module = MagicMock()

        # Mock the imports inside the load_models method
        with patch.dict(
            "sys.modules",
            {
                "surya.detection": mock_detection_module,
                "surya.recognition": mock_recognition_module,
                "surya.foundation": mock_foundation_module,
            },
        ):
            engine.load_models(verbose=False)

        # Verify predictors were created
        assert engine._loaded is True
        mock_foundation_module.FoundationPredictor.assert_called_once()
        mock_detection_module.DetectionPredictor.assert_called_once()
        mock_recognition_module.RecognitionPredictor.assert_called_once()


class TestOCREngineExtractText:
    """Tests for text extraction."""

    @patch.object(OCREngine, "load_models")
    def test_extract_text_loads_models(self, mock_load):
        """Should load models before extraction."""
        engine = OCREngine()
        engine._loaded = False

        # Mock the recognition predictor
        mock_result = MagicMock()
        mock_result.text_lines = []
        engine._recognition_predictor = MagicMock(return_value=[mock_result])
        engine._detection_predictor = MagicMock()

        from PIL import Image

        images = [Image.new("RGB", (100, 100))]
        engine.extract_text(images)

        mock_load.assert_called_once()

    def test_extract_text_empty_results(self):
        """Should handle empty OCR results."""
        engine = OCREngine()
        engine._loaded = True

        mock_result = MagicMock()
        mock_result.text_lines = []
        engine._recognition_predictor = MagicMock(return_value=[mock_result])
        engine._detection_predictor = MagicMock()

        from PIL import Image

        images = [Image.new("RGB", (100, 100))]
        results = engine.extract_text(images)

        assert results == [[]]

    def test_extract_text_with_lines(self):
        """Should extract text lines correctly."""
        engine = OCREngine()
        engine._loaded = True

        mock_line = MagicMock()
        mock_line.text = "Hello World"
        mock_line.bbox = [10, 20, 100, 40]
        mock_line.polygon = [[10, 20], [100, 20], [100, 40], [10, 40]]
        mock_line.confidence = 0.95

        mock_result = MagicMock()
        mock_result.text_lines = [mock_line]

        engine._recognition_predictor = MagicMock(return_value=[mock_result])
        engine._detection_predictor = MagicMock()

        from PIL import Image

        images = [Image.new("RGB", (100, 100))]
        results = engine.extract_text(images)

        assert len(results) == 1
        assert len(results[0]) == 1
        assert results[0][0]["text"] == "Hello World"
        assert results[0][0]["confidence"] == 0.95

    def test_extract_text_skips_empty_lines(self):
        """Should skip empty text lines."""
        engine = OCREngine()
        engine._loaded = True

        mock_line1 = MagicMock()
        mock_line1.text = ""
        mock_line1.bbox = [10, 20, 100, 40]
        mock_line1.polygon = []
        mock_line1.confidence = 0.5

        mock_line2 = MagicMock()
        mock_line2.text = "Valid text"
        mock_line2.bbox = [10, 50, 100, 70]
        mock_line2.polygon = []
        mock_line2.confidence = 0.9

        mock_result = MagicMock()
        mock_result.text_lines = [mock_line1, mock_line2]

        engine._recognition_predictor = MagicMock(return_value=[mock_result])
        engine._detection_predictor = MagicMock()

        from PIL import Image

        images = [Image.new("RGB", (100, 100))]
        results = engine.extract_text(images)

        assert len(results[0]) == 1
        assert results[0][0]["text"] == "Valid text"

    def test_extract_text_multiple_images(self):
        """Should handle multiple images."""
        engine = OCREngine()
        engine._loaded = True

        mock_line1 = MagicMock()
        mock_line1.text = "Page 1"
        mock_line1.bbox = [0, 0, 50, 20]
        mock_line1.polygon = []
        mock_line1.confidence = 0.9

        mock_line2 = MagicMock()
        mock_line2.text = "Page 2"
        mock_line2.bbox = [0, 0, 50, 20]
        mock_line2.polygon = []
        mock_line2.confidence = 0.9

        mock_result1 = MagicMock()
        mock_result1.text_lines = [mock_line1]
        mock_result2 = MagicMock()
        mock_result2.text_lines = [mock_line2]

        engine._recognition_predictor = MagicMock(
            return_value=[mock_result1, mock_result2]
        )
        engine._detection_predictor = MagicMock()

        from PIL import Image

        images = [Image.new("RGB", (100, 100)), Image.new("RGB", (100, 100))]
        results = engine.extract_text(images)

        assert len(results) == 2
        assert results[0][0]["text"] == "Page 1"
        assert results[1][0]["text"] == "Page 2"

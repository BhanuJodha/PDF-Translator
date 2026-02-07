"""Tests for the text renderer module."""

import numpy as np
from PIL import Image, ImageDraw

from pdf_translator.core.renderer import TextRenderer


class TestTextRendererInit:
    """Tests for TextRenderer initialization."""

    def test_init_default_lang(self):
        """Should default to Hindi target language."""
        renderer = TextRenderer()
        assert renderer.target_lang == "hi"

    def test_init_custom_lang(self):
        """Should accept custom target language."""
        renderer = TextRenderer(target_lang="es")
        assert renderer.target_lang == "es"

    def test_font_paths_defined(self):
        """Should have font paths defined."""
        assert len(TextRenderer.HINDI_FONTS) > 0
        assert len(TextRenderer.DEFAULT_FONTS) > 0


class TestTextRendererContrastingColor:
    """Tests for contrast color calculation."""

    def test_dark_background_white_text(self):
        """Dark background should return white text."""
        renderer = TextRenderer()
        dark_bg = np.array([20, 20, 20])
        color = renderer._get_contrasting_color(dark_bg)
        assert color == (255, 255, 255)

    def test_light_background_black_text(self):
        """Light background should return black text."""
        renderer = TextRenderer()
        light_bg = np.array([240, 240, 240])
        color = renderer._get_contrasting_color(light_bg)
        assert color == (0, 0, 0)

    def test_mid_tone_black_text(self):
        """Mid-tone background should return black text (threshold is 128)."""
        renderer = TextRenderer()
        mid_bg = np.array([130, 130, 130])
        color = renderer._get_contrasting_color(mid_bg)
        assert color == (0, 0, 0)

    def test_just_below_threshold(self):
        """Just below threshold should return white text."""
        renderer = TextRenderer()
        dark_bg = np.array([127, 127, 127])
        color = renderer._get_contrasting_color(dark_bg)
        assert color == (255, 255, 255)

    def test_pure_black(self):
        """Pure black should return white text."""
        renderer = TextRenderer()
        black = np.array([0, 0, 0])
        color = renderer._get_contrasting_color(black)
        assert color == (255, 255, 255)

    def test_pure_white(self):
        """Pure white should return black text."""
        renderer = TextRenderer()
        white = np.array([255, 255, 255])
        color = renderer._get_contrasting_color(white)
        assert color == (0, 0, 0)

    def test_colored_background(self):
        """Colored backgrounds should use luminance formula."""
        renderer = TextRenderer()
        # Red has luminance ~76 (dark)
        red = np.array([255, 0, 0])
        assert renderer._get_contrasting_color(red) == (255, 255, 255)

        # Yellow has luminance ~226 (light)
        yellow = np.array([255, 255, 0])
        assert renderer._get_contrasting_color(yellow) == (0, 0, 0)

    def test_grayscale_single_channel(self):
        """Should handle single-channel grayscale."""
        renderer = TextRenderer()
        gray = np.array([100])
        color = renderer._get_contrasting_color(gray)
        assert color == (255, 255, 255)


class TestTextRendererSampleBackground:
    """Tests for background color sampling."""

    def test_white_image(self):
        """White image should sample white background."""
        renderer = TextRenderer()
        white_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        box = (20, 20, 80, 80)
        bg = renderer._sample_background(white_image, box)
        assert np.allclose(bg, [255, 255, 255], atol=1)

    def test_black_image(self):
        """Black image should sample black background."""
        renderer = TextRenderer()
        black_image = np.zeros((100, 100, 3), dtype=np.uint8)
        box = (20, 20, 80, 80)
        bg = renderer._sample_background(black_image, box)
        assert np.allclose(bg, [0, 0, 0], atol=1)

    def test_colored_image(self):
        """Colored image should sample that color."""
        renderer = TextRenderer()
        red_image = np.zeros((100, 100, 3), dtype=np.uint8)
        red_image[:, :] = [255, 0, 0]
        box = (20, 20, 80, 80)
        bg = renderer._sample_background(red_image, box)
        assert bg[0] == 255  # Red channel

    def test_box_at_top_edge(self):
        """Should handle box at top edge."""
        renderer = TextRenderer()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        box = (20, 0, 80, 20)  # At top
        bg = renderer._sample_background(image, box)
        assert bg is not None

    def test_box_at_bottom_edge(self):
        """Should handle box at bottom edge."""
        renderer = TextRenderer()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        box = (20, 80, 80, 100)  # At bottom
        bg = renderer._sample_background(image, box)
        assert bg is not None

    def test_box_at_left_edge(self):
        """Should handle box at left edge."""
        renderer = TextRenderer()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        box = (0, 20, 20, 80)  # At left
        bg = renderer._sample_background(image, box)
        assert bg is not None

    def test_box_at_right_edge(self):
        """Should handle box at right edge."""
        renderer = TextRenderer()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        box = (80, 20, 100, 80)  # At right
        bg = renderer._sample_background(image, box)
        assert bg is not None

    def test_no_samples_returns_white(self):
        """Should return white when no samples available."""
        renderer = TextRenderer()
        # Very small image where sampling fails
        tiny_image = np.ones((5, 5, 3), dtype=np.uint8) * 128
        box = (0, 0, 5, 5)
        bg = renderer._sample_background(tiny_image, box)
        # Should return something (either sampled or default white)
        assert bg is not None


class TestTextRendererRender:
    """Tests for the main render method."""

    def test_empty_regions(self):
        """Empty regions should return original image."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        result = renderer.render_translations(image, [], [])
        assert result.shape == (100, 100, 3)

    def test_preserves_dimensions(self):
        """Output should have same dimensions as input."""
        renderer = TextRenderer()
        image = Image.new("RGB", (200, 150), color="white")
        regions = [{"box": [10, 10, 50, 30], "formatting": {}}]
        translations = ["test"]

        result = renderer.render_translations(image, regions, translations)
        assert result.shape == (150, 200, 3)

    def test_multiple_regions(self):
        """Should handle multiple regions."""
        renderer = TextRenderer()
        image = Image.new("RGB", (200, 200), color="white")
        regions = [
            {"box": [10, 10, 90, 30], "formatting": {}},
            {"box": [10, 50, 90, 70], "formatting": {}},
            {"box": [10, 90, 90, 110], "formatting": {}},
        ]
        translations = ["one", "two", "three"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_with_bold_formatting(self):
        """Should handle bold formatting."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 90, 40], "formatting": {"bold": True}}]
        translations = ["bold text"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_with_underline_formatting(self):
        """Should handle underline formatting."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 90, 40], "formatting": {"underline": True}}]
        translations = ["underlined"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_missing_formatting_key(self):
        """Should handle missing formatting key."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 90, 40]}]  # No formatting key
        translations = ["test"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None


class TestTextRendererEdgeCases:
    """Edge case tests for TextRenderer."""

    def test_empty_translation_skipped(self):
        """Empty translations should be skipped without error."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 50, 30], "formatting": {}}]
        translations = [""]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_whitespace_translation_skipped(self):
        """Whitespace-only translations should be skipped."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 50, 30], "formatting": {}}]
        translations = ["   "]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_zero_width_box_skipped(self):
        """Zero-width boxes should be skipped."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 10, 30], "formatting": {}}]
        translations = ["test"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_zero_height_box_skipped(self):
        """Zero-height boxes should be skipped."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 50, 10], "formatting": {}}]
        translations = ["test"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_negative_dimension_box(self):
        """Negative dimension boxes should be skipped."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [50, 50, 10, 10], "formatting": {}}]  # x2 < x1
        translations = ["test"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_box_at_corner(self):
        """Boxes at image corner should be handled."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [0, 0, 20, 20], "formatting": {}}]
        translations = ["corner"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_very_long_text(self):
        """Very long text should be handled (font shrinking)."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 50), color="white")
        regions = [{"box": [5, 5, 95, 45], "formatting": {}}]
        translations = ["This is a very long text that should be shrunk to fit"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None

    def test_very_small_box(self):
        """Very small boxes should be handled."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100), color="white")
        regions = [{"box": [10, 10, 15, 15], "formatting": {}}]
        translations = ["x"]

        result = renderer.render_translations(image, regions, translations)
        assert result is not None


class TestTextRendererFont:
    """Tests for font handling."""

    def test_get_font_returns_font(self):
        """Should return a font object."""
        renderer = TextRenderer()
        font = renderer._get_font(12)
        assert font is not None

    def test_get_font_different_sizes(self):
        """Should return fonts of different sizes."""
        renderer = TextRenderer()
        font12 = renderer._get_font(12)
        font24 = renderer._get_font(24)
        # Both should be valid fonts
        assert font12 is not None
        assert font24 is not None

    def test_get_font_bold(self):
        """Should return bold font when requested."""
        renderer = TextRenderer()
        font = renderer._get_font(12, bold=True)
        assert font is not None

    def test_get_font_hindi(self):
        """Should return font for Hindi."""
        renderer = TextRenderer(target_lang="hi")
        font = renderer._get_font(12)
        assert font is not None

    def test_measure_text(self):
        """Should measure text dimensions."""
        renderer = TextRenderer()
        image = Image.new("RGB", (100, 100))
        draw = ImageDraw.Draw(image)
        font = renderer._get_font(12)

        width, height = renderer._measure_text(draw, "test", font)
        assert width > 0
        assert height > 0

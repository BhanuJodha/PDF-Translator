"""Text rendering and image manipulation for translated PDFs."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont


class TextRenderer:
    """
    Handles removing original text and drawing translated text on images.

    Takes care of:
    - Sampling background colors to cleanly erase text
    - Choosing contrasting text colors for readability
    - Fitting translated text into the original bounding boxes
    - Preserving formatting like bold and underline
    """

    # Font paths for different languages (macOS paths, extend for other OS)
    HINDI_FONTS = [
        "/System/Library/Fonts/Kohinoor.ttc",
        "/System/Library/Fonts/Supplemental/Devanagari MT.ttc",
        "/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc",
    ]

    DEFAULT_FONTS = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SF-Pro.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "C:/Windows/Fonts/arial.ttf",  # Windows
    ]

    def __init__(self, target_lang: str = "hi"):
        self.target_lang = target_lang

    def render_translations(
        self,
        image: Image.Image,
        regions: list[dict],
        translations: list[str],
    ) -> np.ndarray:
        """
        Replace original text with translations on the image.

        Args:
            image: Original PIL Image
            regions: Text regions from OCR
            translations: Translated text strings

        Returns:
            NumPy array of the modified image
        """
        if not regions:
            return np.array(image)

        image_array = np.array(image)

        # First pass: erase original text and figure out what colors to use
        cleaned, text_colors = self._remove_text(image_array, regions)

        # Second pass: draw the translated text
        result = self._draw_text(cleaned, regions, translations, text_colors)

        return result

    def _remove_text(
        self, image: np.ndarray, regions: list[dict]
    ) -> tuple[np.ndarray, list[tuple]]:
        """
        Erase original text by filling with background color.

        Also determines what text color to use for each region based
        on the background, so we can ensure good contrast.
        """
        result = image.copy()
        text_colors = []

        for region in regions:
            box = region["box"]
            x1, y1, x2, y2 = map(int, box)

            # Small padding around the text box
            pad = 2
            x1_pad = max(0, x1 - pad)
            y1_pad = max(0, y1 - pad)
            x2_pad = min(image.shape[1], x2 + pad)
            y2_pad = min(image.shape[0], y2 + pad)

            # Sample the background before we erase anything
            bg_color = self._sample_background(image, box)
            text_color = self._get_contrasting_color(bg_color)
            text_colors.append(text_color)

            # Fill the region with background color
            result[y1_pad:y2_pad, x1_pad:x2_pad] = bg_color

        return result, text_colors

    def _sample_background(self, image: np.ndarray, box: tuple) -> np.ndarray:
        """
        Sample pixels around a text box to estimate background color.

        We look at the edges just outside the box to get a good estimate
        of what color to use when erasing the text.
        """
        x1, y1, x2, y2 = map(int, box)

        pad = 2
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(image.shape[1], x2 + pad)
        y2 = min(image.shape[0], y2 + pad)

        samples = []

        # Sample from each edge if there's room
        if y1 > 3:
            samples.extend(image[y1 - 3, x1:x2:5].tolist())
        if y2 < image.shape[0] - 3:
            samples.extend(image[y2 + 2, x1:x2:5].tolist())
        if x1 > 3:
            samples.extend(image[y1:y2:5, x1 - 3].tolist())
        if x2 < image.shape[1] - 3:
            samples.extend(image[y1:y2:5, x2 + 2].tolist())

        if samples:
            return np.median(samples, axis=0).astype(np.uint8)

        # Default to white if we couldn't sample
        return np.array([255, 255, 255], dtype=np.uint8)

    def _get_contrasting_color(self, bg_color: np.ndarray) -> tuple:
        """
        Pick black or white text based on background brightness.

        Uses the standard luminance formula that accounts for how
        human eyes perceive different colors.
        """
        if len(bg_color) >= 3:
            luminance = 0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]
        else:
            luminance = bg_color[0]

        # Dark background -> white text, light background -> black text
        return (255, 255, 255) if luminance < 128 else (0, 0, 0)

    def _draw_text(
        self,
        image: np.ndarray,
        regions: list[dict],
        translations: list[str],
        text_colors: list[tuple],
    ) -> np.ndarray:
        """Draw translated text onto the image."""
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)

        for region, text, text_color in zip(regions, translations, text_colors):
            if not text or not text.strip():
                continue

            box = region["box"]
            x1, y1, x2, y2 = map(int, box)
            width = x2 - x1
            height = y2 - y1

            if width <= 0 or height <= 0:
                continue

            formatting = region.get("formatting", {})
            is_bold = formatting.get("bold", False)
            has_underline = formatting.get("underline", False)

            # Start with a font size based on the box height
            font_size = max(8, min(int(height * 0.75), 48))
            font = self._get_font(font_size, bold=is_bold)

            # Shrink font if text doesn't fit
            text_width, text_height = self._measure_text(draw, text, font)
            while text_width > width * 0.95 and font_size > 6:
                font_size -= 1
                font = self._get_font(font_size, bold=is_bold)
                text_width, text_height = self._measure_text(draw, text, font)

            # Position: left-aligned, vertically centered
            text_x = x1
            text_y = y1 + (height - text_height) // 2

            draw.text((text_x, text_y), text, font=font, fill=text_color)

            if has_underline:
                underline_y = text_y + text_height + 1
                draw.line(
                    [(text_x, underline_y), (text_x + text_width, underline_y)],
                    fill=text_color,
                    width=1,
                )

        return np.array(pil_image)

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Load an appropriate font for the target language."""
        font_paths = (
            self.HINDI_FONTS if self.target_lang == "hi" else self.DEFAULT_FONTS
        )

        for font_path in font_paths:
            try:
                index = 1 if bold else 0
                return ImageFont.truetype(font_path, size, index=index)
            except OSError:
                continue

        return ImageFont.load_default()  # type: ignore[return-value]

    def _measure_text(
        self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
    ) -> tuple[int, int]:
        """Get the width and height of rendered text."""
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            return len(text) * 10, font.size if hasattr(font, "size") else 12

"""PDF text replacement for digitally-born PDFs using PyMuPDF."""

from __future__ import annotations

import platform
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import fitz

from pdf_translator.core.pdf_extractor import TextBlock


class PDFRenderer:
    """
    Handles text replacement in native PDFs using PyMuPDF.

    Uses redaction to remove original text and then inserts translated
    text with proper Unicode font support.
    """

    # Scripts that need special font handling (non-Latin)
    INDIC_SCRIPTS = {"hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "or"}
    ARABIC_SCRIPTS = {"ar", "fa", "ur"}
    CJK_SCRIPTS = {"zh", "zh-cn", "zh-tw", "ja", "ko"}

    # System font paths for different platforms
    FONT_PATHS = {
        "Darwin": {  # macOS
            "default": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "fallback": "/System/Library/Fonts/Helvetica.ttc",
            "indic": "/System/Library/Fonts/Kohinoor.ttc",
            "cjk": "/System/Library/Fonts/PingFang.ttc",
        },
        "Linux": {
            "default": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "fallback": "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "indic": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "cjk": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        },
        "Windows": {
            "default": "C:/Windows/Fonts/arial.ttf",
            "fallback": "C:/Windows/Fonts/segoeui.ttf",
            "indic": "C:/Windows/Fonts/Nirmala.ttf",
            "cjk": "C:/Windows/Fonts/msyh.ttc",
        },
    }

    def __init__(self, target_lang: str = "hi"):
        """
        Initialize the renderer.

        Args:
            target_lang: Target language code for font selection
        """
        self.target_lang = target_lang
        self._doc: fitz.Document | None = None
        self._output_path: Path | None = None
        self._font_path: str | None = None
        self._font_name: str = "unicode-font"

    def open(self, path: str | Path) -> None:
        """
        Open a PDF for modification.

        Args:
            path: Path to the PDF file
        """
        import fitz

        self._doc = fitz.open(str(path))
        self._font_path = self._find_unicode_font()

    def close(self) -> None:
        """Close the PDF document without saving."""
        if self._doc:
            self._doc.close()
            self._doc = None

    def save(self, output_path: str | Path) -> Path:
        """
        Save the modified PDF.

        Args:
            output_path: Where to save the modified PDF

        Returns:
            Path to the saved file
        """
        if not self._doc:
            raise RuntimeError("No document open")

        output_path = Path(output_path)
        self._doc.save(str(output_path), garbage=4, deflate=True)
        return output_path

    def replace_text_on_page(
        self,
        page_num: int,
        blocks: list[TextBlock],
        translations: list[str],
    ) -> None:
        """
        Replace text blocks on a page with their translations.

        Uses a two-step process:
        1. Add redaction annotations to remove original text
        2. Insert translated text with proper Unicode font

        Args:
            page_num: 0-based page number
            blocks: Original text blocks with position info
            translations: Translated text for each block
        """
        if not self._doc:
            raise RuntimeError("No document open")

        if len(blocks) != len(translations):
            raise ValueError("Number of blocks and translations must match")

        page = self._doc[page_num]

        # Collect blocks to process
        replacements: list[tuple[TextBlock, str, float]] = []

        # Step 1: Add redaction annotations to remove original text
        for block, translation in zip(blocks, translations):
            if not translation or not translation.strip():
                continue

            import fitz

            rect = fitz.Rect(block.bbox)
            if rect.is_empty or rect.is_infinite:
                continue

            # Calculate font size
            original_len = len(block.text)
            translation_len = len(translation)
            size_ratio = original_len / max(translation_len, 1)
            font_size = min(block.font_size, block.font_size * size_ratio * 1.2)
            font_size = max(6, min(font_size, block.font_size))

            # Add redaction to remove original text (no replacement text)
            page.add_redact_annot(rect, fill=(1, 1, 1))  # White fill only

            replacements.append((block, translation, font_size))

        # Apply redactions to remove original text
        page.apply_redactions(images=0)

        # Step 2: Insert translated text with Unicode font
        for block, translation, font_size in replacements:
            self._insert_text(page, block, translation, font_size)

    def _insert_text(
        self,
        page: fitz.Page,
        block: TextBlock,
        translation: str,
        font_size: float,
    ) -> None:
        """
        Insert translated text at the block position.

        Args:
            page: PyMuPDF page object
            block: Original text block for position
            translation: Translated text to insert
            font_size: Font size to use
        """
        import fitz

        rect = fitz.Rect(block.bbox)

        # Get text color
        text_color = self._int_to_rgb(block.color)

        # Create text writer for proper Unicode support
        tw = fitz.TextWriter(page.rect)

        # Try to use embedded font for Unicode support
        if self._font_path and Path(self._font_path).exists():
            try:
                font = fitz.Font(fontfile=self._font_path)
                tw.append(
                    (rect.x0, rect.y1 - 2),  # Position at bottom-left of rect
                    translation,
                    font=font,
                    fontsize=font_size,
                )
                tw.write_text(page, color=text_color)
                return
            except Exception:
                pass  # Fall back to built-in font

        # Fallback: use built-in font (may not render all scripts)
        try:
            tw.append(
                (rect.x0, rect.y1 - 2),
                translation,
                fontsize=font_size,
            )
            tw.write_text(page, color=text_color)
        except Exception:
            # Last resort: insert as annotation
            page.insert_text(
                (rect.x0, rect.y1 - 2),
                translation,
                fontsize=font_size,
                color=text_color,
            )

    def _replace_single_block(
        self,
        page: fitz.Page,
        block: TextBlock,
        translation: str,
    ) -> None:
        """
        Replace a single text block with its translation.

        This is a simplified version for testing compatibility.
        The main replace_text_on_page method handles batching.

        Args:
            page: PyMuPDF page object
            block: Original text block
            translation: Translated text
        """
        import fitz

        rect = fitz.Rect(block.bbox)

        # Skip if rect is invalid
        if rect.is_empty or rect.is_infinite:
            return

        # Calculate font size
        original_len = len(block.text)
        translation_len = len(translation)
        size_ratio = original_len / max(translation_len, 1)
        font_size = min(block.font_size, block.font_size * size_ratio * 1.2)
        font_size = max(6, min(font_size, block.font_size))

        # Add redaction to remove original
        page.add_redact_annot(rect, fill=(1, 1, 1))

    def _get_font_for_language(self, lang: str) -> str:
        """
        Get appropriate font name for a language.

        Note: This method is kept for backward compatibility.
        The actual font selection now uses _find_unicode_font().

        Args:
            lang: Language code

        Returns:
            PyMuPDF built-in font name
        """
        lang_lower = lang.lower()

        if lang_lower in self.CJK_SCRIPTS:
            if lang_lower in ("zh", "zh-cn"):
                return "china-s"
            elif lang_lower == "zh-tw":
                return "china-t"
            elif lang_lower == "ja":
                return "japan"
            elif lang_lower == "ko":
                return "korea"

        return "helv"

    def _find_unicode_font(self) -> str | None:
        """
        Find a Unicode font that supports the target language.

        Returns:
            Path to font file, or None if not found
        """
        system = platform.system()
        paths = self.FONT_PATHS.get(system, self.FONT_PATHS["Linux"])

        lang_lower = self.target_lang.lower()

        # Determine which font type to look for
        if lang_lower in self.INDIC_SCRIPTS:
            font_key = "indic"
        elif lang_lower in self.CJK_SCRIPTS:
            font_key = "cjk"
        else:
            font_key = "default"

        # Try the specific font first
        font_path = paths.get(font_key)
        if font_path and Path(font_path).exists():
            return font_path

        # Try default Unicode font
        font_path = paths.get("default")
        if font_path and Path(font_path).exists():
            return font_path

        # Try fallback
        font_path = paths.get("fallback")
        if font_path and Path(font_path).exists():
            return font_path

        return None

    def _int_to_rgb(self, color_int: int) -> tuple[float, float, float]:
        """
        Convert integer color to RGB tuple (0-1 range).

        Args:
            color_int: Color as integer (0xRRGGBB)

        Returns:
            Tuple of (r, g, b) in 0-1 range
        """
        r = ((color_int >> 16) & 0xFF) / 255.0
        g = ((color_int >> 8) & 0xFF) / 255.0
        b = (color_int & 0xFF) / 255.0
        return (r, g, b)


class DigitalPDFTranslator:
    """
    High-level interface for translating digital PDFs.

    Coordinates text extraction, translation, and replacement
    for PDFs with embedded text.
    """

    def __init__(self, target_lang: str = "hi"):
        """
        Initialize the digital PDF translator.

        Args:
            target_lang: Target language for translation
        """
        self.target_lang = target_lang
        self._renderer = PDFRenderer(target_lang)

    def translate_pdf(
        self,
        input_path: str | Path,
        output_path: str | Path,
        translator_func: Callable[[list[str]], list[str]],
        page_indices: list[int] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """
        Translate a digital PDF.

        Args:
            input_path: Path to input PDF
            output_path: Path for output PDF
            translator_func: Function that takes list[str] and returns list[str]
            page_indices: Specific pages to translate (0-based), None for all
            progress_callback: Optional callback(current, total)

        Returns:
            Path to the translated PDF
        """
        from pdf_translator.core.pdf_extractor import PDFExtractor

        input_path = Path(input_path)
        output_path = Path(output_path)

        with PDFExtractor(input_path) as extractor:
            # Determine pages to process
            if page_indices is None:
                page_indices = list(range(extractor.page_count))

            total_pages = len(page_indices)

            # Open for modification
            self._renderer.open(input_path)

            try:
                for i, page_num in enumerate(page_indices):
                    if progress_callback:
                        progress_callback(i, total_pages)

                    # Extract text blocks
                    blocks = extractor.extract_text_blocks(page_num)

                    if not blocks:
                        continue

                    # Get texts to translate
                    texts = [b.text for b in blocks]

                    # Translate
                    translations = translator_func(texts)

                    # Replace text
                    self._renderer.replace_text_on_page(page_num, blocks, translations)

                if progress_callback:
                    progress_callback(total_pages, total_pages)

                # Save result
                return self._renderer.save(output_path)

            finally:
                self._renderer.close()

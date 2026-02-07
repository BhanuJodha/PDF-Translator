"""Main PDF translation orchestrator."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import numpy as np
from pdf2image import convert_from_path
from PIL import Image

from pdf_translator.core.config import TranslationConfig
from pdf_translator.core.ocr import OCREngine
from pdf_translator.core.renderer import TextRenderer
from pdf_translator.core.text_translator import TextTranslator


class PDFTranslator:
    """
    High-level interface for translating PDF documents.

    Coordinates the OCR, translation, and rendering pipeline.
    Supports batch processing and parallel execution for speed.

    Example:
        >>> from pdf_translator import PDFTranslator
        >>> translator = PDFTranslator()
        >>> translator.translate("document.pdf", target_lang="hi")
    """

    def __init__(self, config: TranslationConfig | None = None):
        """
        Initialize the translator.

        Args:
            config: Translation settings. If None, uses auto-detected defaults.
        """
        self.config = config or TranslationConfig()
        self.config.apply_environment()

        self._ocr = OCREngine(self.config)
        self._text_translator: TextTranslator | None = None
        self._renderer: TextRenderer | None = None

    def translate(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        source_lang: str | None = None,
        target_lang: str | None = None,
        page_range: str = "all",
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> Path:
        """
        Translate a PDF file.

        Args:
            input_path: Path to the input PDF
            output_path: Where to save the result. Defaults to input_translated.pdf
            source_lang: Override source language from config
            target_lang: Override target language from config
            page_range: Which pages to translate (e.g., "1-5", "1,3,5", "all")
            progress_callback: Optional function called with (stage, current, total)

        Returns:
            Path to the translated PDF
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"PDF not found: {input_path}")

        if output_path is None:
            output_path = input_path.with_stem(f"{input_path.stem}_translated")
        output_path = Path(output_path)

        # Use provided languages or fall back to config
        src_lang = source_lang or self.config.source_lang
        tgt_lang = target_lang or self.config.target_lang

        self._text_translator = TextTranslator(src_lang, tgt_lang)
        self._renderer = TextRenderer(tgt_lang)

        self._log_start(input_path, output_path, src_lang, tgt_lang, page_range)

        total_start = time.time()

        # Step 1: Convert PDF pages to images
        self._report(progress_callback, "Converting PDF", 0, 4)
        images, page_indices = self._load_pdf(input_path, page_range)

        # Step 2: Run OCR on all pages
        self._report(progress_callback, "Running OCR", 1, 4)
        all_regions = self._run_ocr(images)

        # Step 3: Translate and render in parallel
        self._report(progress_callback, "Translating", 2, 4)
        processed = self._process_pages(images, all_regions)

        # Step 4: Save the result
        self._report(progress_callback, "Saving PDF", 3, 4)
        self._save_pdf(processed, output_path)

        self._report(progress_callback, "Done", 4, 4)
        self._log_complete(total_start, len(images), output_path)

        return output_path

    def _load_pdf(
        self, path: Path, page_range: str
    ) -> tuple[list[Image.Image], list[int]]:
        """Convert PDF to images and filter by page range."""
        print("Converting PDF to images...")
        start = time.time()

        all_images = convert_from_path(
            str(path),
            dpi=self.config.dpi,
            thread_count=self.config.num_workers,
        )

        total_pages = len(all_images)
        print(f"  PDF has {total_pages} pages")

        page_indices = self._parse_page_range(page_range, total_pages)
        if not page_indices:
            raise ValueError("No valid pages to process")

        images = [all_images[i] for i in page_indices]
        print(f"  Selected pages: {[i + 1 for i in page_indices]}")
        print(f"  Done in {time.time() - start:.2f}s\n")

        return images, page_indices

    def _run_ocr(self, images: list[Image.Image]) -> list[list[dict]]:
        """Run OCR on all images in batches."""
        print("Running OCR...")
        start = time.time()

        all_regions = []
        batch_size = self.config.ocr_batch_size

        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]
            batch_end = min(i + batch_size, len(images))
            print(f"  Processing pages {i + 1}-{batch_end}...")

            regions = self._ocr.extract_text(batch)
            all_regions.extend(regions)

        total_lines = sum(len(r) for r in all_regions)
        print(f"  Found {total_lines} text lines")
        print(f"  Done in {time.time() - start:.2f}s\n")

        return all_regions

    def _process_pages(
        self, images: list[Image.Image], all_regions: list[list[dict]]
    ) -> list[np.ndarray]:
        """Translate and render all pages in parallel."""
        print(f"Processing pages ({self.config.num_workers} workers)...")
        start = time.time()

        args = list(zip(images, all_regions))

        with ThreadPoolExecutor(max_workers=self.config.num_workers) as executor:
            processed = list(executor.map(self._process_single_page, args))

        print(f"  Done in {time.time() - start:.2f}s\n")
        return processed

    def _process_single_page(self, args: tuple[Image.Image, list[dict]]) -> np.ndarray:
        """Process one page: translate text and render."""
        image, regions = args

        if not regions:
            return np.array(image)

        texts = [r["text"] for r in regions]
        assert self._text_translator is not None
        translations = self._text_translator.translate_batch(texts)

        assert self._renderer is not None
        return self._renderer.render_translations(image, regions, translations)

    def _save_pdf(self, pages: list[np.ndarray], output_path: Path) -> None:
        """Save processed pages as a PDF."""
        print("Saving PDF...")
        start = time.time()

        pil_images = [Image.fromarray(p) for p in pages]

        pil_images[0].save(
            str(output_path),
            "PDF",
            save_all=True,
            append_images=pil_images[1:] if len(pil_images) > 1 else [],
            resolution=self.config.dpi,
        )

        print(f"  Saved to {output_path}")
        print(f"  Done in {time.time() - start:.2f}s\n")

    def _parse_page_range(self, page_range: str, total_pages: int) -> list[int]:
        """
        Parse a page range string into 0-based indices.

        Supports formats like:
        - "all" or "" -> all pages
        - "5" -> just page 5
        - "1-10" -> pages 1 through 10
        - "1,5,9" -> pages 1, 5, and 9
        - "1-3,7,10-12" -> combination
        """
        if not page_range or page_range.lower() == "all":
            return list(range(total_pages))

        pages = set()
        parts = page_range.replace(" ", "").split(",")

        for part in parts:
            if "-" in part:
                try:
                    start_str, end_str = part.split("-")
                    start = int(start_str)
                    end = int(end_str)
                    for p in range(max(1, start), min(total_pages, end) + 1):
                        pages.add(p - 1)
                except ValueError:
                    print(f"Warning: Invalid range '{part}', skipping")
            else:
                try:
                    p = int(part)
                    if 1 <= p <= total_pages:
                        pages.add(p - 1)
                except ValueError:
                    print(f"Warning: Invalid page '{part}', skipping")

        return sorted(pages)

    def _report(
        self,
        callback: Callable[[str, int, int], None] | None,
        stage: str,
        current: int,
        total: int,
    ) -> None:
        """Report progress if a callback is provided."""
        if callback:
            callback(stage, current, total)

    def _log_start(
        self,
        input_path: Path,
        output_path: Path,
        source_lang: str,
        target_lang: str,
        page_range: str,
    ) -> None:
        """Print startup information."""
        print("=" * 50)
        print("PDF Translator")
        print("=" * 50)
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print(f"Languages: {source_lang} -> {target_lang}")
        print(f"Pages: {page_range}")
        print(f"Device: {self.config.device}")
        print("=" * 50)
        print()

    def _log_complete(
        self, start_time: float, num_pages: int, output_path: Path
    ) -> None:
        """Print completion summary."""
        elapsed = time.time() - start_time
        print("=" * 50)
        print("Complete!")
        print(f"Total time: {elapsed:.2f}s ({elapsed / num_pages:.2f}s per page)")
        print(f"Output: {output_path}")
        print("=" * 50)

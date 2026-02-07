"""OCR engine using Surya for text detection and recognition."""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    from pdf_translator.core.config import TranslationConfig


class OCREngine:
    """
    Handles text detection and recognition using Surya OCR.

    Surya provides state-of-the-art OCR with support for 90+ languages
    and works well on both printed and handwritten text.
    """

    def __init__(self, config: TranslationConfig | None = None):
        self.config = config
        self._detection_predictor = None
        self._recognition_predictor = None
        self._foundation_predictor = None
        self._loaded = False

    def load_models(self, verbose: bool = True) -> None:
        """
        Load OCR models into memory.

        This is called automatically on first use, but you can call it
        explicitly to control when the (slow) model loading happens.
        """
        if self._loaded:
            return

        if verbose:
            print("Loading Surya OCR models...")

        start = time.time()

        from surya.detection import DetectionPredictor
        from surya.foundation import FoundationPredictor
        from surya.recognition import RecognitionPredictor

        self._foundation_predictor = FoundationPredictor()
        self._detection_predictor = DetectionPredictor()
        self._recognition_predictor = RecognitionPredictor(self._foundation_predictor)

        self._loaded = True

        if verbose:
            print(f"Models loaded in {time.time() - start:.2f}s")

    def extract_text(self, images: list[Image.Image]) -> list[list[dict]]:
        """
        Extract text regions from a batch of images.

        Args:
            images: List of PIL Images to process

        Returns:
            List of text regions for each image. Each region contains:
            - text: cleaned text content
            - raw_text: original text with any HTML tags
            - box: bounding box [x1, y1, x2, y2]
            - polygon: precise polygon coordinates
            - confidence: OCR confidence score
            - formatting: dict with 'bold' and 'underline' flags
        """
        self.load_models()

        assert self._recognition_predictor is not None
        assert self._detection_predictor is not None
        results = self._recognition_predictor(
            images,
            det_predictor=self._detection_predictor,
            sort_lines=True,
        )

        all_regions = []
        for ocr_result in results:
            regions = []
            for line in ocr_result.text_lines:
                raw_text = line.text.strip()
                if not raw_text:
                    continue

                clean_text, formatting = self._clean_text(raw_text)
                if not clean_text:
                    continue

                regions.append(
                    {
                        "text": clean_text,
                        "raw_text": raw_text,
                        "box": list(line.bbox),
                        "polygon": line.polygon,
                        "confidence": line.confidence,
                        "formatting": formatting,
                    }
                )
            all_regions.append(regions)

        return all_regions

    def _clean_text(self, text: str) -> tuple[str, dict]:
        """
        Strip HTML tags and extract formatting information.

        Some OCR results include formatting tags like <b> for bold text.
        We preserve this info for rendering but remove the tags from the text.
        """
        has_bold = "<b>" in text.lower() or "</b>" in text.lower()
        has_underline = "<u>" in text.lower() or "</u>" in text.lower()

        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()

        return clean, {"bold": has_bold, "underline": has_underline}

"""Configuration management for PDF Translator."""

from __future__ import annotations

import multiprocessing as mp
import os
from dataclasses import dataclass, field
from typing import Literal

DeviceType = Literal["cuda", "mps", "cpu", "auto"]


@dataclass
class TranslationConfig:
    """
    Configuration for PDF translation.

    Attributes:
        source_lang: Source language code (e.g., 'en' for English)
        target_lang: Target language code (e.g., 'hi' for Hindi)
        device: Compute device - 'cuda' for NVIDIA GPU, 'mps' for Apple Silicon, 'cpu', or 'auto'
        dpi: Resolution for PDF rendering. Higher = better quality but slower
        ocr_batch_size: Number of pages to process in one OCR batch
        num_workers: Number of parallel workers for translation/rendering
        detector_batch_size: Batch size for text detection model
        recognition_batch_size: Batch size for text recognition model
        layout_batch_size: Batch size for layout analysis
    """

    source_lang: str = "en"
    target_lang: str = "hi"
    device: DeviceType = "auto"
    dpi: int = 200
    ocr_batch_size: int = 4
    num_workers: int = field(default_factory=lambda: max(1, mp.cpu_count() - 1))

    # Model batch sizes - tune based on your GPU memory
    detector_batch_size: int = 16
    recognition_batch_size: int = 32
    layout_batch_size: int = 8

    def __post_init__(self) -> None:
        """Validate and set up environment after initialization."""
        self._detect_device()

    def _detect_device(self) -> None:
        """Auto-detect the best available compute device."""
        if self.device == "auto":
            try:
                import torch

                if torch.cuda.is_available():
                    self.device = "cuda"
                elif (
                    hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                ):
                    self.device = "mps"
                else:
                    self.device = "cpu"
            except ImportError:
                self.device = "cpu"

    def apply_environment(self) -> None:
        """Apply configuration to environment variables for Surya OCR."""
        os.environ["TORCH_DEVICE"] = self.device
        os.environ["DETECTOR_BATCH_SIZE"] = str(self.detector_batch_size)
        os.environ["RECOGNITION_BATCH_SIZE"] = str(self.recognition_batch_size)
        os.environ["LAYOUT_BATCH_SIZE"] = str(self.layout_batch_size)
        os.environ["DETECTOR_POSTPROCESSING_CPU_WORKERS"] = str(mp.cpu_count())

    @classmethod
    def for_apple_silicon(cls) -> TranslationConfig:
        """Optimized config for Apple Silicon Macs."""
        return cls(
            device="mps",
            detector_batch_size=16,
            recognition_batch_size=32,
            layout_batch_size=8,
        )

    @classmethod
    def for_nvidia_gpu(cls) -> TranslationConfig:
        """Optimized config for NVIDIA GPUs with decent VRAM."""
        return cls(
            device="cuda",
            detector_batch_size=32,
            recognition_batch_size=256,
            layout_batch_size=32,
        )

    @classmethod
    def for_cpu(cls) -> TranslationConfig:
        """Conservative config for CPU-only systems."""
        return cls(
            device="cpu",
            detector_batch_size=4,
            recognition_batch_size=16,
            layout_batch_size=4,
            ocr_batch_size=1,
        )

"""Tests for configuration module."""

import os
from unittest.mock import MagicMock, patch

from pdf_translator.core.config import TranslationConfig


class TestTranslationConfig:
    """Tests for TranslationConfig class."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        config = TranslationConfig()

        assert config.source_lang == "en"
        assert config.target_lang == "hi"
        assert config.dpi == 200
        assert config.ocr_batch_size == 4
        assert config.num_workers >= 1

    def test_custom_values(self):
        """Config should accept custom values."""
        config = TranslationConfig(
            source_lang="es",
            target_lang="fr",
            dpi=300,
            device="cpu",
        )

        assert config.source_lang == "es"
        assert config.target_lang == "fr"
        assert config.dpi == 300
        assert config.device == "cpu"

    def test_all_batch_sizes(self):
        """Should accept all batch size parameters."""
        config = TranslationConfig(
            detector_batch_size=8,
            recognition_batch_size=64,
            layout_batch_size=4,
        )

        assert config.detector_batch_size == 8
        assert config.recognition_batch_size == 64
        assert config.layout_batch_size == 4

    def test_apply_environment(self):
        """Environment variables should be set correctly."""
        config = TranslationConfig(
            device="cpu",
            detector_batch_size=8,
            recognition_batch_size=16,
            layout_batch_size=4,
        )
        config.apply_environment()

        assert os.environ.get("TORCH_DEVICE") == "cpu"
        assert os.environ.get("DETECTOR_BATCH_SIZE") == "8"
        assert os.environ.get("RECOGNITION_BATCH_SIZE") == "16"
        assert os.environ.get("LAYOUT_BATCH_SIZE") == "4"
        assert os.environ.get("DETECTOR_POSTPROCESSING_CPU_WORKERS") is not None

    def test_for_apple_silicon(self):
        """Apple Silicon preset should use MPS."""
        config = TranslationConfig.for_apple_silicon()

        assert config.device == "mps"
        assert config.detector_batch_size == 16
        assert config.recognition_batch_size == 32
        assert config.layout_batch_size == 8

    def test_for_nvidia_gpu(self):
        """NVIDIA preset should use CUDA with higher batch sizes."""
        config = TranslationConfig.for_nvidia_gpu()

        assert config.device == "cuda"
        assert config.detector_batch_size == 32
        assert config.recognition_batch_size == 256
        assert config.layout_batch_size == 32

    def test_for_cpu(self):
        """CPU preset should use conservative settings."""
        config = TranslationConfig.for_cpu()

        assert config.device == "cpu"
        assert config.ocr_batch_size == 1
        assert config.detector_batch_size == 4
        assert config.recognition_batch_size == 16
        assert config.layout_batch_size == 4


class TestTranslationConfigAutoDetect:
    """Tests for device auto-detection."""

    def test_auto_detect_cuda(self):
        """Should detect CUDA when available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True

        with patch.dict("sys.modules", {"torch": mock_torch}):
            config = TranslationConfig(device="auto")
            config._detect_device()
            assert config.device == "cuda"

    def test_auto_detect_mps(self):
        """Should detect MPS when CUDA unavailable but MPS available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True

        with patch.dict("sys.modules", {"torch": mock_torch}):
            config = TranslationConfig(device="auto")
            config._detect_device()
            assert config.device == "mps"

    def test_auto_detect_cpu_fallback(self):
        """Should fall back to CPU when no GPU available."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            config = TranslationConfig(device="auto")
            config._detect_device()
            assert config.device == "cpu"

    def test_auto_detect_no_torch(self):
        """Should fall back to CPU when torch not installed."""
        with patch.dict("sys.modules", {"torch": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                config = TranslationConfig.__new__(TranslationConfig)
                config.device = "auto"
                config._detect_device()
                assert config.device == "cpu"

    def test_explicit_device_not_overridden(self):
        """Explicit device setting should not be auto-detected."""
        config = TranslationConfig(device="cpu")
        # Device should remain cpu, not auto-detected
        assert config.device == "cpu"

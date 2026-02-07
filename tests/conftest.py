"""Pytest configuration and shared fixtures."""

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def sample_image():
    """Create a simple test image."""
    return Image.new("RGB", (200, 100), color="white")


@pytest.fixture
def sample_image_large():
    """Create a larger test image."""
    return Image.new("RGB", (800, 600), color="white")


@pytest.fixture
def sample_image_dark():
    """Create a dark test image."""
    return Image.new("RGB", (200, 100), color="black")


@pytest.fixture
def sample_image_colored():
    """Create a colored test image."""
    return Image.new("RGB", (200, 100), color="red")


@pytest.fixture
def sample_image_array():
    """Create a simple test image as numpy array."""
    return np.ones((100, 200, 3), dtype=np.uint8) * 255


@pytest.fixture
def sample_image_array_dark():
    """Create a dark test image as numpy array."""
    return np.zeros((100, 200, 3), dtype=np.uint8)


@pytest.fixture
def sample_region():
    """Create a single sample OCR region."""
    return {
        "text": "Hello World",
        "raw_text": "Hello World",
        "box": [10, 10, 100, 30],
        "polygon": [[10, 10], [100, 10], [100, 30], [10, 30]],
        "confidence": 0.95,
        "formatting": {"bold": False, "underline": False},
    }


@pytest.fixture
def sample_regions():
    """Create sample OCR regions."""
    return [
        {
            "text": "Hello World",
            "raw_text": "Hello World",
            "box": [10, 10, 100, 30],
            "polygon": [[10, 10], [100, 10], [100, 30], [10, 30]],
            "confidence": 0.95,
            "formatting": {"bold": False, "underline": False},
        },
        {
            "text": "Test Text",
            "raw_text": "<b>Test Text</b>",
            "box": [10, 40, 80, 60],
            "polygon": [[10, 40], [80, 40], [80, 60], [10, 60]],
            "confidence": 0.88,
            "formatting": {"bold": True, "underline": False},
        },
    ]


@pytest.fixture
def sample_regions_with_underline():
    """Create sample OCR regions with underline formatting."""
    return [
        {
            "text": "Underlined Text",
            "raw_text": "<u>Underlined Text</u>",
            "box": [10, 10, 150, 30],
            "polygon": [[10, 10], [150, 10], [150, 30], [10, 30]],
            "confidence": 0.92,
            "formatting": {"bold": False, "underline": True},
        },
    ]


@pytest.fixture
def sample_regions_mixed_formatting():
    """Create sample OCR regions with mixed formatting."""
    return [
        {
            "text": "Plain text",
            "raw_text": "Plain text",
            "box": [10, 10, 100, 30],
            "polygon": [],
            "confidence": 0.95,
            "formatting": {"bold": False, "underline": False},
        },
        {
            "text": "Bold text",
            "raw_text": "<b>Bold text</b>",
            "box": [10, 40, 100, 60],
            "polygon": [],
            "confidence": 0.93,
            "formatting": {"bold": True, "underline": False},
        },
        {
            "text": "Underlined",
            "raw_text": "<u>Underlined</u>",
            "box": [10, 70, 100, 90],
            "polygon": [],
            "confidence": 0.91,
            "formatting": {"bold": False, "underline": True},
        },
        {
            "text": "Bold and underlined",
            "raw_text": "<b><u>Bold and underlined</u></b>",
            "box": [10, 100, 180, 120],
            "polygon": [],
            "confidence": 0.89,
            "formatting": {"bold": True, "underline": True},
        },
    ]


@pytest.fixture
def temp_pdf(tmp_path):
    """Create a minimal PDF file for testing."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""

    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(pdf_content)
    return pdf_file


@pytest.fixture
def mock_translation_config():
    """Create a mock translation config."""
    from pdf_translator.core.config import TranslationConfig

    return TranslationConfig(
        source_lang="en",
        target_lang="hi",
        device="cpu",
        dpi=150,
        ocr_batch_size=2,
    )


@pytest.fixture
def sample_texts():
    """Create sample texts for translation."""
    return [
        "Hello, world!",
        "This is a test.",
        "PDF Translator",
        "Machine learning is amazing.",
    ]


@pytest.fixture
def sample_translations():
    """Create sample translated texts."""
    return [
        "नमस्ते, दुनिया!",
        "यह एक परीक्षण है।",
        "पीडीएफ अनुवादक",
        "मशीन लर्निंग अद्भुत है।",
    ]

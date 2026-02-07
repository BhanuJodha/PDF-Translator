"""
PDF Translator - Translate PDF documents using OCR and machine translation.

A Python package for translating scanned PDFs and image-based documents
using Surya OCR and Google Translate.
"""

from pdf_translator.core.config import TranslationConfig
from pdf_translator.core.translator import PDFTranslator

__version__ = "0.1.0"
__author__ = "Bhanu Pratap Singh Rathore"

__all__ = [
    "PDFTranslator",
    "TranslationConfig",
    "__version__",
]

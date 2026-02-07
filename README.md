# PDF Translator

Translate scanned PDFs and image-based documents using OCR and machine translation.

This tool extracts text from PDF pages using [Surya OCR](https://github.com/VikParuchuri/surya), translates it via Google Translate, and renders the translated text back onto the original document—preserving layout, colors, and formatting.

## Features

- **High-quality OCR** powered by Surya (supports 90+ languages)
- **Automatic text color detection** ensures readability on any background
- **Batch processing** for faster translation of multi-page documents
- **GPU acceleration** on NVIDIA (CUDA) and Apple Silicon (MPS)
- **Page range selection** to translate specific pages
- **Preserves formatting** including bold and underlined text

## Installation

```bash
pip install pdf-translator
```

### System Dependencies

You'll need `poppler` for PDF rendering:

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows (via conda)
conda install -c conda-forge poppler
```

## Quick Start

### Command Line

```bash
# Basic usage - translates English to Hindi by default
pdf-translator document.pdf

# Specify languages
pdf-translator document.pdf --source en --target hi

# Translate specific pages
pdf-translator document.pdf --pages 1-5

# Custom output path
pdf-translator document.pdf -o translated.pdf

# Higher quality (slower)
pdf-translator document.pdf --dpi 300
```

### Python API

```python
from pdf_translator import PDFTranslator, TranslationConfig

# Simple usage
translator = PDFTranslator()
translator.translate("document.pdf", target_lang="hi")

# With custom configuration
config = TranslationConfig(
    source_lang="en",
    target_lang="hi",
    device="mps",  # or "cuda", "cpu"
    dpi=200,
)

translator = PDFTranslator(config)
output_path = translator.translate(
    "document.pdf",
    output_path="translated.pdf",
    page_range="1-10",
)
```

### Device-Specific Configs

```python
from pdf_translator import TranslationConfig

# For Apple Silicon Macs
config = TranslationConfig.for_apple_silicon()

# For NVIDIA GPUs
config = TranslationConfig.for_nvidia_gpu()

# For CPU-only systems
config = TranslationConfig.for_cpu()
```

## CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output file path | `input_translated.pdf` |
| `--source` | `-s` | Source language code | `en` |
| `--target` | `-t` | Target language code | `hi` |
| `--pages` | `-p` | Page range (e.g., "1-5", "1,3,5") | `all` |
| `--dpi` | `-d` | Rendering resolution | `200` |
| `--batch-size` | `-b` | Pages per OCR batch | `4` |
| `--device` | | Compute device | `auto` |

## Supported Languages

The source language can be any of the 90+ languages supported by Surya OCR. Target languages depend on Google Translate availability.

Common language codes:
- `en` - English
- `hi` - Hindi
- `es` - Spanish
- `fr` - French
- `de` - German
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- `ar` - Arabic
- `ru` - Russian

## How It Works

1. **PDF to Images**: Each page is rendered as a high-resolution image
2. **OCR**: Surya detects and recognizes text regions with their positions
3. **Translation**: Text is batch-translated via Google Translate
4. **Rendering**: Original text is erased and replaced with translations
5. **Output**: Processed images are combined back into a PDF

The tool samples background colors around each text region to cleanly erase the original text, then automatically chooses black or white text for maximum contrast.

## Performance Tips

- **Lower DPI** (150-200) for faster processing, higher (300+) for better quality
- **Increase batch size** if you have more GPU memory
- **Use page ranges** to translate only what you need
- **GPU acceleration** provides 5-10x speedup over CPU

## Development

### Setup

```bash
# Clone the repo
git clone https://github.com/bhanurathore/pdf-translator.git
cd pdf-translator

# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Or using pytest directly
pytest tests/ -v

# Run specific test file
pytest tests/core/test_config.py -v

# Run with coverage
pytest tests/ --cov=pdf_translator --cov-report=term-missing
```

### Linting and Formatting

```bash
# Check code style with ruff
make lint

# Auto-fix linting issues
make lint-fix

# Format code with black
make format

# Check formatting without changes
make format-check

# Run type checker
make typecheck

# Run all checks (format, lint, typecheck, test)
make check
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

### Building and Publishing

```bash
# Build package
make build

# Publish to Test PyPI (for testing)
make publish-test

# Publish to PyPI
make publish
```

## Project Structure

```
pdf-translator/
├── pdf_translator/              # Main package
│   ├── __init__.py              # Package exports
│   ├── cli.py                   # Command-line interface
│   ├── py.typed                 # PEP 561 type marker
│   ├── core/                    # Core functionality
│   │   ├── config.py            # Configuration management
│   │   ├── ocr.py               # Surya OCR wrapper
│   │   ├── renderer.py          # Text rendering
│   │   ├── text_translator.py   # Google Translate wrapper
│   │   └── translator.py        # Main orchestrator
│   └── utils/                   # Utilities
│       ├── fonts.py             # Cross-platform font discovery
│       └── page_range.py        # Page range parsing
├── tests/                       # Test suite (mirrors package structure)
│   ├── conftest.py              # Shared fixtures
│   ├── test_cli.py
│   ├── core/                    # Tests for core modules
│   │   ├── test_config.py
│   │   ├── test_ocr.py
│   │   ├── test_renderer.py
│   │   └── test_text_translator.py
│   └── utils/                   # Tests for utilities
│       ├── test_fonts.py
│       └── test_page_range.py
├── docs/                        # Documentation
│   └── PROJECT_STRUCTURE.md     # Explains all project files
├── pyproject.toml               # Package configuration (main config!)
├── setup.py                     # Legacy compatibility
├── Makefile                     # Command shortcuts
├── MANIFEST.in                  # Package manifest
├── .pre-commit-config.yaml      # Pre-commit hooks
├── .gitignore                   # Git ignore rules
├── .editorconfig                # Editor settings
├── .python-version              # Python version (for pyenv)
└── LICENSE                      # MIT License
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Maintainer

**Bhanu Pratap Singh Rathore**

## Acknowledgments

- [Surya OCR](https://github.com/VikParuchuri/surya) for the excellent OCR engine
- [deep-translator](https://github.com/nidhaloff/deep-translator) for the translation API wrapper
- [pdf2image](https://github.com/Belval/pdf2image) for PDF rendering

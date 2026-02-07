"""Command-line interface for PDF Translator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pdf_translator import __version__
from pdf_translator.core.config import TranslationConfig
from pdf_translator.core.translator import PDFTranslator


def create_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pdf-translator",
        description="Translate PDF documents using OCR and machine translation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pdf-translator document.pdf
  pdf-translator document.pdf -t hi -o translated.pdf
  pdf-translator document.pdf --pages 1-5
  pdf-translator document.pdf --pages "1,3,5-10"
  pdf-translator document.pdf --device cuda --dpi 300

Page Range Formats:
  all       Process all pages (default)
  5         Just page 5
  1-10      Pages 1 through 10
  1,5,9     Pages 1, 5, and 9
  1-3,7-10  Pages 1-3 and 7-10
        """,
    )

    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF file to translate",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output PDF path (default: input_translated.pdf)",
    )

    parser.add_argument(
        "-s",
        "--source",
        type=str,
        default="en",
        help="Source language code (default: en)",
    )

    parser.add_argument(
        "-t",
        "--target",
        type=str,
        default="hi",
        help="Target language code (default: hi)",
    )

    parser.add_argument(
        "-p",
        "--pages",
        type=str,
        default="all",
        help="Page range to process (default: all)",
    )

    parser.add_argument(
        "-d",
        "--dpi",
        type=int,
        default=200,
        help="DPI for PDF rendering (default: 200)",
    )

    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=4,
        help="Number of pages to OCR at once (default: 4)",
    )

    parser.add_argument(
        "--device",
        type=str,
        choices=["auto", "cuda", "mps", "cpu"],
        default="auto",
        help="Compute device (default: auto-detect)",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    pdf_path = Path(args.pdf_path).resolve()

    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        return 1

    if not pdf_path.suffix.lower() == ".pdf":
        print(f"Warning: File doesn't have .pdf extension: {pdf_path}")

    # Build configuration from CLI args
    config = TranslationConfig(
        source_lang=args.source,
        target_lang=args.target,
        device=args.device,
        dpi=args.dpi,
        ocr_batch_size=args.batch_size,
    )

    try:
        translator = PDFTranslator(config)
        output = translator.translate(
            pdf_path,
            output_path=args.output,
            page_range=args.pages,
        )
        print(f"\nTranslated PDF saved to: {output}")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

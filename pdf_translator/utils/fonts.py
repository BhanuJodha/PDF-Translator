"""Font management utilities."""

from __future__ import annotations

import platform
from collections.abc import Iterator
from pathlib import Path

from PIL import ImageFont


class FontManager:
    """
    Manages font discovery and loading across different operating systems.

    Handles the messy reality of finding appropriate fonts for different
    languages on macOS, Linux, and Windows.
    """

    # Common font locations by OS
    FONT_DIRS = {
        "Darwin": [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library/Fonts",
        ],
        "Linux": [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local/share/fonts",
        ],
        "Windows": [
            Path("C:/Windows/Fonts"),
        ],
    }

    # Language-specific font preferences
    LANGUAGE_FONTS = {
        "hi": {  # Hindi / Devanagari
            "Darwin": ["Kohinoor.ttc", "Devanagari MT.ttc", "Devanagari Sangam MN.ttc"],
            "Linux": ["Noto Sans Devanagari", "Lohit-Devanagari.ttf"],
            "Windows": ["Nirmala.ttf", "Mangal.ttf"],
        },
        "zh": {  # Chinese
            "Darwin": ["PingFang.ttc", "STHeiti Light.ttc"],
            "Linux": ["Noto Sans CJK SC", "WenQuanYi Micro Hei"],
            "Windows": ["msyh.ttc", "simsun.ttc"],
        },
        "ja": {  # Japanese
            "Darwin": ["Hiragino Sans GB.ttc", "Hiragino Kaku Gothic Pro.ttc"],
            "Linux": ["Noto Sans CJK JP", "TakaoPGothic.ttf"],
            "Windows": ["msgothic.ttc", "meiryo.ttc"],
        },
        "ko": {  # Korean
            "Darwin": ["AppleGothic.ttf", "AppleSDGothicNeo.ttc"],
            "Linux": ["Noto Sans CJK KR", "NanumGothic.ttf"],
            "Windows": ["malgun.ttf", "gulim.ttc"],
        },
        "ar": {  # Arabic
            "Darwin": ["GeezaPro.ttc"],
            "Linux": ["Noto Sans Arabic", "Amiri-Regular.ttf"],
            "Windows": ["arial.ttf"],
        },
    }

    # Fallback fonts for Latin scripts
    DEFAULT_FONTS = {
        "Darwin": ["Helvetica.ttc", "SF-Pro.ttf", "Arial.ttf"],
        "Linux": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "FreeSans.ttf"],
        "Windows": ["arial.ttf", "segoeui.ttf", "tahoma.ttf"],
    }

    def __init__(self) -> None:
        self._system = platform.system()
        self._cache: dict[tuple[str, int, bool], ImageFont.FreeTypeFont] = {}

    def get_font(
        self,
        size: int,
        lang: str = "en",
        bold: bool = False,
    ) -> ImageFont.FreeTypeFont:
        """
        Get an appropriate font for the given language and style.

        Results are cached to avoid repeated filesystem lookups.
        """
        cache_key = (lang, size, bold)
        if cache_key in self._cache:
            return self._cache[cache_key]

        font = self._find_font(size, lang, bold)
        self._cache[cache_key] = font
        return font

    def _find_font(self, size: int, lang: str, bold: bool) -> ImageFont.FreeTypeFont:
        """Search for a suitable font file."""
        # Try language-specific fonts first
        for font_path in self._get_font_candidates(lang):
            try:
                index = 1 if bold else 0
                return ImageFont.truetype(str(font_path), size, index=index)
            except OSError:
                continue

        # Fall back to default fonts
        for font_path in self._get_font_candidates("en"):
            try:
                index = 1 if bold else 0
                return ImageFont.truetype(str(font_path), size, index=index)
            except OSError:
                continue

        return ImageFont.load_default()  # type: ignore[return-value]

    def _get_font_candidates(self, lang: str) -> Iterator[Path]:
        """Generate possible font paths for a language."""
        font_dirs = self.FONT_DIRS.get(self._system, [])

        # Get language-specific font names
        lang_fonts = self.LANGUAGE_FONTS.get(lang, {})
        font_names = lang_fonts.get(self._system, [])

        # Add default fonts as fallback
        default_names = self.DEFAULT_FONTS.get(self._system, [])
        all_names = list(font_names) + list(default_names)

        for font_dir in font_dirs:
            if not font_dir.exists():
                continue

            for name in all_names:
                # Try direct path
                direct = font_dir / name
                if direct.exists():
                    yield direct

                # Try in Supplemental folder (macOS)
                supplemental = font_dir / "Supplemental" / name
                if supplemental.exists():
                    yield supplemental

                # Search subdirectories (Linux)
                for subdir in font_dir.iterdir():
                    if subdir.is_dir():
                        candidate = subdir / name
                        if candidate.exists():
                            yield candidate

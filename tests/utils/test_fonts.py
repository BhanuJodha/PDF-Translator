"""Tests for font management utilities."""

from pathlib import Path
from unittest.mock import patch

from pdf_translator.utils.fonts import FontManager


class TestFontManagerInit:
    """Tests for FontManager initialization."""

    def test_init_detects_system(self):
        """Should detect operating system."""
        manager = FontManager()
        assert manager._system in ["Darwin", "Linux", "Windows", ""]

    def test_init_empty_cache(self):
        """Should start with empty cache."""
        manager = FontManager()
        assert manager._cache == {}

    @patch("platform.system")
    def test_init_darwin(self, mock_system):
        """Should detect macOS."""
        mock_system.return_value = "Darwin"
        manager = FontManager()
        assert manager._system == "Darwin"

    @patch("platform.system")
    def test_init_linux(self, mock_system):
        """Should detect Linux."""
        mock_system.return_value = "Linux"
        manager = FontManager()
        assert manager._system == "Linux"

    @patch("platform.system")
    def test_init_windows(self, mock_system):
        """Should detect Windows."""
        mock_system.return_value = "Windows"
        manager = FontManager()
        assert manager._system == "Windows"


class TestFontManagerFontDirs:
    """Tests for font directory definitions."""

    def test_darwin_dirs_defined(self):
        """Should have macOS font directories."""
        assert "Darwin" in FontManager.FONT_DIRS
        dirs = FontManager.FONT_DIRS["Darwin"]
        assert len(dirs) > 0
        assert any("System" in str(d) or "Library" in str(d) for d in dirs)

    def test_linux_dirs_defined(self):
        """Should have Linux font directories."""
        assert "Linux" in FontManager.FONT_DIRS
        dirs = FontManager.FONT_DIRS["Linux"]
        assert len(dirs) > 0
        assert any("share/fonts" in str(d) for d in dirs)

    def test_windows_dirs_defined(self):
        """Should have Windows font directories."""
        assert "Windows" in FontManager.FONT_DIRS
        dirs = FontManager.FONT_DIRS["Windows"]
        assert len(dirs) > 0
        assert any("Fonts" in str(d) for d in dirs)


class TestFontManagerLanguageFonts:
    """Tests for language-specific font definitions."""

    def test_hindi_fonts(self):
        """Should have Hindi font preferences."""
        assert "hi" in FontManager.LANGUAGE_FONTS
        for platform in ["Darwin", "Linux", "Windows"]:
            assert platform in FontManager.LANGUAGE_FONTS["hi"]
            assert len(FontManager.LANGUAGE_FONTS["hi"][platform]) > 0

    def test_chinese_fonts(self):
        """Should have Chinese font preferences."""
        assert "zh" in FontManager.LANGUAGE_FONTS
        for platform in ["Darwin", "Linux", "Windows"]:
            assert platform in FontManager.LANGUAGE_FONTS["zh"]

    def test_japanese_fonts(self):
        """Should have Japanese font preferences."""
        assert "ja" in FontManager.LANGUAGE_FONTS
        for platform in ["Darwin", "Linux", "Windows"]:
            assert platform in FontManager.LANGUAGE_FONTS["ja"]

    def test_korean_fonts(self):
        """Should have Korean font preferences."""
        assert "ko" in FontManager.LANGUAGE_FONTS
        for platform in ["Darwin", "Linux", "Windows"]:
            assert platform in FontManager.LANGUAGE_FONTS["ko"]

    def test_arabic_fonts(self):
        """Should have Arabic font preferences."""
        assert "ar" in FontManager.LANGUAGE_FONTS
        for platform in ["Darwin", "Linux", "Windows"]:
            assert platform in FontManager.LANGUAGE_FONTS["ar"]

    def test_hindi_darwin_specific_fonts(self):
        """Should have specific Hindi fonts for macOS."""
        fonts = FontManager.LANGUAGE_FONTS["hi"]["Darwin"]
        assert any("Kohinoor" in f or "Devanagari" in f for f in fonts)

    def test_chinese_darwin_specific_fonts(self):
        """Should have specific Chinese fonts for macOS."""
        fonts = FontManager.LANGUAGE_FONTS["zh"]["Darwin"]
        assert len(fonts) > 0


class TestFontManagerDefaultFonts:
    """Tests for default font definitions."""

    def test_darwin_defaults(self):
        """Should have default fonts for macOS."""
        assert "Darwin" in FontManager.DEFAULT_FONTS
        fonts = FontManager.DEFAULT_FONTS["Darwin"]
        assert len(fonts) > 0
        assert any("Helvetica" in f or "Arial" in f for f in fonts)

    def test_linux_defaults(self):
        """Should have default fonts for Linux."""
        assert "Linux" in FontManager.DEFAULT_FONTS
        fonts = FontManager.DEFAULT_FONTS["Linux"]
        assert len(fonts) > 0
        assert any("DejaVu" in f or "Liberation" in f for f in fonts)

    def test_windows_defaults(self):
        """Should have default fonts for Windows."""
        assert "Windows" in FontManager.DEFAULT_FONTS
        fonts = FontManager.DEFAULT_FONTS["Windows"]
        assert len(fonts) > 0
        assert any("arial" in f.lower() for f in fonts)


class TestFontManagerGetFont:
    """Tests for get_font method."""

    def test_returns_font(self):
        """Should return a font object."""
        manager = FontManager()
        font = manager.get_font(12)
        assert font is not None

    def test_caches_result(self):
        """Should cache font lookups."""
        manager = FontManager()

        font1 = manager.get_font(12, lang="en")
        font2 = manager.get_font(12, lang="en")

        assert font1 is font2
        assert ("en", 12, False) in manager._cache

    def test_different_sizes_cached_separately(self):
        """Different sizes should have separate cache entries."""
        manager = FontManager()

        manager.get_font(12, lang="en")
        manager.get_font(14, lang="en")

        assert ("en", 12, False) in manager._cache
        assert ("en", 14, False) in manager._cache

    def test_bold_cached_separately(self):
        """Bold fonts should be cached separately."""
        manager = FontManager()

        manager.get_font(12, lang="en", bold=False)
        manager.get_font(12, lang="en", bold=True)

        assert ("en", 12, False) in manager._cache
        assert ("en", 12, True) in manager._cache

    def test_different_languages_cached_separately(self):
        """Different languages should have separate cache entries."""
        manager = FontManager()

        manager.get_font(12, lang="en")
        manager.get_font(12, lang="hi")

        assert ("en", 12, False) in manager._cache
        assert ("hi", 12, False) in manager._cache

    def test_unknown_language_returns_font(self):
        """Should return font for unknown language (fallback)."""
        manager = FontManager()
        font = manager.get_font(12, lang="xyz")
        assert font is not None

    def test_various_sizes(self):
        """Should handle various font sizes."""
        manager = FontManager()

        for size in [8, 12, 16, 24, 36, 48]:
            font = manager.get_font(size)
            assert font is not None

    def test_hindi_font(self):
        """Should return font for Hindi."""
        manager = FontManager()
        font = manager.get_font(12, lang="hi")
        assert font is not None

    def test_chinese_font(self):
        """Should return font for Chinese."""
        manager = FontManager()
        font = manager.get_font(12, lang="zh")
        assert font is not None

    def test_japanese_font(self):
        """Should return font for Japanese."""
        manager = FontManager()
        font = manager.get_font(12, lang="ja")
        assert font is not None


class TestFontManagerFindFont:
    """Tests for _find_font method."""

    def test_returns_font(self):
        """Should return a font."""
        manager = FontManager()
        font = manager._find_font(12, "en", False)
        assert font is not None

    def test_bold_font(self):
        """Should attempt to get bold font."""
        manager = FontManager()
        font = manager._find_font(12, "en", True)
        assert font is not None

    def test_fallback_to_default(self):
        """Should fall back to default font."""
        manager = FontManager()
        # Unknown language should fall back
        font = manager._find_font(12, "unknown_lang", False)
        assert font is not None


class TestFontManagerGetFontCandidates:
    """Tests for _get_font_candidates method."""

    def test_yields_paths(self):
        """Should yield Path objects."""
        manager = FontManager()
        candidates = list(manager._get_font_candidates("en"))
        # May be empty if no fonts found, but should not error
        for candidate in candidates:
            assert isinstance(candidate, Path)

    def test_language_specific_first(self):
        """Should try language-specific fonts."""
        manager = FontManager()
        # Just verify it doesn't crash
        list(manager._get_font_candidates("hi"))

    def test_unknown_language(self):
        """Should handle unknown language."""
        manager = FontManager()
        # Should not crash, may return default fonts
        list(manager._get_font_candidates("xyz"))

"""Text translation using Google Translate."""

from __future__ import annotations

from deep_translator import GoogleTranslator


class TextTranslator:
    """
    Handles text translation using Google Translate API.

    Supports batch translation for efficiency and falls back to
    individual translation if batch fails.
    """

    def __init__(self, source_lang: str = "en", target_lang: str = "hi"):
        self.source_lang = source_lang
        self.target_lang = target_lang

    def translate_batch(self, texts: list[str]) -> list[str]:
        """
        Translate a batch of texts.

        Short texts (single digits, very short strings) are skipped
        to avoid wasting API calls on things that don't need translation.

        Args:
            texts: List of strings to translate

        Returns:
            List of translated strings in the same order
        """
        if not texts:
            return []

        translator = GoogleTranslator(
            source=self.source_lang,
            target=self.target_lang,
        )

        # Figure out which texts actually need translation
        translatable_indices = []
        translatable_texts = []
        results = [""] * len(texts)

        for i, text in enumerate(texts):
            if self._should_skip(text):
                results[i] = text
            else:
                translatable_indices.append(i)
                translatable_texts.append(text)

        if not translatable_texts:
            return results

        # Try batch first, fall back to individual if needed
        try:
            translated = translator.translate_batch(translatable_texts)
            for idx, trans in zip(translatable_indices, translated):
                results[idx] = trans if trans else texts[idx]
        except Exception as e:
            print(f"Batch translation failed ({e}), falling back to individual...")
            self._translate_individually(
                translator, translatable_indices, translatable_texts, texts, results
            )

        return results

    def translate(self, text: str) -> str:
        """Translate a single text string."""
        if self._should_skip(text):
            return text

        translator = GoogleTranslator(
            source=self.source_lang,
            target=self.target_lang,
        )

        try:
            result = translator.translate(text)
            return str(result) if result else text
        except Exception:
            return text

    def _should_skip(self, text: str) -> bool:
        """Check if text should be skipped (too short or just numbers)."""
        stripped = text.strip()
        return len(stripped) < 2 or stripped.isdigit()

    def _translate_individually(
        self,
        translator: GoogleTranslator,
        indices: list[int],
        texts: list[str],
        originals: list[str],
        results: list[str],
    ) -> None:
        """Fallback: translate texts one by one."""
        for idx, text in zip(indices, texts):
            try:
                result = translator.translate(text)
                results[idx] = result if result else originals[idx]
            except Exception:
                results[idx] = originals[idx]

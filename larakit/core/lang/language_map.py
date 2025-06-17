from typing import Iterator, Optional, Dict, List

from larakit.core.lang.language import Language


class LanguageMap:
    class Entry:
        def __init__(self, code: str, language: Optional[Language] = None,
                     variants: Optional[List[Language]] = None):
            self.code = code
            if language is None:
                self.language = Language.from_string(code)
                self.variants = None
            else:
                self.language = language
                self.variants = set(variants) if variants else None

        def has_variants(self) -> bool:
            return self.variants is not None and len(self.variants) > 0

        def get_or_default(self, q: Language) -> Language:
            if not self.has_variants() or self.code != q.code() or q.is_language_only():
                return self.language

            region = q.region()
            for variant in self.variants:
                if variant.region() == region:
                    return variant

            return self.language

        def __lt__(self, other: 'LanguageMap.Entry') -> bool:
            return self.code < other.code

    def __init__(self, entries: List[Entry]):
        self.entries = sorted(entries)
        self.codes = {entry.code for entry in entries}
        self.map: Dict[str, LanguageMap.Entry] = {entry.code: entry for entry in entries}

    def get(self, language: Language) -> Optional[Entry]:
        return self.map.get(language.code(), None)

    def is_direction_supported(self, source: Language, target: Language) -> bool:
        return self.is_language_supported(source) and self.is_language_supported(target)

    def is_language_supported(self, language: Language) -> bool:
        return language.code() in self.codes

    def __iter__(self) -> Iterator[Entry]:
        return iter(self.entries)

from dataclasses import dataclass
from typing import Tuple

from larakit.core.lang.language import Language


@dataclass
class LanguageDirection:
    source: Language
    target: Language

    @classmethod
    def from_tuple(cls, language: Tuple[str, str]) -> 'LanguageDirection':
        if len(language) != 2:
            raise ValueError(f"Language tuple must contain two elements, got {len(language)}")
        return cls(source=Language.from_string(language[0]), target=Language.from_string(language[1]))

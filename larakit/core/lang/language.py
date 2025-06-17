from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Language:
    language: str
    tag: str
    script: str
    region: str

    @staticmethod
    def _to_title_case(string: str) -> str:
        return string[0].upper() + string[1:].lower()

    @staticmethod
    def _is_alpha(string: str) -> bool:
        return all('a' <= c <= 'z' or 'A' <= c <= 'Z' for c in string)

    @staticmethod
    def _is_digit(string: str) -> bool:
        return all('0' <= c <= '9' for c in string)

    @staticmethod
    def _parse_language(string: str) -> Optional[str]:
        if (len(string) == 2 or len(string) == 3) and Language._is_alpha(string):
            return string.lower()
        return None

    @staticmethod
    def _parse_script(string: str) -> Optional[str]:
        if len(string) == 4 and Language._is_alpha(string):
            return Language._to_title_case(string)
        return None

    @staticmethod
    def _parse_region(string: str) -> Optional[str]:
        if len(string) == 2 and Language._is_alpha(string):
            return string.upper()
        elif len(string) == 3 and Language._is_digit(string):
            return string
        return None

    @classmethod
    def from_string(cls, string: str) -> 'Language':
        if string is None:
            raise ValueError("Input string must not be None")
        if not string:
            raise ValueError("Input string must not be empty")

        language: Optional[str] = None
        script: Optional[str] = None
        region: Optional[str] = None
        tag_parts: List[str] = []

        skip: bool = False
        chunks: List[str] = string.replace('_', '-').split('-')
        for i, chunk in enumerate(chunks):
            if i == 0:
                language = Language._parse_language(chunk)
                if language is None:
                    raise ValueError(f"Invalid language subtag: '{chunk}' in '{string}'")
                tag_parts.append(language)
            else:
                if not skip:
                    if i == 1 and script is None:
                        script_candidate = Language._parse_script(chunk)
                        if script_candidate is not None:
                            script = script_candidate
                            tag_parts.append(script)
                            continue

                    if i <= 2 and region is None:
                        region_candidate = Language._parse_region(chunk)
                        if region_candidate is not None:
                            region = region_candidate
                            tag_parts.append(region)
                            continue

                skip = True
                tag_parts.append(chunk)

        if language is None:
            raise ValueError(f"Language subtag missing in '{string}'")

        tag: str = '-'.join(tag_parts)
        return cls(language, tag, script, region)

    def code(self) -> str:
        return self.language

    def region(self) -> Optional[str]:
        return self.region

    def is_language_only(self) -> bool:
        return self.language == self.tag

    def as_language_only(self) -> 'Language':
        return self if self.is_language_only() else Language.from_string(self.code())

    def __hash__(self) -> int:
        return hash(self.tag)

    def __str__(self):
        return self.tag

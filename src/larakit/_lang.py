from typing import Optional, List, Tuple


class Language:
    def __init__(self, code: str, tag: str, region: Optional[str] = None, script: Optional[str] = None):
        if not code or not isinstance(code, str):
            raise ValueError("code must be a non-empty string")
        if not tag or not isinstance(tag, str):
            raise ValueError("tag must be a non-empty string")

        self._code: str = code
        self._tag: str = tag
        self._region: Optional[str] = region
        self._script: Optional[str] = script

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
        if len(string) == 3 and Language._is_digit(string):
            return string
        return None

    @classmethod
    def from_string(cls, string: str) -> 'Language':
        if string is None:
            raise ValueError("Input string must not be None")
        if not string:
            raise ValueError("Input string must not be empty")

        code: Optional[str] = None
        region: Optional[str] = None
        script: Optional[str] = None
        tag_parts: List[str] = []

        skip: bool = False
        chunks: List[str] = string.replace('_', '-').split('-')
        for i, chunk in enumerate(chunks):
            if i == 0:
                code = Language._parse_language(chunk)
                if code is None:
                    raise ValueError(f"Invalid language subtag: '{chunk}' in '{string}'")
                tag_parts.append(code)
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

        if code is None:
            raise ValueError(f"Language subtag missing in '{string}'")

        tag: str = '-'.join(tag_parts)
        return cls(code=code, tag=tag, region=region, script=script)

    @property
    def code(self) -> str:
        return self._code

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def region(self) -> Optional[str]:
        return self._region

    @property
    def script(self) -> Optional[str]:
        return self._script

    def is_language_only(self) -> bool:
        return self.code == self.tag

    def as_language_only(self) -> 'Language':
        return self if self.is_language_only() else Language.from_string(self.code)

    def is_equal_or_more_generic_than(self, other: 'Language') -> bool:
        if not other:
            return False

        if self.code != other.code:
            return False
        if self.script and self.script != other.script:
            return False
        if self.region and self.region != other.region:
            return False

        return True

    def __eq__(self, other: 'Language') -> bool:
        return self.tag == other.tag

    def __hash__(self) -> int:
        return hash(self.tag)

    def __repr__(self) -> str:
        return self.tag

    def __str__(self):
        return self.tag


class LanguageDirection:
    def __init__(self, source: Language, target: Language):
        self._source: Language = source
        self._target: Language = target
        self._reversed: Optional['LanguageDirection'] = None

    @property
    def source(self) -> Language:
        return self._source

    @property
    def target(self) -> Language:
        return self._target

    @property
    def reversed(self):
        if self._reversed is None:
            self._reversed = LanguageDirection(source=self.target, target=self.source)
        return self._reversed

    @classmethod
    def from_tuple(cls, language: Tuple[str, str]) -> 'LanguageDirection':
        if len(language) != 2:
            raise ValueError(f"Language tuple must contain two elements, got {len(language)}")
        return cls(source=Language.from_string(language[0]), target=Language.from_string(language[1]))

    def is_equal_or_more_generic_than(self, other: 'LanguageDirection') -> bool:
        return (self.source.is_equal_or_more_generic_than(other.source) and
                self.target.is_equal_or_more_generic_than(other.target))

    def to_json(self) -> Tuple[str, str]:
        return self.source.tag, self.target.tag

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LanguageDirection):
            return False
        return self.source == other.source and self.target == other.target

    def __hash__(self) -> int:
        return hash((self.source, self.target))

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.source}\u2192{self.target}"

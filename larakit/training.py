import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Generator

from larakit.lang import LanguageDirection


@dataclass
class GlossaryItem:
    term: str
    translation: str

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'GlossaryItem':
        return cls(**data)

    def to_json(self) -> Dict[str, Any]:
        return self.__dict__


@dataclass
class MemoryMatch:
    sentence: str
    translation: str
    language: LanguageDirection
    score: float

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'MemoryMatch':
        data['language'] = LanguageDirection.from_tuple(data['language'])

        return cls(**data)

    def to_json(self) -> Dict[str, Any]:
        data = {k: v for k, v in self.__dict__.items() if v is not None and k != 'language'}
        data['language'] = self.language.to_json()

        return data


@dataclass
class TrainingUnit:
    language: List[str]
    sentence: str
    translation: str
    tuid: Optional[str] = field(default=None)
    matches: Optional[List[MemoryMatch]] = field(default=None)
    before: Optional[List[str]] = field(default=None)
    after: Optional[List[str]] = field(default=None)
    glossary: Optional[List[GlossaryItem]] = field(default=None)
    instructions: Optional[List[str]] = field(default=None)

    @classmethod
    def keys(cls) -> List[str]:
        return list(cls.__annotations__.keys())

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'TrainingUnit':
        if data.get("matches"):
            data["matches"] = [MemoryMatch.from_json(m) for m in data["matches"]]
        if data.get("glossary"):
            data["glossary"] = [GlossaryItem.from_json(g) for g in data["glossary"]]

        return cls(**data)

    def to_json(self) -> Dict[str, Any]:
        data = {k: v for k, v in self.__dict__.items() if v is not None and k not in ['matches', 'glossary']}
        if self.matches is not None:
            data['matches'] = [m.to_json() for m in self.matches]
        if self.glossary is not None:
            data['glossary'] = [g.to_json() for g in self.glossary]

        return data


class TrainingFileReader:
    def __init__(self, path: str, skip_rejected: bool = False):
        self._path = path
        self._file = None

    def __enter__(self):
        self._file = open(self._path, 'r', encoding='utf-8')
        return self

    def __iter__(self) -> Generator[TrainingUnit, None, None]:
        if self._file is None:
            raise IOError("Reader is not open.")

        for line in self._file:
            yield TrainingUnit.from_json(json.loads(line))

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()


class TrainingFileWriter:
    def __init__(self, path: str, properties: Dict[str, Any] = None):
        self._path = path
        self._file = None

    def __enter__(self):
        self._file = open(self._path, 'w', encoding='utf-8')
        return self

    def write(self, tu: TrainingUnit) -> None:
        self._file.write(json.dumps(tu.to_json(), ensure_ascii=False) + '\n')

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()

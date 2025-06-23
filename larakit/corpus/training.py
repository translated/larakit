from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from larakit.corpus import TranslationUnit, Corpus
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
class TrainingUnit(TranslationUnit):
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
        """
        if data.get("matches"):
            data["matches"] = [MemoryMatch.from_json(m) for m in data["matches"]]
        if data.get("glossary"):
            data["glossary"] = [GlossaryItem.from_json(g) for g in data["glossary"]]

        return cls(**data)
        """
        raise NotImplementedError

    def to_json(self) -> Dict[str, Any]:
        """
        data = {k: v for k, v in self.__dict__.items() if v is not None and k not in ['matches', 'glossary']}
        if self.matches is not None:
            data['matches'] = [m.to_json() for m in self.matches]
        if self.glossary is not None:
            data['glossary'] = [g.to_json() for g in self.glossary]
        return data
        """
        raise NotImplementedError


class TrainingCorpus(Corpus):
    pass

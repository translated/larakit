from abc import abstractmethod, ABC
from typing import Dict, List, Union, Optional, Iterable, Set, Tuple, Generator

from larakit import LanguageDirection


class Properties:
    def __init__(self, other: Optional['Properties'] = None):
        self._map: Dict[str, Union[str, List[str]]] = {}
        if other:
            self._set_all(other.map)

    @classmethod
    def from_json(cls, json_data: Dict[str, Union[str, List[str]]]) -> 'Properties':
        properties = cls()
        properties._set_all(json_data)
        return properties

    @property
    def map(self) -> Dict[str, Union[str, List[str]]]:
        return self._map

    def put(self, key: str, value: str) -> None:
        existing = self.map.get(key)
        if existing is None:
            self.map[key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            self.map[key] = [existing, value]

    def _set(self, key: str, value: Union[str, List[str]]) -> None:
        self.map[key] = value.copy() if isinstance(value, list) else value

    def _set_all(self, data: Dict[str, Union[str, List[str]]]) -> None:
        for key, value in data.items():
            self._set(key, value)

    def set(self, key: str, value: str) -> None:
        self._set(key, value)

    def has(self, key: str) -> bool:
        return key in self.map

    def keys(self) -> Iterable[str]:
        return self.map.keys()

    def get(self, key: str) -> Optional[Union[str, List[str]]]:
        return self.map.get(key)

    def size(self) -> int:
        return len(self.map)

    def value(self, key: str) -> Optional[str]:
        value = self.map.get(key)
        if value is None:
            return None
        if isinstance(value, list):
            return value[0]
        return value

    def values(self, key: str) -> Optional[List[str]]:
        value = self.map.get(key)
        if value is None:
            return None
        if isinstance(value, list):
            return value[:]
        return [value]

    def remove(self, key: str) -> None:
        self.map.pop(key, None)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Properties):
            return False
        return self.map == other.map

    def __hash__(self) -> int:
        items = tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k, v in self.map.items()))
        return hash(items)

    def __str__(self) -> str:
        return str(self.map)


class TranslationUnit:
    def __init__(self, language: LanguageDirection, sentence: str, translation: str, *,
                 tuid: Optional[str] = None, creation_date: Optional[str] = None, change_date: Optional[str] = None,
                 properties: Optional[Properties] = None):
        self._language: LanguageDirection = language
        self._sentence: str = sentence
        self._translation: str = translation
        self._tuid: Optional[str] = tuid
        self._creation_date: Optional[str] = creation_date
        self._change_date: Optional[str] = change_date
        self._properties: Optional[Properties] = properties

    @classmethod
    def from_tu(cls, tu: 'TranslationUnit') -> 'TranslationUnit':
        return cls(language=tu.language, sentence=tu.sentence, translation=tu.translation, tuid=tu.tuid,
                   creation_date=tu.creation_date, change_date=tu.change_date,
                   properties=None if tu.properties is None else Properties(tu.properties))

    @classmethod
    def from_json(cls, json_data: Dict[str, Union[str, List[str], Tuple[str, str]]]) -> 'TranslationUnit':
        return cls(language=LanguageDirection.from_tuple(json_data['language']), sentence=json_data["sentence"],
                   translation=json_data["translation"], tuid=json_data.get("tuid", None),
                   creation_date=json_data.get("creationDate", None), change_date=json_data.get("changeDate", None),
                   properties=json_data.get("properties"))

    @property
    def language(self) -> LanguageDirection:
        return self._language

    @property
    def sentence(self) -> str:
        return self._sentence

    @property
    def translation(self) -> str:
        return self._translation

    @property
    def tuid(self) -> Optional[str]:
        return self._tuid

    @property
    def creation_date(self) -> Optional[str]:
        return self._creation_date

    @property
    def change_date(self) -> Optional[str]:
        return self._change_date

    @property
    def properties(self) -> Optional[Properties]:
        return self._properties

    def to_json(self) -> Dict[str, Union[str, Tuple[str, str], Dict[str, Union[str, List[str]]]]]:
        data: Dict[str, Union[str, Tuple[str, str], Dict[str, Union[str, List[str]]]]] = {
            "language": self.language.to_json(), "sentence": self.sentence, "translation": self.translation
        }

        if self.tuid is not None:
            data["tuid"] = self.tuid
        if self.creation_date is not None:
            data["creationDate"] = self.creation_date
        if self.change_date is not None:
            data["changeDate"] = self.change_date
        if self.properties is not None:
            data["properties"] = self.properties.map

        return data

    def __eq__(self, other: 'TranslationUnit') -> bool:
        if not isinstance(other, TranslationUnit):
            return False
        return (self.tuid == other.tuid and self.language == other.language and
                self.sentence == other.sentence and self.translation == other.translation and
                self.creation_date == other.creation_date and self.change_date == other.change_date)

    def __hash__(self) -> int:
        return hash((self.tuid, self.language, self.sentence, self.translation, self.creation_date, self.change_date))

    def __str__(self) -> str:
        return f'[{self.language}] <{self.sentence}> ||| <{self.translation}>'


class TUReader(ABC):
    @abstractmethod
    def __enter__(self) -> 'TUReader':
        pass

    @abstractmethod
    def __iter__(self) -> Generator[TranslationUnit, None, None]:
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass


class TUWriter(ABC):
    @abstractmethod
    def __enter__(self) -> 'TUWriter':
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def write(self, tu: TranslationUnit):
        pass


class MultilingualCorpus(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def languages(self) -> Set[LanguageDirection]:
        pass

    @abstractmethod
    def reader(self) -> TUReader:
        pass

    @abstractmethod
    def writer(self) -> TUWriter:
        pass

from dataclasses import dataclass, field
from typing import Any
from typing import Dict, List, Union, Optional, Iterable

from larakit.lang import LanguageDirection


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

    def get(self, key: str) -> Union[str, List[str], None]:
        return self.map.get(key)

    def size(self) -> int:
        return len(self.map)

    def value(self, key: str) -> Optional[str]:
        value = self.map.get(key)
        if value is None:
            return None
        elif isinstance(value, list):
            return value[0]
        else:
            return value

    def values(self, key: str) -> Optional[List[str]]:
        value = self.map.get(key)
        if value is None:
            return None
        elif isinstance(value, list):
            return value[:]
        else:
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


@dataclass
class TranslationUnit:
    language: LanguageDirection
    sentence: str
    translation: str
    tuid: Optional[str] = field(default=None)
    creation_date: Optional[str] = field(default=None)
    change_date: Optional[str] = field(default=None)
    properties: Properties = field(default=None)

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]):
        return cls(
            language=LanguageDirection.from_tuple(json_data['language']),
            sentence=json_data["sentence"],
            translation=json_data["translation"],

            tuid=json_data.get("tuid", None),
            creation_date=json_data.get("creationDate", None),
            change_date=json_data.get("changeDate", None),
            properties=Properties.from_json(json_data.get("properties"))
        )

    def to_json(self) -> Dict[str, Any]:
        data: Dict[str, Union[str, Dict[str, List[str]]]] = {
            "language": self.language.to_json(),
            "sentence": self.sentence,
            "translation": self.translation,
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


class Corpus:
    pass

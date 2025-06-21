import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Generator, Union, Optional, Any

from larakit import shell
from larakit.counter import Counter
from larakit.lang import LanguageDirection
from larakit.properties import Properties


@dataclass
class TU:
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


class JTMReader:
    def __init__(self, path: str):
        self._path = path
        self._file = None

    def __enter__(self):
        self._file = open(self._path, 'r', encoding='utf-8')
        return self

    def __iter__(self) -> Generator[TU, None, None]:
        if self._file is None:
            raise IOError("Reader is not open.")

        for line in self._file:
            if not line.startswith(".footer"):
                yield TU.from_json(json.loads(line))

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()


class JTMWriter:
    def __init__(self, path: str, properties: Dict[str, Any] = None):
        self._path = path
        self._file = None
        self._properties = properties
        self._counter: Counter[LanguageDirection] = Counter()

    def add_property(self, key: str, value: str):
        if self._properties is None:
            self._properties = Properties()

        self._properties.put(key, value)

    def __enter__(self):
        self._file = open(self._path, 'w', encoding='utf-8')
        return self

    def write(self, tu: TU):
        self._counter.count(tu.language)
        self._file.write(json.dumps(tu.to_json(), ensure_ascii=False) + '\n')

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.write(JTM.Footer(self._counter, self._properties))
        self._file.close()


@dataclass
class JTM:
    @dataclass
    class Footer:
        _counter: Counter[LanguageDirection] = field(default=None)
        _properties: Optional[Properties] = field(default=None)

        _FOOTER_LINE_BEGIN = ".footer"

        def __post_init__(self):
            if self.counter is None:
                self._counter = Counter[LanguageDirection]()

        @classmethod
        def parse(cls, line: str) -> 'JTM.Footer':
            if line.startswith(cls._FOOTER_LINE_BEGIN):
                json_part = line[len(cls._FOOTER_LINE_BEGIN):].strip()
                return cls.from_json(json.loads(json_part))
            else:
                raise ValueError("The final line does not start with the expected '.footer' prefix.")

        @classmethod
        def from_json(cls, data: Dict[str, Any]):
            counter_data: List = data.get("counter", [])
            properties_data: Optional[Dict] = data.get("properties", None)

            counter = Counter[LanguageDirection]()
            for lang_tuple, lang_count in counter_data:
                counter.count(LanguageDirection.from_tuple(lang_tuple), lang_count)

            properties = Properties.from_json(properties_data) if properties_data else None
            return cls(counter, properties)

        @property
        def counter(self) -> Counter[LanguageDirection]:
            return self._counter

        @property
        def properties(self) -> Properties:
            return self._properties

        def get_total_count(self) -> int:
            return self._counter.get_total_count()

        def to_json(self) -> Dict[str, Any]:
            data: Dict[str, Any] = {"counter": [[lang.to_json(), count] for lang, count in self.counter.items_count()]}
            if self._properties:
                data["properties"] = self._properties.map

            return data

        def __str__(self) -> str:
            return f"{JTM.Footer._FOOTER_LINE_BEGIN}{json.dumps(self.to_json())}"

    _path: str
    _datasource_key: str = field(init=False)
    _id: str = field(init=False)
    _language: LanguageDirection = field(init=False)
    _footer: Optional['JTM.Footer'] = field(init=False, default=None)

    @classmethod
    def list(cls, path: str) -> List['JTM']:
        return [cls(os.path.join(path, file)) for file in os.listdir(path) if file.endswith('.jtm')]

    def __post_init__(self):
        self._datasource_key, self._id, lang_key = os.path.basename(self._path).split('.')[:3]
        self._datasource_key = self._datasource_key.lower()

        l1, l2 = lang_key.split('__')
        self._language = LanguageDirection.from_tuple((l1, l2))

    @property
    def id(self) -> str:
        return self._id

    @property
    def path(self) -> str:
        return self._path

    @property
    def filename(self) -> str:
        return os.path.basename(self._path)

    @property
    def datasource_key(self) -> str:
        return self._datasource_key

    @property
    def language(self) -> LanguageDirection:
        return self._language

    @property
    def footer(self) -> 'JTM.Footer':
        if self._footer is None:
            self._footer = self._parse_footer()
        return self._footer

    @property
    def properties(self) -> Optional[Properties]:
        return self.footer.properties if self.footer else None

    def _parse_footer(self) -> Optional['JTM.Footer']:
        if not os.path.exists(self._path):
            return None

        last_line = shell.tail_1(self._path).decode("utf-8")
        return JTM.Footer.parse(last_line)

    def reader(self) -> JTMReader:
        return JTMReader(self._path)

    def writer(self, properties: Dict[str, Union[str, List[str]]] = None) -> JTMWriter:
        return JTMWriter(self._path, properties or self.properties)

    def link(self, dest_path: str, symbolic: bool = False, overwrite: bool = True) -> 'JTM':
        output_path = shell.link(self._path, dest_path, symbolic=symbolic, overwrite=overwrite)
        return JTM(output_path)

    def __len__(self):
        return self.footer.get_total_count() if self.footer else 0

import json
import os
from collections import Counter
from typing import Dict, Optional, Set, TextIO
from typing import Generator, Any

from larakit import shell, LanguageDirection
from larakit.corpus._base import TranslationUnit, Properties, MultilingualCorpus, TUReader, TUWriter


class JTMReader(TUReader):
    def __init__(self, path: str):
        self._path = path
        self._file: Optional[TextIO] = None

    def __enter__(self) -> 'JTMReader':
        self._file = open(self._path, 'r', encoding='utf-8')
        return self

    def __iter__(self) -> Generator[TranslationUnit, None, None]:
        if self._file is None:
            raise IOError("Reader is not open.")

        for line in self._file:
            if not line.startswith(JTMCorpus.Footer.FOOTER_LINE_BEGIN):
                yield TranslationUnit.from_json(json.loads(line))

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.close()


class JTMWriter(TUWriter):
    def __init__(self, path: str, properties: Optional[Properties] = None):
        self._path = path
        self._file: Optional[TextIO] = None
        self._properties = properties
        self._counter: Counter[LanguageDirection] = Counter()

    def __enter__(self) -> 'JTMWriter':
        self._file = open(self._path, 'w', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._file.write(f'{JTMCorpus.Footer(self._counter, self._properties)}\n')
        self._file.close()

    def add_property(self, key: str, value: str):
        if self._properties is None:
            self._properties = Properties()

        self._properties.put(key, value)

    def write(self, tu: TranslationUnit):
        self._counter[tu.language] += 1
        self._file.write(json.dumps(tu.to_json(), ensure_ascii=False, separators=(',', ':')) + '\n')


class JTMCorpus(MultilingualCorpus):
    class Footer:
        FOOTER_LINE_BEGIN = ".footer"

        def __init__(self, counter: Optional[Counter[LanguageDirection]] = None,
                     properties: Optional[Properties] = None):
            self._counter: Counter[LanguageDirection] = counter if counter else Counter()
            self._properties: Optional[Properties] = properties

        @classmethod
        def parse(cls, line: str) -> 'JTMCorpus.Footer':
            if line.startswith(cls.FOOTER_LINE_BEGIN):
                json_part = line[len(cls.FOOTER_LINE_BEGIN):].strip()
                return cls.from_json(json.loads(json_part))

            raise ValueError("The final line does not start with the expected '.footer' prefix.")

        @classmethod
        def from_json(cls, data: Dict[str, Any]) -> 'JTMCorpus.Footer':
            counter = Counter({LanguageDirection.from_tuple(lang_tuple): lang_count
                               for lang_tuple, lang_count in data.get("counter", [])})

            properties_data: Optional[Dict] = data.get("properties", None)
            properties = Properties.from_json(properties_data) if properties_data else None
            return cls(counter, properties)

        @property
        def counter(self) -> Counter[LanguageDirection]:
            return self._counter

        @property
        def properties(self) -> Properties:
            return self._properties

        def get_total_count(self) -> int:
            return self._counter.total()

        def to_json(self) -> Dict[str, Any]:
            data: Dict[str, Any] = {
                "counter": [[lang.to_json(), count] for lang, count in self.counter.items()]}
            if self._properties:
                data["properties"] = self._properties.map

            return data

        def __str__(self) -> str:
            return f"{JTMCorpus.Footer.FOOTER_LINE_BEGIN}{json.dumps(self.to_json(), separators=(',', ':'))}"

    def __init__(self, path: str):
        self._path: str = path
        self._name: str = os.path.basename(path)
        self._footer: Optional[JTMCorpus.Footer] = None

    @property
    def path(self) -> str:
        return self._path

    @property
    def name(self) -> str:
        return self._name

    @property
    def languages(self) -> Set[LanguageDirection]:
        return set(self.footer.counter.keys())

    @property
    def footer(self) -> 'JTMCorpus.Footer':
        if self._footer is None:
            self._footer = self._parse_footer()

        return self._footer

    @property
    def properties(self) -> Optional[Properties]:
        return self.footer.properties if self.footer else None

    def _parse_footer(self) -> Optional['JTMCorpus.Footer']:
        if not os.path.exists(self._path):
            return None

        last_line = shell.tail_1(self._path).decode("utf-8")
        return JTMCorpus.Footer.parse(last_line)

    def reader(self) -> JTMReader:
        return JTMReader(self._path)

    def writer(self, properties: Optional[Properties] = None) -> JTMWriter:
        return JTMWriter(self._path, properties or self.properties)

    def __len__(self):
        return self.footer.get_total_count() if self.footer else 0

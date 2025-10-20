import os
from dataclasses import dataclass
from typing import Generator, Optional, Set, TextIO, List, Dict, Tuple, Iterator
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

from larakit import LanguageDirection, Language
from larakit.corpus._base import MultilingualCorpus, TUReader, TUWriter, TranslationUnit, Properties


def _local_name(tag: str) -> str:
    if tag is None:
        return ""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _get_lang(attrib: Dict[str, str]) -> Optional[str]:
    return attrib.get("{http://www.w3.org/XML/1998/namespace}lang") or attrib.get("lang")


def _normalize_segment(text: str) -> str:
    return text.replace("\n", " ").strip()


def _attr_escape(value: str) -> str:
    return xml_escape(value, {'"': '&quot;'})


class TMXReader(TUReader):
    @dataclass
    class _TUVData:
        lang: Optional[str]
        text: Optional[str]
        creation_date: Optional[str]
        change_date: Optional[str]

    def __init__(self, path: str):
        self._path: str = path
        self._file: Optional[TextIO] = None
        self._header_properties: Optional[Properties] = None
        self._header_srclang: Optional[str] = None

    def __enter__(self) -> 'TMXReader':
        self._file = open(self._path, 'r', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            self._file.close()

    def _parse_header(self, context: Iterator[Tuple[str, ET.Element]]) -> None:
        if self._header_properties:
            return

        self._header_properties = Properties()
        for event, elem in context:
            tag = _local_name(elem.tag)
            if event == 'start' and tag == 'header':
                self._header_srclang = elem.attrib.get("srclang")
            elif event == 'end' and tag == 'prop' and 'type' in elem.attrib:
                self._header_properties.put(elem.attrib['type'], "".join(elem.itertext()))
            elif event == 'end' and tag == 'header':
                elem.clear()
                return

    @staticmethod
    def _find_source_tuv_index(tuvs: List[_TUVData], source_lang: Optional[Language]) -> int:
        if not source_lang:
            return 0

        tuv_langs = [Language.from_string(tuv.lang) if tuv.lang else None for tuv in tuvs]

        # 1. Exact match
        for i, tuv_lang in enumerate(tuv_langs):
            if tuv_lang == source_lang:
                return i

        # 2. Generic match (e.g., source 'en' matches TUV 'en-US')
        for i, tuv_lang in enumerate(tuv_langs):
            if tuv_lang and source_lang.is_equal_or_more_generic_than(tuv_lang):
                return i

        # 3. Specific match (e.g., source 'en-US' matches TUV 'en')
        for i, tuv_lang in enumerate(tuv_langs):
            if tuv_lang and tuv_lang.is_equal_or_more_generic_than(source_lang):
                return i

        # 4. Fallback to the first TUV
        return 0

    @classmethod
    def _tuvs_from_element(cls, tu_element: ET.Element) -> List[_TUVData]:
        tuvs = []
        for tuv_elem in tu_element.findall('tuv'):
            seg_elem = tuv_elem.find('seg')
            if seg_elem is None:
                continue

            text = _normalize_segment("".join(seg_elem.itertext()))
            tuvs.append(cls._TUVData(
                lang=_get_lang(tuv_elem.attrib), text=text, creation_date=tuv_elem.attrib.get("creationdate"),
                change_date=tuv_elem.attrib.get("changedate")))
        return tuvs

    def _translation_units_from_element(self, tu_element: ET.Element) -> Generator[TranslationUnit, None, None]:
        tuvs = self._tuvs_from_element(tu_element)
        if len(tuvs) < 2:
            return

        # Determine source language, falling back from TU, header, or first TUV
        source_lang_tag = tu_element.attrib.get("srclang") or self._header_srclang
        if not source_lang_tag and tuvs[0].lang:
            source_lang_tag = tuvs[0].lang

        source_lang = Language.from_string(source_lang_tag) if source_lang_tag else None
        source_tuv = tuvs.pop(self._find_source_tuv_index(tuvs, source_lang))

        # Extract TU-level metadata
        tu_props = Properties()
        for prop_elem in tu_element.findall('prop'):
            prop_type = prop_elem.attrib.get('type')
            if prop_type:
                tu_props.put(prop_type, "".join(prop_elem.itertext()))

        # Yield a TranslationUnit for each remaining target TUV
        for target_tuv in tuvs:
            if not all([source_tuv.lang, source_tuv.text, target_tuv.lang, target_tuv.text]):
                continue

            lang_dir = LanguageDirection.from_tuple((source_tuv.lang, target_tuv.lang))
            yield TranslationUnit(
                language=lang_dir, sentence=source_tuv.text, translation=target_tuv.text,
                tuid=tu_element.attrib.get("tuid"),
                creation_date=target_tuv.creation_date or tu_element.attrib.get("creationdate"),
                change_date=target_tuv.change_date or tu_element.attrib.get("changedate"),
                properties=Properties(tu_props) if tu_props.size() > 0 else None)

    def __iter__(self) -> Generator[TranslationUnit, None, None]:
        if self._file is None:
            raise IOError("Reader is not open.")

        context = ET.iterparse(self._file, events=("start", "end"))
        self._parse_header(context)
        for event, elem in context:
            if event == 'end' and _local_name(elem.tag) == 'tu':
                yield from self._translation_units_from_element(elem)
                elem.clear()

    @property
    def header_properties(self) -> Optional[Properties]:
        return self._header_properties

    @property
    def header_source_language(self) -> Optional[str]:
        return self._header_srclang


class TMXWriter(TUWriter):
    def __init__(self, path: str, header_properties: Optional[Properties] = None):
        self._path: str = path
        self._file: Optional[TextIO] = None
        self._header_written: bool = False
        self._header_properties = header_properties

    def __enter__(self) -> 'TMXWriter':
        self._file = open(self._path, 'w', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            if not self._header_written:
                self._write_header(None)
            self._file.write("  </body>\n</tmx>\n")
            self._file.close()

    def add_property(self, key: str, value: str) -> None:
        if self._header_properties is None:
            self._header_properties = Properties()
        self._header_properties.put(key, value)

    def write(self, tu: TranslationUnit) -> None:
        if self._file is None:
            raise IOError("Writer is not open.")

        src_lang, tgt_lang = tu.language.source, tu.language.target
        if not self._header_written:
            self._write_header(src_lang)

        attrs = ['datatype="plaintext"', f'srclang="{_attr_escape(src_lang.tag)}"']
        if tu.tuid:
            attrs.append(f'tuid="{_attr_escape(tu.tuid)}"')
        if tu.creation_date:
            attrs.append(f'creationdate="{_attr_escape(tu.creation_date)}"')
        if tu.change_date:
            attrs.append(f'changedate="{_attr_escape(tu.change_date)}"')

        self._file.write(f'    <tu {" ".join(attrs)}>\n')
        # TU-level properties
        if tu.properties is not None:
            for key in tu.properties.keys():
                values = tu.properties.values(key) or []
                for val in values:
                    self._file.write(f'      <prop type="{_attr_escape(key)}">{xml_escape(val)}</prop>\n')
        # TUVs
        self._write_tuv(src_lang, tu.sentence)
        self._write_tuv(tgt_lang, tu.translation)
        self._file.write("    </tu>\n")

    def _write_header(self, srclang: Optional[Language]) -> None:
        self._file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self._file.write('<tmx version="1.4">\n')
        header_attrs = ['datatype="plaintext"', 'o-tmf="LaraKit"', 'segtype="sentence"', 'adminlang="en"']
        if srclang:
            header_attrs.append(f'srclang="{_attr_escape(srclang.tag)}"')

        self._file.write(f'  <header {" ".join(header_attrs)}>\n')
        if self._header_properties is not None:
            for key in self._header_properties.keys():
                values = self._header_properties.values(key) or []
                for val in values:
                    self._file.write(f'    <prop type="{_attr_escape(key)}">{xml_escape(val)}</prop>\n')

        self._file.write('  </header>\n')
        self._file.write('  <body>\n')
        self._header_written = True

    def _write_tuv(self, lang: Language, segment: str) -> None:
        seg_text = _normalize_segment(segment)
        self._file.write(f'      <tuv xml:lang="{_attr_escape(lang.tag)}"><seg>{xml_escape(seg_text)}</seg></tuv>\n')


class TMXCorpus(MultilingualCorpus):
    def __init__(self, path: str):
        self._path: str = path
        self._name: str = os.path.splitext(os.path.basename(path))[0]
        self._languages: Optional[Set[LanguageDirection]] = None
        self._length: Optional[int] = None
        self._header_properties: Optional[Properties] = None

    @property
    def path(self) -> str:
        return self._path

    @property
    def name(self) -> str:
        return self._name

    @property
    def languages(self) -> Optional[Set[LanguageDirection]]:
        if not os.path.exists(self._path):
            return None

        if self._languages is None:
            langs: Set[LanguageDirection] = set()
            with TMXReader(self._path) as r:
                for tu in r:
                    langs.add(tu.language)
            self._languages = langs

        return self._languages

    def reader(self) -> TMXReader:
        return TMXReader(self._path)

    def writer(self, properties: Optional[Properties] = None) -> TMXWriter:
        return TMXWriter(self._path, properties or self.properties)

    @property
    def properties(self) -> Optional[Properties]:
        if not os.path.exists(self._path):
            return None

        if self._header_properties is not None:
            return self._header_properties
        with TMXReader(self._path) as r:
            for _ in r:
                break
            self._header_properties = r.header_properties if r.header_properties.size() > 0 else None

        return self._header_properties

    def __len__(self) -> int:
        if not os.path.exists(self._path):
            return 0

        if self._length is None:
            with TMXReader(self._path) as r:
                self._length = sum(1 for _ in r)
        return self._length

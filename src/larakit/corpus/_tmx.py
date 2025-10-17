import os
from typing import Generator, Optional, Set, TextIO, List, Dict, Tuple
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

from larakit import LanguageDirection
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


def _is_equal_or_more_generic(a: str, b: str) -> bool:
    # True if 'a' is equal to 'b' or 'a' is a generic prefix of 'b' (e.g., 'en' >= 'en-US')
    a_l = a.lower()
    b_l = b.lower()
    return a_l == b_l or b_l.startswith(a_l + "-")


def _is_equal_or_more_specific(a: str, b: str) -> bool:
    # True if 'a' is equal or more specific than 'b' (e.g., 'en-US' >= 'en')
    a_l = a.lower()
    b_l = b.lower()
    return a_l == b_l or a_l.startswith(b_l + "-")


class TMXReader(TUReader):
    def __init__(self, path: str):
        self._path = path
        self._file: Optional[TextIO] = None
        self._header_properties: Properties = Properties()
        self._header_srclang: Optional[str] = None

    def __enter__(self) -> 'TMXReader':
        self._file = open(self._path, 'r', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            self._file.close()

    def __iter__(self) -> Generator[TranslationUnit, None, None]:
        # pylint:disable=too-many-locals
        # pylint:disable=too-many-branches
        # pylint:disable=too-many-statements
        if self._file is None:
            raise IOError("Reader is not open.")

        context = ET.iterparse(self._file, events=("start", "end"))
        stack: List[Tuple[str, ET.Element]] = []

        tu_attrs: Dict[str, Optional[str]] = {}
        tu_properties: Optional[Properties] = None
        tuv_current: Optional[Dict[str, Optional[str]]] = None
        tuvs: List[Dict[str, Optional[str]]] = []

        # pylint:disable=too-many-nested-blocks
        for event, elem in context:
            tag = _local_name(elem.tag)

            if event == "start":
                stack.append((tag, elem))

                if tag == "header":
                    self._header_srclang = elem.attrib.get("srclang") or self._header_srclang

                elif tag == "tu":
                    tu_attrs = {
                        "tuid": elem.attrib.get("tuid"),
                        "srclang": elem.attrib.get("srclang"),
                        "creationdate": elem.attrib.get("creationdate"),
                        "changedate": elem.attrib.get("changedate"),
                    }
                    tu_properties = Properties()
                    tuvs = []

                elif tag == "tuv":
                    tuv_current = {
                        "lang": _get_lang(elem.attrib),
                        "creationdate": elem.attrib.get("creationdate"),
                        "changedate": elem.attrib.get("changedate"),
                        "text": None,
                    }

            else:
                parent_tag = stack[-2][0] if len(stack) > 1 else None

                if tag == "prop":
                    prop_type = elem.attrib.get("type")
                    if prop_type:
                        prop_val = "".join(elem.itertext())
                        if parent_tag == "header":
                            self._header_properties.put(prop_type, prop_val)
                        elif parent_tag == "tu" and tu_properties is not None:
                            tu_properties.put(prop_type, prop_val)
                    elem.clear()

                elif tag == "seg":
                    if parent_tag == "tuv" and tuv_current is not None:
                        seg_text = "".join(elem.itertext())
                        tuv_current["text"] = _normalize_segment(seg_text)
                    elem.clear()

                elif tag == "tuv":
                    if tuv_current is None or not tuv_current.get("lang"):
                        pass
                    else:
                        tuvs.append(tuv_current)
                    tuv_current = None
                    elem.clear()

                elif tag == "tu":
                    if tuvs and len(tuvs) >= 2:
                        source_lang = tu_attrs.get("srclang") or self._header_srclang
                        if not source_lang:
                            source_lang = tuvs[0]["lang"]

                        src_idx: Optional[int] = None
                        if source_lang:
                            for i, t in enumerate(tuvs):
                                if t["lang"] and t["lang"].lower() == source_lang.lower():
                                    src_idx = i
                                    break
                            if src_idx is None:
                                for i, t in enumerate(tuvs):
                                    if t["lang"] and _is_equal_or_more_generic(source_lang, t["lang"]):
                                        src_idx = i
                                        break
                            if src_idx is None:
                                for i, t in enumerate(tuvs):
                                    if t["lang"] and _is_equal_or_more_specific(t["lang"], source_lang):
                                        src_idx = i
                                        break

                        if src_idx is None:
                            src_idx = 0

                        source_tuv = tuvs.pop(src_idx)

                        # defaults from TU if TUV-level dates are missing
                        tu_creation = tu_attrs.get("creationdate")
                        tu_change = tu_attrs.get("changedate")

                        for t in tuvs:
                            if not t.get("lang") or t.get("text") is None or source_tuv.get("text") is None:
                                continue
                            src_tag = source_tuv["lang"]
                            tgt_tag = t["lang"]

                            lang = LanguageDirection.from_tuple((src_tag, tgt_tag))
                            creation = t.get("creationdate") or tu_creation
                            change = t.get("changedate") or tu_change

                            yield TranslationUnit(language=lang, sentence=source_tuv["text"], translation=t["text"],
                                                  tuid=tu_attrs.get("tuid"), creation_date=creation, change_date=change,
                                                  properties=Properties(tu_properties) if tu_properties else None)

                    elem.clear()
                    tu_attrs = {}
                    tu_properties = None
                    tuvs = []

                elif tag == "header":
                    elem.clear()

                stack.pop()

    @property
    def header_properties(self) -> Properties:
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

    def add_property(self, key: str, value: str):
        if self._header_properties is None:
            self._header_properties = Properties()
        self._header_properties.put(key, value)

    def write(self, tu: TranslationUnit):
        if self._file is None:
            raise IOError("Writer is not open.")

        src_tag, tgt_tag = self._lang_tuple(tu.language)

        if not self._header_written:
            self._write_header(src_tag)

        # TU start with attributes
        attrs = []
        if tu.tuid is not None:
            attrs.append(f'tuid="{_attr_escape(tu.tuid)}"')
        if src_tag:
            attrs.append(f'srclang="{_attr_escape(src_tag)}"')
        attrs.append('datatype="plaintext"')
        if tu.creation_date is not None:
            attrs.append(f'creationdate="{_attr_escape(tu.creation_date)}"')
        if tu.change_date is not None:
            attrs.append(f'changedate="{_attr_escape(tu.change_date)}"')

        self._file.write(f'    <tu {" ".join(attrs)}>\n')

        # TU-level properties
        if tu.properties is not None:
            for key in tu.properties.keys():
                values = tu.properties.values(key) or []
                for val in values:
                    self._file.write(f'      <prop type="{_attr_escape(key)}">{xml_escape(val)}</prop>\n')

        # TUVs
        self._write_tuv(src_tag, tu.sentence)
        self._write_tuv(tgt_tag, tu.translation)

        self._file.write("    </tu>\n")

    def _write_header(self, srclang: Optional[str]):
        self._file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self._file.write('<tmx version="1.4">\n')
        header_attrs = [
            'datatype="plaintext"',
            'o-tmf="LaraKit"',
            'segtype="sentence"',
            'adminlang="en"',
        ]
        if srclang:
            header_attrs.append(f'srclang="{_attr_escape(srclang)}"')

        self._file.write(f'  <header {" ".join(header_attrs)}>\n')

        if self._header_properties is not None:
            for key in self._header_properties.keys():
                values = self._header_properties.values(key) or []
                for val in values:
                    self._file.write(f'    <prop type="{_attr_escape(key)}">{xml_escape(val)}</prop>\n')

        self._file.write('  </header>\n')
        self._file.write('  <body>\n')
        self._header_written = True

    def _write_tuv(self, lang: Optional[str], segment: str):
        # xml:lang is a reserved prefix; no need to declare namespace
        seg_text = _normalize_segment(segment)
        if lang is None:
            lang = ""  # be robust, though SRX expects lang; empty makes it obvious
        self._file.write(f'      <tuv xml:lang="{_attr_escape(lang)}"><seg>{xml_escape(seg_text)}</seg></tuv>\n')

    @staticmethod
    def _lang_tuple(direction: LanguageDirection) -> Tuple[str, str]:
        # Rely on to_json() which returns a (src, tgt) tuple in existing codebase
        data = direction.to_json()
        if isinstance(data, (list, tuple)) and len(data) == 2:
            return data[0], data[1]
        # Fallback: try attributes
        src = getattr(direction, "source", None)
        tgt = getattr(direction, "target", None)
        return src or "", tgt or ""


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
    def languages(self) -> Set[LanguageDirection]:
        if self._languages is None:
            langs: Set[LanguageDirection] = set()
            try:
                with TMXReader(self._path) as r:
                    for tu in r:
                        langs.add(tu.language)
            except FileNotFoundError:
                langs = set()
            self._languages = langs
        return self._languages

    def reader(self) -> TMXReader:
        return TMXReader(self._path)

    def writer(self, properties: Optional[Properties] = None) -> TMXWriter:
        header_props = properties or self.properties
        return TMXWriter(self._path, header_props)

    @property
    def properties(self) -> Optional[Properties]:
        if self._header_properties is not None:
            return self._header_properties
        try:
            with TMXReader(self._path) as r:
                # Consume nothing; header props are exposed after initialization via __iter__ setup
                # But TMXReader collects header props during iteration. Force a small parse to header:
                for _ in r:
                    # After first iteration header is surely parsed; we can break immediately
                    break
                self._header_properties = r.header_properties if r.header_properties.size() > 0 else None
        except FileNotFoundError:
            self._header_properties = None
        return self._header_properties

    def __len__(self) -> int:
        if self._length is None:
            count = 0
            try:
                with TMXReader(self._path) as r:
                    for _ in r:
                        count += 1
            except FileNotFoundError:
                count = 0
            self._length = count
        return self._length

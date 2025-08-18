import os
from typing import Set, Optional, TextIO, Generator

from larakit import LanguageDirection
from larakit.corpus._base import MultilingualCorpus, TUReader, TranslationUnit, TUWriter


class ParallelCorpusReader(TUReader):
    def __init__(self, language: LanguageDirection, source: str, target: str):
        self._language: LanguageDirection = language
        self._source: str = source
        self._target: str = target

        self._source_file: Optional[TextIO] = None
        self._target_file: Optional[TextIO] = None

    def __enter__(self) -> 'ParallelCorpusReader':
        self._source_file = open(self._source, 'r', encoding='utf-8')
        self._target_file = open(self._target, 'r', encoding='utf-8')
        return self

    def __iter__(self) -> Generator[TranslationUnit, None, None]:
        if self._source_file is None or self._target_file is None:
            raise IOError("Reader is not open.")

        for src_line, tgt_line in zip(self._source_file, self._target_file):
            yield TranslationUnit(language=self._language, sentence=src_line.strip(), translation=tgt_line.strip())

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._source_file.close()
        self._target_file.close()


class ParallelCorpusWriter(TUWriter):
    def __init__(self, language: LanguageDirection, source: str, target: str):
        self._language: LanguageDirection = language
        self._source: str = source
        self._target: str = target

        self._source_file: Optional[TextIO] = None
        self._target_file: Optional[TextIO] = None

    def __enter__(self) -> 'ParallelCorpusWriter':
        self._source_file = open(self._source, 'w', encoding='utf-8')
        self._target_file = open(self._target, 'w', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._source_file:
            self._source_file.close()
        if self._target_file:
            self._target_file.close()

    @staticmethod
    def _normalize(text: str) -> str:
        return text.replace('\n', ' ').strip()

    def write(self, tu: TranslationUnit):
        self._source_file.write(self._normalize(tu.sentence) + '\n')
        self._target_file.write(self._normalize(tu.translation) + '\n')


class ParallelCorpus(MultilingualCorpus):
    def __init__(self, source: str, target: str):
        self._source: str = source
        self._target: str = target

        source_parts = os.path.splitext(os.path.basename(source))
        target_parts = os.path.splitext(os.path.basename(target))
        self._name = source_parts[0]
        self._language: LanguageDirection = LanguageDirection.from_tuple((source_parts[1][1:], target_parts[1][1:]))

    @property
    def name(self) -> str:
        return self._name

    @property
    def languages(self) -> Set[LanguageDirection]:
        return {self._language}

    def reader(self) -> ParallelCorpusReader:
        return ParallelCorpusReader(self._language, self._source, self._target)

    def writer(self) -> ParallelCorpusWriter:
        return ParallelCorpusWriter(self._language, self._source, self._target)

import tempfile
import unittest
from typing import List, Optional

from larakit import Language, LanguageDirection
from larakit.corpus import MultilingualCorpus, TranslationUnit


class TestCorpus(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.corpus_name = 'example_corpus'
        self.source_lang = Language.from_string('en')
        self.target_lang = Language.from_string('fr')

        self.language_direction = LanguageDirection(self.source_lang, self.target_lang)
        self.tu = TranslationUnit(language=self.language_direction, sentence='Hello', translation='Bonjour')

        self.corpus: Optional[MultilingualCorpus] = None

    def tearDown(self):
        self.temp_dir.cleanup()

    def _read(self):
        with self.corpus.reader() as reader:
            return list(reader)

    def _write(self, tus: List[TranslationUnit]):
        with self.corpus.writer() as writer:
            for tu in tus:
                writer.write(tu)

    def _single_write(self):
        self._write([self.tu])

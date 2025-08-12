import tempfile
import unittest
from typing import Optional

from larakit.corpus import TranslationUnit, MultilingualCorpus
from larakit.lang import LanguageDirection, Language


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

    def _single_write(self):
        with self.corpus.writer() as writer:
            writer.write(self.tu)

    def _read_all(self):
        with self.corpus.reader() as reader:
            return list(reader)

    def _test_writer_and_reader(self):
        self._single_write()
        units = self._read_all()

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, self.tu.sentence)
        self.assertEqual(units[0].translation, self.tu.translation)

    def _test_filename_parsing(self):
        self.assertEqual(self.corpus.name, self.corpus_name)

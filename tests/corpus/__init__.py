import tempfile
import unittest
from typing import List, Optional

from larakit import Language, LanguageDirection
from larakit.corpus import MultilingualCorpus, TranslationUnit, Properties


class TestCorpus(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.corpus_name = 'example_corpus'
        self.source_lang = Language.from_string('en')
        self.target_lang = Language.from_string('fr')

        self.language_direction = LanguageDirection(self.source_lang, self.target_lang)
        self.tu = TranslationUnit(language=self.language_direction, sentence='Hello', translation='Bonjour')
        self.tu_properties = Properties.from_json({"note": "test"})
        self.tu_with_properties = TranslationUnit(language=self.language_direction, sentence='Goodbye',
                                                  translation='Au revoir', properties=self.tu_properties)

        self.corpus: Optional[MultilingualCorpus] = None

    def tearDown(self):
        self.temp_dir.cleanup()

    def _read(self) -> List[TranslationUnit]:
        with self.corpus.reader() as reader:
            return list(reader)

    def _write(self, tus: List[TranslationUnit]):
        with self.corpus.writer() as writer:
            for tu in tus:
                writer.write(tu)

    def _single_write(self):
        self._write([self.tu])

    def _test_languages_parsing(self):
        self._single_write()
        self.assertEqual(self.corpus.languages, {self.language_direction})

    def _test_single_tu_writer_and_reader(self):
        self._single_write()
        units = self._read()

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, self.tu.sentence)
        self.assertEqual(units[0].translation, self.tu.translation)

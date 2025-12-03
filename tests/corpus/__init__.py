import tempfile
import unittest
from typing import List, Optional

from larakit import Language, LanguageDirection
from larakit.corpus import MultilingualCorpus, TranslationUnit, Properties


class TestCorpus(unittest.TestCase):
    def setUp(self):
        self.temp_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()

        self.corpus_name: str = 'example_corpus'
        self.source_lang: Language = Language.from_string('en')
        self.target_lang: Language = Language.from_string('fr')

        self.language_direction: LanguageDirection = LanguageDirection(self.source_lang, self.target_lang)
        self.tu: TranslationUnit = TranslationUnit(language=self.language_direction, sentence='Hello',
                                                   translation='Bonjour')
        self.tu_properties: Properties = Properties.from_json({"note": "test"})
        self.tu_with_properties: TranslationUnit = TranslationUnit(language=self.language_direction, sentence='Night',
                                                                   translation='Nuit', properties=self.tu_properties)

        self.corpus: Optional[MultilingualCorpus] = None

    def tearDown(self):
        self.temp_dir.cleanup()

    def _read(self) -> List[TranslationUnit]:
        with self.corpus.reader() as reader:
            return list(reader)

    def _write(self, tus: List[TranslationUnit]) -> None:
        with self.corpus.writer() as writer:
            for tu in tus:
                writer.write(tu)

    def _single_write(self) -> None:
        self._write([self.tu])

    def _test_languages_parsing(self) -> None:
        self._single_write()
        self.assertEqual(self.corpus.languages, {self.language_direction})

    def _test_single_tu_writer_and_reader(self) -> None:
        self._single_write()
        units = self._read()

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, self.tu.sentence)
        self.assertEqual(units[0].translation, self.tu.translation)

    def _test_multiple_tu_writer_and_reader(self) -> None:
        tus_to_write = [self.tu for _ in range(10)]
        self._write(tus_to_write)
        units = self._read()

        self.assertEqual(len(units), len(tus_to_write))
        for read_tu, written_tu in zip(units, tus_to_write):
            self.assertEqual(read_tu, written_tu)

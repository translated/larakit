import os
import tempfile
import unittest

from larakit.corpus import TranslationUnit
from larakit.corpus.parallel import ParallelCorpus
from larakit.lang import LanguageDirection


class TestParallelCorpus(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_file_path = os.path.join(self.temp_dir.name, "example.en")
        self.target_file_path = os.path.join(self.temp_dir.name, "example.fr")

        self.parallel_corpus = ParallelCorpus(self.source_file_path, self.target_file_path)
        self.language_direction = LanguageDirection.from_tuple(("en", "fr"))
        self.tu = TranslationUnit(language=self.language_direction, sentence="Hello", translation="Bonjour")

    def test_writer_and_reader(self):
        with self.parallel_corpus.writer() as writer:
            writer.write(self.tu)

        with self.parallel_corpus.reader() as reader:
            units = list(reader)

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, self.tu.sentence)
        self.assertEqual(units[0].translation, self.tu.translation)

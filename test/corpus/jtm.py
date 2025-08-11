import tempfile
import unittest

from larakit.corpus import TranslationUnit, Properties
from larakit.corpus.jtm import JTMCorpus
from larakit.lang import LanguageDirection


class TestJTMCorpus(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=True)
        self.temp_file.close()

        self.jtm = JTMCorpus(self.temp_file.name)
        self.language_direction = LanguageDirection.from_tuple(("en", "fr"))
        self.tu = TranslationUnit(language=self.language_direction, sentence="Hello", translation="Bonjour")

    def test_writer_and_reader(self):
        properties = Properties()
        properties.put("source", "test")
        with self.jtm.writer(properties) as writer:
            writer.write(self.tu)

        with self.jtm.reader() as reader:
            units = list(reader)

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, self.tu.sentence)
        self.assertEqual(units[0].translation, self.tu.translation)
        self.assertEqual(self.jtm.properties.get("source"), "test")

    def test_footer_write_and_read(self):
        with self.jtm.writer() as writer:
            writer.write(self.tu)

        corpus = JTMCorpus(self.temp_file.name)
        self.assertEqual(corpus.footer.get_total_count(), 1)
        self.assertEqual(corpus.footer.counter[self.language_direction], 1)

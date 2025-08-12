import os

from larakit.corpus import Properties
from larakit.corpus.jtm import JTMCorpus
from test.corpus._base import TestCorpus


class TestJTMCorpus(TestCorpus):
    def setUp(self):
        super().setUp()

        self.jtm_path = os.path.join(self.temp_dir.name, f'{self.corpus_name}.jtm')
        self.corpus = JTMCorpus(path=self.jtm_path)

    def test_writer_and_reader(self):
        properties = Properties()
        properties.put("source", "test")
        with self.corpus.writer(properties) as writer:
            writer.write(self.tu)

        units = self._read_all()

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, self.tu.sentence)
        self.assertEqual(units[0].translation, self.tu.translation)
        self.assertEqual(self.corpus.properties.get("source"), "test")

    def test_footer_write_and_read(self):
        self._single_write()

        same_corpus = JTMCorpus(self.corpus.path)
        self.assertEqual(same_corpus.footer.get_total_count(), 1)
        self.assertEqual(same_corpus.footer.counter[self.language_direction], 1)

    def test_languages_parsing(self):
        self._single_write()
        self.assertEqual(self.corpus.languages, {self.language_direction})

    def test_writer_and_reader(self):
        self._test_writer_and_reader()

    def test_filename_parsing(self):
        self._test_filename_parsing()

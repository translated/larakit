import os

from corpus import TestCorpus

from larakit.corpus import JTMCorpus


class TestJTMCorpus(TestCorpus):
    def setUp(self):
        super().setUp()

        self.jtm_filename: str = f'{self.corpus_name}.jtm'
        self.jtm_path: str = os.path.join(self.temp_dir.name, self.jtm_filename)
        self.corpus: JTMCorpus = JTMCorpus(path=self.jtm_path)

    def test_writer_and_reader(self):
        self._write([self.tu_with_properties])
        units = self._read()
        self.assertEqual(units[0].properties, self.tu_properties)

    def test_footer_write_and_read(self):
        self._single_write()

        same_corpus = JTMCorpus(self.corpus.path)
        self.assertEqual(same_corpus.footer.get_total_count(), 1)
        self.assertEqual(same_corpus.footer.counter[self.language_direction], 1)

    def test_languages_parsing(self):
        self._test_languages_parsing()

    def test_jtm_single_writer_and_reader(self):
        self._test_single_tu_writer_and_reader()

    def test_filename_parsing(self):
        self.assertEqual(self.corpus.name, self.jtm_filename)

    def test_multiple_tu_writer_and_reader(self):
        self._test_multiple_tu_writer_and_reader()

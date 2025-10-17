import os

from corpus import TestCorpus

from larakit.corpus import TMXCorpus


class TestTMXCorpus(TestCorpus):
    def setUp(self):
        super().setUp()

        self.tmx_filename: str = f'{self.corpus_name}.tmx'
        self.tmx_path: str = os.path.join(self.temp_dir.name, self.tmx_filename)
        self.corpus: TMXCorpus = TMXCorpus(path=self.tmx_path)

    def test_writer_and_reader(self):
        self._write([self.tu_with_properties])
        units = self._read()
        self.assertEqual(units[0].properties, self.tu_properties)

    def test_footer_write_and_read(self):
        self._single_write()

        same_corpus = TMXCorpus(self.corpus.path)
        self.assertEqual(len(same_corpus), 1)
        self.assertTrue(self.language_direction in same_corpus.languages)

    def test_languages_parsing(self):
        self._single_write()
        self.assertEqual(self.corpus.languages, {self.language_direction})

    def test_jtm_single_writer_and_reader(self):
        self._test_parallel_single_writer_and_reader()

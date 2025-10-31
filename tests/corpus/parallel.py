import os

from corpus import TestCorpus

from larakit.corpus import TranslationUnit, ParallelCorpus


class TestParallelCorpus(TestCorpus):
    def setUp(self):
        super().setUp()

        self.source_file_path = os.path.join(self.temp_dir.name, f'{self.corpus_name}.{self.source_lang}')
        self.target_file_path = os.path.join(self.temp_dir.name, f'{self.corpus_name}.{self.target_lang}')
        self.corpus = ParallelCorpus(self.source_file_path, self.target_file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_empty_corpus(self):
        with open(self.source_file_path, 'w', encoding='utf-8') as f:
            f.write('')
        with open(self.target_file_path, 'w', encoding='utf-8') as f:
            f.write('')

        units = self._read()
        self.assertEqual(len(units), 0)

    def test_writer_normalization(self):
        tu_with_newline = TranslationUnit(language=self.language_direction, sentence='This is\na test.',
                                          translation='Ceci est\nun test.', )

        with self.corpus.writer() as writer:
            writer.write(tu_with_newline)

        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, 'This is a test.')
        self.assertEqual(units[0].translation, 'Ceci est un test.')

    def test_languages_parsing(self):
        self.assertEqual(self.corpus.languages, {self.language_direction})

    def test_parallel_single_writer_and_reader(self):
        self._test_single_tu_writer_and_reader()

    def test_multiple_tu_writer_and_reader(self):
        self._test_multiple_tu_writer_and_reader()

    def test_filename_parsing(self):
        self.assertEqual(self.corpus.name, self.corpus_name)

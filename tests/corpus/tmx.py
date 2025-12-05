import os

from corpus import TestCorpus

from larakit import Language
from larakit.corpus import TMXCorpus, TranslationUnit


class TestTMXCorpus(TestCorpus):
    _ITALIAN: Language = Language.from_string("it")
    _SPANISH: Language = Language.from_string("es")
    _ENGLISH: Language = Language.from_string("en")
    _FRENCH: Language = Language.from_string("fr")
    _AMERICAN_ENGLISH: Language = Language.from_string("en-US")

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
        self._test_languages_parsing()

    def test_jtm_single_writer_and_reader(self):
        self._test_single_tu_writer_and_reader()

    def _write_raw_tmx(self, body_content: str, srclang: str = "en"):
        tmx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <tmx version="1.4">
        <header srclang="{srclang}" adminlang="en" segtype="sentence" datatype="plaintext" />
        <body>
        {body_content}
        </body>
        </tmx>
        """
        with open(self.tmx_path, 'w', encoding='utf-8') as f:
            f.write(tmx_content)

    def _write_raw_tmx_simple(self, sentence: str, translation: str = "Questo è un test.",
                              src_lang: str = "en", tgt_lang: str = "it", tu_srclang: str = "en"):
        tu_content = f"""
        <tu srclang="{tu_srclang}" datatype="plaintext">
          <tuv xml:lang="{src_lang}"><seg>{sentence}</seg></tuv>
          <tuv xml:lang="{tgt_lang}"><seg>{translation}</seg></tuv>
        </tu>
        """
        self._write_raw_tmx(tu_content, srclang=tu_srclang)

    def test_reader_control_character(self):
        self._write_raw_tmx_simple(sentence="Hello\f")
        units = self._read()
        self.assertEqual(units[0].sentence, "Hello")

    def test_reader_new_line_raw(self):
        self._write_raw_tmx_simple(sentence='Hello\nHow are you?')
        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, 'Hello\nHow are you?')

    def test_reader_writer_new_line(self):
        sentence = 'Hello\nHow are you?'
        translation = 'Bonjour\nComment ça va?'
        self._write([TranslationUnit(language=self.language_direction, sentence=sentence, translation=translation)])
        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, sentence)
        self.assertEqual(units[0].translation, translation)

    def test_writer_control_character(self):
        self._write(
            [TranslationUnit(language=self.language_direction, sentence='Hello\f', translation='Bonjour')])
        units = self._read()
        self.assertEqual(units[0].sentence, "Hello")

    def test_reader_control_xml_entity(self):
        self._write_raw_tmx_simple(sentence="&#x0C;")
        units = self._read()
        self.assertEqual(units[0].sentence, " ")

    def test_writer_control_xml_entity(self):
        self._write([TranslationUnit(language=self.language_direction, sentence='&#x0C;', translation='Bonjour')])
        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, " ")

    def test_reader_4_byte_character(self):
        char = "𩸽"  # U+29E3D
        self._write_raw_tmx_simple(sentence=char)
        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, char)

    def test_reader_4_byte_character_entity(self):
        char = "𩸽"  # U+29E3D
        entity = "&#x29e3d;"
        self._write_raw_tmx_simple(sentence=entity)
        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, char)

    def test_writer_4_byte_character(self):
        char = "𩸽"  # U+29E3D
        tu = TranslationUnit(self.language_direction, char, "ok")
        self._write([tu])
        with open(self.tmx_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(f"<seg>{char}</seg>", content)
        self.assertIn("<seg>ok</seg>", content)
        self.assertNotIn("&#x29e3d;", content)

    def test_generic_tu_source_lang(self):
        sentence = "This is a test with a generic source language."
        self._write_raw_tmx_simple(sentence=sentence, translation="Questo è un test.",
                                   src_lang="en-US", tgt_lang="it", tu_srclang="en")
        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, sentence)
        self.assertEqual(units[0].language.source, self._AMERICAN_ENGLISH)
        self.assertEqual(units[0].language.target, self._ITALIAN)

    def test_generic_tuv_lang(self):
        sentence = "This is a test with a generic TUV language."
        self._write_raw_tmx_simple(sentence=sentence, translation="Questo è un test.",
                                   src_lang="en", tgt_lang="it", tu_srclang="en-US")

        units = self._read()
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, sentence)
        self.assertEqual(units[0].language.source, self._ENGLISH)
        self.assertEqual(units[0].language.target, self._ITALIAN)

    def test_single_tuv_and_empty_segment(self):
        tu1 = """
        <tu srclang="fr">
          <tuv xml:lang="fr"><seg>Ceci est un test.</seg></tuv>
          <tuv xml:lang="it"><seg></seg></tuv>
        </tu>
        """  # Skipped (empty segment)
        tu2 = """
        <tu srclang="en">
          <tuv xml:lang="it"><seg>Questo è un test.</seg></tuv>
        </tu>
        """  # Skipped (len(tuvs) < 2)
        tu3 = """
        <tu srclang="en">
          <tuv xml:lang="es"><seg>Esta es una prueba.</seg></tuv>
          <tuv xml:lang="en"><seg>This is a test.</seg></tuv>
        </tu>
        """  # Read (en -> es)

        self._write_raw_tmx(tu1 + tu2 + tu3, srclang="en")
        units = self._read()

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].sentence, "This is a test.")
        self.assertEqual(units[0].translation, "Esta es una prueba.")
        self.assertEqual(units[0].language.source, self._ENGLISH)
        self.assertEqual(units[0].language.target, self._SPANISH)

    def test_missing_src_tuv(self):
        es_seg = "Esta es una prueba."
        it_seg = "Questo è un test."
        fr_seg = "Ceci est un test."
        tu_content = f"""
        <tu srclang="en">
          <tuv xml:lang="es"><seg>{es_seg}</seg></tuv>
          <tuv xml:lang="it"><seg>{it_seg}</seg></tuv>
          <tuv xml:lang="fr"><seg>{fr_seg}</seg></tuv>
        </tu>
        """
        self._write_raw_tmx(tu_content, srclang="en")
        units = self._read()

        # Source falls back to the first TUV (es)
        self.assertEqual(len(units), 2)
        self.assertEqual(units[0].sentence, es_seg)
        self.assertEqual(units[0].translation, it_seg)
        self.assertEqual(units[0].language.source, self._SPANISH)
        self.assertEqual(units[0].language.target, self._ITALIAN)

        self.assertEqual(units[1].sentence, es_seg)
        self.assertEqual(units[1].translation, fr_seg)
        self.assertEqual(units[1].language.source, self._SPANISH)
        self.assertEqual(units[1].language.target, self._FRENCH)

    def test_invalid_language_tag(self):
        self._write_raw_tmx_simple(sentence="This is a test", translation="Questo è un test.",
                                   src_lang="en", tgt_lang="Italian", tu_srclang="en")
        with self.assertRaises(Exception):
            self._read()

    def test_multiple_tu_writer_and_reader(self):
        self._test_multiple_tu_writer_and_reader()

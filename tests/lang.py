import unittest

from larakit import Language, LanguageDirection


class TestLanguage(unittest.TestCase):
    def test_lt(self):
        self.assertLess(Language.from_string("de"), Language.from_string("en"))
        self.assertLess(Language.from_string("en"), Language.from_string("en-US"))
        self.assertFalse(Language.from_string("it") < Language.from_string("it"))

    def test_lt_non_language_operand(self):
        self.assertEqual(Language.from_string("en").__lt__("en"), NotImplemented)
        with self.assertRaises(TypeError):
            _ = Language.from_string("en") < "en"

    def test_sorted(self):
        languages = [Language.from_string(s) for s in ("it", "en-US", "de", "zh-Hant", "en")]
        sorted_tags = [language.tag for language in sorted(languages)]
        self.assertEqual(sorted_tags, ["de", "en", "en-US", "it", "zh-Hant"])


class TestLanguageDirection(unittest.TestCase):
    def test_lt(self):
        self.assertLess(LanguageDirection.from_string("de__en"), LanguageDirection.from_string("en__de"))
        self.assertLess(LanguageDirection.from_string("en__de"), LanguageDirection.from_string("en__it"))
        self.assertFalse(LanguageDirection.from_string("en__it") < LanguageDirection.from_string("en__it"))

    def test_lt_non_direction_operand(self):
        direction = LanguageDirection.from_string("en__it")
        self.assertEqual(direction.__lt__("en__it"), NotImplemented)
        with self.assertRaises(TypeError):
            _ = direction < "en__it"

    def test_sorted(self):
        directions = [LanguageDirection.from_string(s) for s in ("it__en", "en__it", "en__de", "de__en")]
        sorted_strings = [str(direction) for direction in sorted(directions)]
        self.assertEqual(sorted_strings, ["de__en", "en__de", "en__it", "it__en"])

    def test_ordered(self):
        self.assertEqual(str(LanguageDirection.from_string("en__de").ordered), "de__en")
        self.assertEqual(str(LanguageDirection.from_string("zh-Hant__en").ordered), "en__zh-Hant")
        self.assertEqual(str(LanguageDirection.from_string("it-IT__en-US").ordered), "en-US__it-IT")

    def test_ordered_returns_self_when_ordered(self):
        direction = LanguageDirection.from_string("de__en")
        self.assertIs(direction.ordered, direction)

    def test_str(self):
        self.assertEqual(str(LanguageDirection.from_tuple(("en-US", "it-IT"))), "en-US__it-IT")
        self.assertEqual(str(LanguageDirection.from_tuple(("zh-Hant", "en"))), "zh-Hant__en")
        self.assertEqual(str(LanguageDirection.from_tuple(("en", "it"))), "en__it")

    def test_from_string(self):
        direction = LanguageDirection.from_string("en-US__it")
        self.assertEqual(direction.source.tag, "en-US")
        self.assertEqual(direction.target.tag, "it")

        direction = LanguageDirection.from_string("zh-Hant__en")
        self.assertEqual(direction.source.script, "Hant")
        self.assertEqual(direction.target.tag, "en")

    def test_from_string_round_trip(self):
        for pair in (("en", "it"), ("en-US", "it-IT"), ("zh-Hant", "en")):
            direction = LanguageDirection.from_tuple(pair)
            self.assertEqual(LanguageDirection.from_string(str(direction)), direction)

    def test_from_string_invalid(self):
        for string in ("en", "a__b__c", "__it", "en__", "__", ""):
            with self.assertRaises(ValueError, msg=f"string: '{string}'"):
                LanguageDirection.from_string(string)

    def test_is_language_only(self):
        self.assertTrue(LanguageDirection.from_string("en__it").is_language_only())
        self.assertFalse(LanguageDirection.from_string("en-US__it").is_language_only())
        self.assertFalse(LanguageDirection.from_string("en__it-IT").is_language_only())
        self.assertFalse(LanguageDirection.from_string("zh-Hant__en").is_language_only())

    def test_as_language_only(self):
        direction = LanguageDirection.from_string("en-US__it-IT")
        self.assertEqual(direction.as_language_only(), LanguageDirection.from_string("en__it"))

        direction = LanguageDirection.from_string("zh-Hant__en")
        self.assertEqual(direction.as_language_only(), LanguageDirection.from_string("zh__en"))

    def test_as_language_only_returns_self_when_language_only(self):
        direction = LanguageDirection.from_string("en__it")
        self.assertIs(direction.as_language_only(), direction)

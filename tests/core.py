import json
import os
import tempfile
import unittest

from larakit import Namespace, StatefulNamespace


class NamespaceUpdateTest(unittest.TestCase):
    def test_update_with_dict(self):
        ns = Namespace(a=1, b=2)
        ns.update({'b': 20, 'c': 30})

        self.assertEqual({'a': 1, 'b': 20, 'c': 30}, ns.to_json())

    def test_update_with_kwargs(self):
        ns = Namespace(a=1)
        ns.update({'b': 2}, c=3, a=10)

        self.assertEqual({'a': 10, 'b': 2, 'c': 3}, ns.to_json())

    def test_update_with_namespace(self):
        ns = Namespace(a=1)
        ns.update(Namespace(b=Namespace(c=2)))

        self.assertIsInstance(ns.b, Namespace)
        self.assertEqual({'a': 1, 'b': {'c': 2}}, ns.to_json())

    def test_update_with_pairs(self):
        ns = Namespace()
        ns.update([('a', 1), ('b', 2)])

        self.assertEqual({'a': 1, 'b': 2}, ns.to_json())

    def test_update_with_none(self):
        ns = Namespace(a=1)
        ns.update()
        ns.update(None)

        self.assertEqual({'a': 1}, ns.to_json())

    def test_update_parses_nested_values(self):
        ns = Namespace()
        ns.update({'a': {'b': 1}, 'c': [{'d': 2}]})

        self.assertIsInstance(ns.a, Namespace)
        self.assertEqual(1, ns.a.b)
        self.assertIsInstance(ns.c[0], Namespace)
        self.assertEqual({'a': {'b': 1}, 'c': [{'d': 2}]}, ns.to_json())

    def test_update_rejects_private_keys(self):
        ns = Namespace(a=1)

        with self.assertRaises(KeyError):
            ns.update({'_private': 1})
        with self.assertRaises(KeyError):
            ns.update(_private=1)

        self.assertEqual({'a': 1}, ns.to_json())


class StatefulNamespaceUpdateTest(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()
        self._path = os.path.join(self._tmp_dir, 'state.json')

    def tearDown(self):
        if os.path.isfile(self._path):
            os.remove(self._path)
        os.rmdir(self._tmp_dir)

    def _read_state(self):
        with open(self._path, 'r', encoding='utf-8') as f_input:
            return json.load(f_input)

    def test_update_with_autosave(self):
        ns = StatefulNamespace(self._path, autosave=True, a=1)
        ns.update({'b': 2}, c=3)

        self.assertEqual({'a': 1, 'b': 2, 'c': 3}, self._read_state())

    def test_update_without_autosave(self):
        ns = StatefulNamespace(self._path, autosave=False, a=1)
        ns.update({'b': 2})

        self.assertFalse(os.path.isfile(self._path))

        ns.save()
        self.assertEqual({'a': 1, 'b': 2}, self._read_state())

    def test_autosave_restored_after_failed_update(self):
        ns = StatefulNamespace(self._path, autosave=True, a=1)

        with self.assertRaises(KeyError):
            ns.update({'_private': 1})

        self.assertTrue(ns.autosave)

        ns.set('b', 2)
        self.assertEqual({'a': 1, 'b': 2}, self._read_state())

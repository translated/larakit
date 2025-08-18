import os
import sys
import unittest


def main():
    loader = unittest.TestLoader()
    tests = loader.discover(os.path.dirname(__file__), pattern='[!_]*.py')
    flat_tests = []
    for suite_ in tests:
        flat_tests.extend(list(suite_))

    sorted_tests = sorted(flat_tests, key=lambda test: test.__class__.__name__)
    suite = unittest.TestSuite(sorted_tests)
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == "__main__":
    __larakit_dir__ = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))
    sys.path.insert(0, __larakit_dir__)

    main()

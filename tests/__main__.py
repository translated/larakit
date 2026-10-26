import os
import sys
import unittest


def main():
    loader = unittest.TestLoader()
    tests = loader.discover(os.path.dirname(__file__), pattern='[!_]*.py')
    flat_tests = [test for suite_ in tests for test in suite_]

    sorted_tests = sorted(flat_tests, key=lambda test: test.__class__.__name__)
    suite = unittest.TestSuite(sorted_tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    __src_dir__ = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'src'))
    sys.path.insert(0, __src_dir__)

    main()

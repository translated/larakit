import os
import unittest

if __name__ == "__main__":
    suite = unittest.TestLoader().discover(os.path.dirname(__file__), pattern='[!_]*.py')
    unittest.TextTestRunner(verbosity=2).run(suite)

import unittest

if __name__ == "__main__":
    suite = unittest.TestLoader().discover("test", pattern="*.py")
    unittest.TextTestRunner(verbosity=2).run(suite)

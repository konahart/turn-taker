import unittest
from unittest.mock import MagicMock
from bot import Bot

class TestBot(unittest.TestCase):
    def setUp(self):
        pass

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBot)
    unittest.TextTestRunner(verbosity=2).run(suite)

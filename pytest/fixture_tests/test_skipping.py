import unittest

class TestClassWithSkippedTest(unittest.TestCase):

    @unittest.skip("demonstrating skipping")
    def test_that_is_skipped(self):
        pass

    def test_that_is_not_skipped(self):
        pass

@unittest.skip("showing class skipping")
class TestClassThatIsSkipped(unittest.TestCase):

    def test_something(self):
        pass

    def test_something_else(self):
        pass

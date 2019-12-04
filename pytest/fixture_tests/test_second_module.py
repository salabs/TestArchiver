import unittest

def function_under_tests():
    foo()

class FirstTestClass(unittest.TestCase):

    def test_something(self):
        pass

    def test_other_thing(self):
        pass


class TestClassWithFailingTests(unittest.TestCase):

    def test_failing_assert(self):
        assert False, "foo"

    def test_opening_missing_file(self):
        open('non-existing-file', 'r')

    def test_function_not_found(self):
        function_under_tests()

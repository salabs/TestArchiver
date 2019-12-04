import unittest

class TestClassWithFailingClassSetUp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert False

    def test_something(self):
        pass

    def test_something_else(self):
        pass

class TestClassWithFailingClassTearDownAndPassingTests(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        assert False

    def test_something(self):
        pass

    def test_something_else(self):
        pass

class TestClassWithFailingClassTearDownAndFailingTests(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        assert False

    def test_something(self):
        assert False

    def test_something_else(self):
        assert False








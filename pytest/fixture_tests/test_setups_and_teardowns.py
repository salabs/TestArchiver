import unittest

class TestClassWithFailingTestSetUp(unittest.TestCase):

    def setUp(self):
        assert False

    def test_something(self):
        pass

class TestClassWithFailingTestTearDownAndPassingTests(unittest.TestCase):

    def test_something(self):
        pass

    def test_something_else(self):
        pass

    def tearDown(self):
        assert False

class TestClassWithFailingTestTearDownAndFailingTests(unittest.TestCase):

    def test_something(self):
        assert False

    def test_something_else(self):
        assert False

    def tearDown(self):
        assert False

    @classmethod
    def tearDownClass(cls):
        assert False


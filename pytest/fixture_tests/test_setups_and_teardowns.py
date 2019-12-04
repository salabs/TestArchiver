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
        print('foo1')
        self.foo = 1
        assert False

    def test_something_else(self):
        print('foo2')
        self.foo = 2
        assert False

    def tearDown(self):
        print('foo3')
        assert False
        if self.foo == 1:
            assert False
        else:
            pass

    @classmethod
    def tearDownClass(cls):
        print('foo4')
        assert False




#@unittest.skip("demonstrating skipping")

#@unittest.skipIf(mylib.__version__ < (1, 3), "not supported in this library version")

#@unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")

# @unittest.skip("showing class skipping")
# class MySkippedTestCase(unittest.TestCase):

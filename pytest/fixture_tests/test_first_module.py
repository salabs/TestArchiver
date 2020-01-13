import unittest

import pytest

@pytest.fixture(scope="session", autouse=True)
def log_global_env_facts(record_testsuite_property):
    record_testsuite_property("EXAMPLE_METADATA", "foo")
    record_testsuite_property("SW_VERSION", "X.Y.Z")

class FirstTestClass(unittest.TestCase):

    def test_something(self):
        record_property("example_key", 1)

        pass

    def test_other_thing(self):
        pass

import pytest
from mock import Mock

from test_archiver.archiver_listeners import ChangeEngineListener


@pytest.fixture
def listener():
    mock_archiver = Mock()
    mock_archiver.test_type = "something"
    mock_archiver.repository = "somewhere"
    mock_archiver.execution_context = "PR"
    engine = ChangeEngineListener(mock_archiver, "tidii")
    return engine


def test_change_engine_listener_test_filter_skipped(listener):
    test1 = Mock()
    test1.full_name = "pytest.test_suite.test_a1"
    test1.status = "PASS"
    test2 = Mock()
    test2.full_name = "pytest.test_suite.test_a2"
    test2.status = "SKIPPED"
    tests = listener._filter_tests([test1, test2])
    assert len(tests) == 1, "Skipped test should be filtered out."
    test = tests[0]
    assert test["name"] == "pytest.test_suite.test_a1"


def test_change_engine_listener_test_filter_pass_and_fail(listener):
    test1 = Mock()
    test1.full_name = "pytest.test_suite.test_a1"
    test1.status = "PASS"
    test2 = Mock()
    test2.full_name = "pytest.test_suite.test_a2"
    test2.status = "FAIL"
    tests = listener._filter_tests([test1, test2])
    assert len(tests) == 2, "Skipped test should be filtered out."
    test = tests[0]
    assert test["name"] == "pytest.test_suite.test_a1"
    test = tests[1]
    assert test["name"] == "pytest.test_suite.test_a2"


def test_change_engine_listener_execution_context(listener):
    test1 = Mock()
    test1.full_name = "pytest.test_suite.test_a1"
    test1.status = "PASS"
    body = listener._format_body([test1], "path/tp/changes")
    context = body["context"]
    assert len(body) == 3, "tests, changes and context must be present"
    assert body["changes"]
    assert body["tests"]
    assert context == "PR"

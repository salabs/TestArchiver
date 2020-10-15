import pytest
from mock import Mock

from test_archiver import configs, archiver
from test_archiver.output_parser import (
    XUnitOutputParser,
    JUnitOutputParser,
    MochaJUnitOutputParser,
    PytestJUnitOutputParser,
    MSTestOutputParser
)


@pytest.fixture(scope="module")
def mock_archiver():
    mock_db = Mock()
    config = configs.Config(file_config={})
    return archiver.Archiver(mock_db, config)

@pytest.fixture
def xunit(mock_archiver):
    return XUnitOutputParser(mock_archiver)


@pytest.fixture
def junit(mock_archiver):
    return JUnitOutputParser(mock_archiver)


@pytest.fixture
def mocha_junit(mock_archiver):
    return MochaJUnitOutputParser(mock_archiver)


@pytest.fixture
def pytest_junit(mock_archiver):
    return PytestJUnitOutputParser(mock_archiver)


@pytest.fixture
def mstest(mock_archiver):
    return MSTestOutputParser(mock_archiver)


def test_xunit_has_test_type(xunit):
    assert xunit.archiver.test_type == "xunit"


def test_junit_has_test_type(junit):
    assert junit.archiver.test_type == "junit"


def test_mocha_junit_has_test_type(mocha_junit):
    assert mocha_junit.archiver.test_type == "mocha-junit"


def test_pytest_junit_has_test_type(pytest_junit):
    assert pytest_junit.archiver.test_type == "pytest-junit"


def test_mstest_has_test_type(mstest):
    assert mstest.archiver.test_type == "mstest"

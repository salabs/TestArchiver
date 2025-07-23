
from pathlib import Path

import pytest

PYTEST_FIXTURE_ROOT = Path(__file__).parent

# This runner is needed to ignore the status code from the test run in other scrips

pytest.main([
    PYTEST_FIXTURE_ROOT / "fixture_tests",
    "--tb=no",
    "--junit-xml", PYTEST_FIXTURE_ROOT / "pytest_fixture_output.xml",
])

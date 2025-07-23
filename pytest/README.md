# pytets-JUnit fixture tests

These are fixture tests designed to produce test inputs for the pytest-junit parser using pytest testing library and mocha-junit-reporter module.

The examples here can also be used as example for using TestArchiver with [pytest](https://docs.pytest.org/)

[producing junit xml files](https://docs.pytest.org/en/6.2.x/usage.html#creating-junitxml-format-files)

[How to insert metadata](https://docs.pytest.org/en/6.2.x/usage.html#record-testsuite-property)

## Runing fixture tests and producing xml report
Pytest is included in the dev dependencies of the project and helpers for running and parsing the pytest fixture.

To just generate the fixture xml:
```
pdm pytest_fixture_run
```

To both generate and parse fixture xml:
```
pdm pytest_fixture_populate
```

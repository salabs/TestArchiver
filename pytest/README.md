# pytets-JUnit fixture tests
These are fixture tests designed to produce test inputs for the pytest-junit parser using Mocha testing library and mocha-junit-reporter module.

The examples here can also be used as example for using TestArchiver with pytest

## Required pip modules
[pytest](https://docs.pytest.org/en/5.3.2/contents.html)
```
pip install pytest
```

[producing junit xml files](https://docs.pytest.org/en/5.3.2/usage.html#creating-junitxml-format-files)

[How to insert metadata](https://docs.pytest.org/en/5.3.2/usage.html#record-testsuite-property)


## Runing tests and producing xml report
```
pytest fixture_tests/ --junit-xml=output.xml
```

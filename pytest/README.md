# pytets-JUnit fixture tests
These are fixture tests designed to produce test inputs for the pytest-junit parser using Mocha testing library and mocha-junit-reporter module.

The examples here can also be used as example for using TestArchiver with pytest

## Required pip modules
[pytest](https://docs.pytest.org/en/3.0.2/contents.html)
[producing junit xml files](https://docs.pytest.org/en/3.0.2/usage.html#creating-junitxml-format-files)
```
pip install pytest
```

## Runing tests and producing xml report
```
pytest fixture_tests/ --junit-xml=output.xml
```

# Mocha-JUnit fixture tests
These are fixture tests designed to produce test inputs for the mocha-junit parser using Mocha testing library and mocha-junit-reporter module.

The examples here can also be used as exmple for using TestArchiver with Mocha tests

## Required npm modules
[mocha-junit-reporter](https://www.npmjs.com/package/mocha-junit-reporter)
```
npm install mocha
npm install mocha-junit-reporter
```

## Runing tests and producing xml report
These reporter options are required for optimal results when using the TestArchiver
```
mocha fixture_suite.js \
    --reporter mocha-junit-reporter \
    --reporter-options outputs=true \
    --reporter-options useFullSuiteTitle=True \
    --reporter-options suiteTitleSeparedBy="." \
    --reporter-options testCaseSwitchClassnameAndName=True
```

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

## Example configuration with Cypress

Mocha-JUnit format can be used with [Cypress](https://github.com/cypress-io/cypress) testing framework.

Add `mocha-junit-reporter` and `cypress-multi-reporters` to package.json devDependencies list. Example package.json config:

```
"devDependencies": {
    ...
    "mocha": "6.2.0",
    "cypress-multi-reporters": "1.2.1",
    "mocha-junit-reporter": "1.23.1"
}
```

After npm package installation, configure cypress reporter options. These settings have been verified to work with TestArchiver in production use:

```
"reporter": "cypress-multi-reporters",
"reporterOptions": {
    "reporterEnabled": "spec, mocha-junit-reporter",
    "mochaJunitReporterReporterOptions": {
        "mochaFile": "resultfolder/result-[hash].xml",
        "rootSuiteTitle": "Root Suite Name",
        "outputs": true,
        "testCaseSwitchClassnameAndName": true,
        "useFullSuiteTitle": true,
        "includePending": true,
        "suiteTitleSeparedBy": "."
    }
},
```

After cypress has completed with these settings, test result xml files should be stored in `resultfolder` directory. They can be imported using TestArchiver from there by using `--format mocha-junit` command line parameter.

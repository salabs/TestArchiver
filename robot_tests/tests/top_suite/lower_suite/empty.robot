*** Settings***
Test Tags          should-fail
Test Teardown       Run Keywords       Do Logging       AND     Do Tagging        AND    ${EMPTY}

# This suite contains problems and are demonstrating failing during teardown even test works.

*** Test Cases ***

Test With Same Name
    Log             First Run

Test With Same Name
    Log             Second Run

*** Keywords ***
Do Logging
    Log             Test teardown       DEBUG
Do Tagging
    Set Tags        teardown
*** Settings***
Force Tags          should-fail
Test Teardown       Run Keywords       Do Logging       AND     Do Tagging        AND    ${EMPTY}

# This suite contains problems and are demonstrating failing during teardown even test works.

*** Test Cases ***

Test 1
    Log             First Run
Test 1
    Log             Second Run

Test 1
    Log             Third Run

*** Keywords ***
Do Logging
    Log             Test teardown       DEBUG
Do Tagging
    Set Tags        teardown
*** Settings ***
Resource    ../../resources/common_keywords.robot
Test Tags  failing

*** Test cases ***
You can do it! Go for it!
    Fail the test case

Bungle the set up, do something (or actually not) and then tear things down
    [Setup]     Fail the test case
    [Teardown]  Do nothing twice
    Do nothing twice
    Do nothing twice

Bungle the set up, do something (or actually not) and then bungle the tear down
    [Setup]     Fail the test case
    [Teardown]  Fail the test case
    Do nothing twice
    Do nothing twice

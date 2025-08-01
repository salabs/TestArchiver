*** Settings ***
Resource    ../../resources/common_keywords.robot
Test Tags  skipping  rf4

*** Test cases ***
This test is skipped after doing something
    Do nothing twice
    Skip  This is skipped

This test is skipped in setup
    [Setup]  Skip  This is skipped
    Do nothing twice

This test is skipped in teardown
    Do nothing twice
    [Teardown]  Skip  This is skipped

This test is always skipped
    [Tags]    robot:skip
    Do nothing twice
    [Teardown]  Skip  This is skipped

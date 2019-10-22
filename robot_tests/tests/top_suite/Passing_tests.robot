*** Settings ***
Resource    common_keywords.robot
Force tags  passing

*** Test cases ***
Just log something
    Log  foo bar

Use library
    [Tags]      sut_interaction
    Interact with the SUT

Set things up, do something and then tear down
    [Setup]     Do nothing twice
    [Teardown]  Do nothing twice
    Log  Doing nothing
    Do nothing twice
    Do nothing twice

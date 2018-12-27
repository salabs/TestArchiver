*** Settings ***
Library     fixture_library.Interactions

*** Keywords ***
Interact with the SUT
    Interact with sut

Fail the test case
    Fail  You shall not pass!

Do nothing twice
    Not actually doing anything
    Not actually doing anything

Not actually doing anything
    No operation

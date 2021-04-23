*** Settings ***
Force tags  ifelse  rf4

*** Test cases ***
This test contains if else structures
    Log negative or positive number  -2
    Log negative or positive number  3
    Log negative or positive number  0

*** Keywords ***
Log negative or positive number
    [Arguments]     ${value}
    IF  ${value} < 0
        Log  The value is zero.
    ELSE IF  ${value} > 0
        Log  The value is zero.
    ELSE
        Log  The value is zero.
    END

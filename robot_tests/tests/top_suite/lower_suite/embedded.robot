*** Settings ***
Test Tags                    embedded               loops

*** Test Cases ***
Normal test case with embedded arguments
    The result of 1 + 5 should be 6
    The result of 1 + 6 should be 7

Template with embedded arguments
    [Template]                The result of ${calculation} should be ${expected}
    1 + 1                     2
    1 + 2                     3

Template and for loops
    [Template]                Another template
    FOR                      ${item}                IN                     @{ITEMS}
                             ${item}                Robot
    END

*** Keywords ***
The result of ${calculation} should be ${expected}
    ${result} =               Evaluate               ${calculation}
    Log                       ${result}
    Should Be Equal As Integers                      ${result}              ${expected}

Another template
    [arguments]               ${first_arg}           ${second_arg}
    Log                       ${first_arg}, ${second_arg}                    WARN

*** Variables ***
@{ITEMS} =                    r    o    b     o    t

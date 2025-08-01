
*** Settings ***
Resource     ../../resources/common_keywords.robot


*** Test Cases ***
Try Except Catching
    Try And Catch Not Numbers    1
    Try And Catch Not Numbers    foo

*** Keywords ***
Try And Catch Not Numbers
    [Arguments]    ${value}
    TRY
        Keyword Expecting Numbers    ${value}
    EXCEPT    ValueError: *    type=GLOB
        Log    Exeption cauth, not a number
    ELSE
        Log    No problem with the value
    FINALLY
        Log    Always executed.
    END

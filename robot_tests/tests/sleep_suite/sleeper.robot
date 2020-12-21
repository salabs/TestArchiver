*** Settings ***
Test Template    sleep-driven
Force tags       data-driven    sleep

*** Test Cases ***              Sleep time
First sleep                     1
Second sleep                    6
Third sleep                     1
Fourth sleep                    7

*** Keywords ***
sleep-driven
    [Arguments]                 ${time}
    Sleep                       ${time}
    Run Keyword if              ${time} > 5             Log         That's lazy!    WARN
    Run Keyword if              ${time} > 5             Set tags    Lazy
    Log                         Time to wake up!


*** Settings ***
Library           String
Test Template     Upper case should be

*** Test Cases ***
Grouped Template
    GROUP    ASCII characters
        a    A
        z    Z
    END
    GROUP    Latin-1 characters
        ä    Ä
        ß    SS
    END
    GROUP    Numbers
        1    1
        9    9
    END

*** Keywords ***
Upper case should be
    [Arguments]    ${char}    ${expected}
    ${actual} =    Convert To Upper Case    ${char}
    Should Be Equal    ${actual}    ${expected}

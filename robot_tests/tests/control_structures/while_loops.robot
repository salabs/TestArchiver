
*** Settings ***
Resource         ../../resources/common_keywords.robot

*** Test Cases ***
Limit as iteration count
    [Tags]    random    should_fail
    WHILE    True    limit=0.5s    on_limit_message=Custom While loop error message
        Sleep    0.3s    This is run 0.5 seconds.
    END

CONTINUE and BREAK with WHILE
    WHILE    True
        TRY
             ${value} =    Not actually doing anything
        EXCEPT
            CONTINUE
        END
        Do something with value    ${value}
        BREAK
    END

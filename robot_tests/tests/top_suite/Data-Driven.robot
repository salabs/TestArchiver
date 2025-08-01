*** Settings ***
Test Template    Data driven Template
Test Tags        data-driven

*** Test Cases ***              First value                 Second value
First passes                    1                           1
Second passes                   1                           1
Third passes and warns          1                           2
Fourth fails                    2                           1



*** Keywords ***
Data driven Template
    [Arguments]                 ${fval}                     ${sval}
    Run Keyword If              ${fval}==${sval}            Log                    Passed                            
    ...                         ELSE IF                     ${fval}<${sval}        Log         Warning             WARN    
    ...                         ELSE IF                     ${fval}>${sval}        Fail        Test failed      


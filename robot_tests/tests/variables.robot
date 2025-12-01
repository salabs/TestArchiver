*** Settings ***
Test Tags  variables


*** Variables ***
${ORIGINAL_VARIABLE}=    original value


*** Test cases ***
Set variables
    [Tags]    listener_parser_mismatch
    VAR    ${local_variable}=    ${ORIGINAL_VARIABLE}    scope=LOCAL
    VAR    ${test_variable}=     ${ORIGINAL_VARIABLE}    scope=TEST
    VAR    ${suite_variable}=    ${ORIGINAL_VARIABLE}    scope=SUITE
    Log    ${local_variable} ${test_variable} ${suite_variable}

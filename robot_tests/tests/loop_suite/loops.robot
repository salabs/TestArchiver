*** Settings ***
Library           String
Force tags        loops

*** Test Cases ***

WARN In Range and create strings
    
    : FOR       ${INDEX}                IN RANGE    10     15
    \           Log                     ${INDEX}
    \           ${RANDOM_STRING}=       Generate Random String      ${INDEX}
    \           Log                     ${RANDOM_STRING}            WARN


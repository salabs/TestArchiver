*** Settings ***
Library         String
Force tags      loops
Test setup      Log  foo
Test teardown   Log  foo

*** Test Cases ***
For-Loop-In-Range
    : FOR       ${INDEX}            IN RANGE    1    3
    \           Log                 ${INDEX}
    \           ${RANDOM_STRING}=   Generate Random String           ${INDEX}
    \           Log                 ${RANDOM_STRING}

For-Loop-Elements
    @{ITEMS}    Create List         Robot            Framework       Example
    :FOR        ${ELEMENT}          IN               @{ITEMS}
    \           Log                 ${ELEMENT}
    \           ${ELEMENT}          Replace String   ${ELEMENT}      ${SPACE}        ${EMPTY}
    \           Log                 ${ELEMENT}

For-Loop-Exiting
    @{ITEMS}    Create List         Robot            Framework   Example
    :FOR        ${ELEMENT}          IN               @{ITEMS}
    \           Log                 ${ELEMENT}
    \           Run Keyword If      '${ELEMENT}' == 'Framework'    Exit For Loop
    \           Log                 Found Framework

Repeat-Action
    Repeat Keyword                  2    Log    Repeating this ...
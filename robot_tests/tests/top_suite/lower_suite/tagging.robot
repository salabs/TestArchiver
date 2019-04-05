*** Settings ***
Force Tags      R2-D2
Default Tags    Robot    C-3PO

*** Variables ***
${HOST}         human

*** Test Cases ***
No own tags
    [Documentation]    This test has tags Robot, C-3PO and R2-D2.
    No Operation

With own tags
    [Documentation]    This test has tags not_ready, Robot-v2 and R2-D2.
    [Tags]    Robot-v2    not_ready
    No Operation

Own tags with variables
    [Documentation]    This test has tags hooman-human and R2-D2.
    [Tags]    hooman-${HOST}
    No Operation

Empty own tags
    [Documentation]    This test has only tag R2-D2.
    [Tags]
    No Operation

Set Tags and Remove Tags Keywords
    [Documentation]    This test has tags mytag and C-3PO.
    Set Tags       mytag
    Remove Tags    Robot    R2*
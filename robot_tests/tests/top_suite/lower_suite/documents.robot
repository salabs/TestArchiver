*** Settings ***

Force tags  documenting

*** Test cases ***
Set test documentation
    Set Test Documentation          Test's own documentation
    Log                             ${TEST DOCUMENTATION}

Set suite documentation
    Set Suite Documentation         Suite's own documentation.
    Log                             ${SUITE DOCUMENTATION}

Add text to suite documentation
    Set Suite Documentation         This is the additional text     append=yes
    Log                             ${SUITE DOCUMENTATION}

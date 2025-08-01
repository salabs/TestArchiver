
*** Variables ***
${VAL}=                     true


*** Test Cases ***
Passing test
    Log                     This test shall pass

Choose fail
    Should be true          '${VAL}' == 'true'

Choose fail with WARN
    Log                     Warning                             WARN 
    Should be true          '${VAL}' == 'true'

Counterwise fail
    Set Tags                should-fail
    Log                     Sorry, but cant do anything         WARN 
    Should be true          '${VAL}' == 'false'

Always fails
    Set Tags                should-fail
    Fail                    Test will fail      
Always fails with tag
    Set Tags                should-fail
    Fail                    Test will fail      should-fail

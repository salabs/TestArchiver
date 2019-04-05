*** Test Cases ***

Randomized fail 
    ${random}=          Evaluate                random.randint(1, 100)          random
    Should Be True      ${random} < ${ADJUST}

Low failrate
    ${random}=          Evaluate                random.randint(1, 100)          random
    Should Be True      ${random} < 90

Medium failrate
    ${random}=          Evaluate                random.randint(1, 100)          random
    Should Be True      ${random} < 50

High Failrate
    ${random}=          Evaluate                random.randint(1, 100)          random
    Should Be True      ${random} < 10


*** Variables ***
${ADJUST}=              50
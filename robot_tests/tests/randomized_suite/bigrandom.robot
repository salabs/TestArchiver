*** Settings ***
Test Template                       random-driven
Test Tags                          data-driven        randomized


*** Test Cases ***                  Line value         Max value          
First random                        20                   50        
Second random                       30                   50        
Third random                        25                   50        
Fourth random                       15                   50        
Fifth random                        13                   100
Sixth random                        60                   100    
Sevenh random                       30                   100
Eigth random                        500                  1000
Ninth random                        100                  1200
Tenth random                        120                  300
   

*** Keywords ***
random-driven 
    [Arguments]                     ${lval}              ${maxval}
    ${random}=                      Evaluate             random.randint(1, ${maxval})     random
    Should Be True                  ${random} > ${lval} 

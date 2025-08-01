*** Settings ***
Test Tags              behavior-driven         sleep

*** Test Cases ***
Behavior sleeping
    Given I would like to sleep "3" "seconds" more
    When I woke up I would like to get warning
    and add a "woke-up" tag for Test
    Then I should feel rested
    

*** Keywords ***
I would like to sleep "${value}" "${variable}" more
    Log                 Sleeping
    Sleep               ${value}
I woke up I would like to get warning
    Log                 Wake up!                WARN

add a "${tag}" tag for Test
    Set tags            ${tag}
    Log                 Tag assigned!           WARN
I should feel rested
    Log                 Feeling well!           WARN
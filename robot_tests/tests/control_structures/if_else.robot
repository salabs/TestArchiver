
*** Test Cases ***
If And Else
    Analyse Value    ${1}
    Analyse Value    ${-1}
    Analyse Value    ${0}
    Analyse Value    foo

Nested If And Else
    Log items
    Log items    xxx    log_values=False
    Log items    a    b    c


*** Keywords ***
Analyse Value
    [Arguments]    ${value}
    IF    $value > 0
        Log    Positive value
    ELSE IF    $value < 0
        Log    Negative value
    ELSE IF    $value == 0
        Log    Zero value
    ELSE
        Fail    Unexpected value: ${value}
    END

Log items
    [Arguments]    @{items}    ${log_values}=True
    IF    not ${items}
        Log    No items.
    ELSE IF    len(${items}) == 1
        IF    ${log_values}
            Log    One item: ${items}[0]
        ELSE
            Log    One item.
        END
    ELSE
        Log    ${{len(${items})}} items.
        IF    ${log_values}
            FOR    ${index}    ${item}    IN ENUMERATE    @{items}    start=1
                Log    Item ${index}: ${item}
            END
        END
    END


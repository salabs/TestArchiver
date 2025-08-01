
*** Variables ***
@{ROW1}         yksi    kaksi    kolme
@{ROW2}         one    two    three
@{TABLE}       ${ROW1}    ${ROW2}

@{CHARACTERS}     a    b    c    d    f
@{NUMBERS}        1    2    3

*** Test Cases ***
Simple For Loop
    FOR    ${animal}    IN    cat    dog
        No Operation
        Log    ${animal}
        Log    2nd keyword
    END
    Log    Outside loop

Nested For Loop
    FOR    ${row}    IN    @{table}
        FOR    ${cell}    IN    @{row}
            Log    ${cell}
        END
    END

Multiple Loop Variables
    FOR    ${index}    ${english}    ${finnish}    IN
    ...    1           cat           kissa
    ...    2           dog           koira
    ...    3           horse         hevonen
        Log    ${english},${finnish},${index}
    END

FOR-IN-ENUMERATE With Start
    FOR    ${index}    ${item}    IN ENUMERATE    @{ROW1}    start=1
        Log    ${index}, ${item}
    END

Variable conversion
    # TODO: output.xml will omit the third value and leaves listener and parsing inconsistent
    # FOR    ${value: bytes}    IN    Hello!    Hyvä!    \x00\x00\x07
    #     Log    ${value}    formatter=repr
    # END
    FOR    ${index}    ${date: date}    IN ENUMERATE   2023-06-15    2025-05-30    today
        Log    ${date}     formatter=repr
    END
    FOR    ${item: tuple[str, date]}    IN ENUMERATE   2023-06-15    2025-05-30    today
        Log    ${item}     formatter=repr
    END

BREAK with FOR
    ${text} =    Set Variable    zero
    FOR    ${var}    IN    one    two    three
        IF    '${var}' == 'two'    BREAK
        ${text} =    Set Variable    ${text}-${var}
    END
    Should Be Equal    ${text}    zero-one

CONTINUE with FOR
    ${text} =    Set Variable    zero
    FOR    ${var}    IN    one    two    three
        IF    '${var}' == 'two'    CONTINUE
        ${text} =    Set Variable    ${text}-${var}
    END
    Should Be Equal    ${text}    zero-one-three

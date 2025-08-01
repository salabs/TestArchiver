

*** Test Cases ***
Using Repeat Keyword
    Repeat Keyword    5    Log    Repeat it!

Basic Group Syntax
    GROUP    First group
        Log    Logged in first group
    END
    Log    Logged in in between
    GROUP    Second group
        Log    Logged in second group
    END

Anonymous Group
    GROUP
        Log    Group name is optional.
    END

Nested Groups
    GROUP
        GROUP    Nested group
            Log    Groups can be nested.
        END
    END

*** Settings ***
Resource        common_keywords.robot
Force tags      logging

*** Test cases ***
Log a trace message
    Log         There is some trace  DEBUG

Log a debug message
    Log         Good luck debugging this  DEBUG

Log a info message
    Log         Here is some info for you: foo  INFO
    Log         Here is some info for you: foo  TRACE
    Log         Here is some info for you: foo  INFO

Log a warning message
    Log         This is the last warning!  WARN

Log a error message
    [Tags]      error
    Log         A grave error has been made... but on purpose.  ERROR

Log a fail message
    [Tags]      failing     should-fail
    Fail        This test has been utterly failed

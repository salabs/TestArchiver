*** Settings ***
Documentation       Suite where everything passes
Resource            common_keywords.robot

*** Test Cases ***
First passing testcase
    Log     This test case passes but will be failed

Second passing testcase
    Log     This test case passes but will be failed

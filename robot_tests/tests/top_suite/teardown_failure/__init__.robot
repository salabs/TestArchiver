*** Settings ***
Documentation       Suite where everything passes but the suite teardown fails
Resource            common_keywords.robot
Force tags          failed_by_suite_teardown
Suite Teardown      Fail the test case

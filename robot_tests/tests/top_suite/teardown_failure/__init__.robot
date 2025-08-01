*** Settings ***
Documentation       Suite where everything passes but the suite teardown fails
Resource    ../../../resources/common_keywords.robot
Test Tags    failed_by_suite_teardown
Suite Teardown      Fail the test case

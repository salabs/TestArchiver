*** Settings ***
Library         REST    http://localhost:${PORT}

*** Variables ***
${PORT}=  8888
${TARGET_SERIES}=  2  # Should be the 'Fixture' series

*** Test cases ***

Teams data
    GET             /data/teams/
    Array               $.teams     minItems=1
    String              $.teams[*].name
    Valid series data   $.teams[*]

Test series data
    GET             /data/series/
    Valid series data   $

Builds data
    [Template]    Validate json from path with
    Valid build object  $.builds[*]     /data/series/${TARGET_SERIES}/builds/
    Valid build object  $.builds[*]     /data/series/${TARGET_SERIES}/builds/?build=2
    Valid build object  $.builds[*]     /data/series/${TARGET_SERIES}/builds/?last=10
    Valid build object  $.builds[*]     /data/series/${TARGET_SERIES}/builds/?last=10&offset=5

Test run results data
    GET             /data/test_run/2/results/
    Integer         response status     200
    Valid suite result object   $.suites[*]
    Valid build object          $.included_in_builds[*]

Single test run data
    GET             /data/test_run/2/
    Integer         response status     200
    Integer         $.id
    String          $.imported_at
    String          $.archived_using
    String          $.archiver_version
    String          $.generated
    String          $.generator
    String          $.start_time
    Integer         $.elapsed
    Boolean         $.ignored
    Boolean         $.rpa
    Boolean         $.dryrun

Results data
    [Template]    Validate json with
    Valid results data      /data/series/${TARGET_SERIES}/results/
    Valid results data      /data/series/${TARGET_SERIES}/results/?build=1
    Valid results data      /data/series/${TARGET_SERIES}/results/?last=2
    Valid results data      /data/series/${TARGET_SERIES}/results/?last=2&offset=5

Single test result data
    # if sleep tests are included use test case 58 otherwise 53
    GET         /data/test_run/2/test_case/53/
    Integer     response status     200
    Valid suite result object   $.suites[*]  ${True}

Keyword tree data
    [Template]    Validate json from path with
    Valid keyword tree object   $   /data/keyword_tree/92733cdd5e9d76d0a5108bcb9491aee2fe77e11c/
    Valid keyword tree object   $   /data/keyword_tree/34c6b7c644d6d2d0282bf8de915bce9129ab71ef/

Keyword tree stats data
    [Template]    Validate json from path with
    Valid keyword stat object   $   /data/keyword_tree/92733cdd5e9d76d0a5108bcb9491aee2fe77e11c/stats
    Valid keyword stat object   $   /data/keyword_tree/34c6b7c644d6d2d0282bf8de915bce9129ab71ef/stats

Test case pass ratio data
    [Template]    Validate json with
    Valid status ratio data     /data/test_status_statistics/
    Valid status ratio data     /data/test_status_statistics/?series=${TARGET_SERIES}
    Valid status ratio data     /data/test_status_statistics/?series=${TARGET_SERIES}&build=1           1
    Valid status ratio data     /data/test_status_statistics/?series=${TARGET_SERIES}&last=3            3
    Valid status ratio data     /data/test_status_statistics/?series=${TARGET_SERIES}&last=3&offset=2   3

    Valid status ratio data     /data/series/${TARGET_SERIES}/test_status_statistics/
    Valid status ratio data     /data/series/${TARGET_SERIES}/build/1/test_status_statistics/           1
    Valid status ratio data     /data/series/${TARGET_SERIES}/test_status_statistics/?last=3            3
    Valid status ratio data     /data/series/${TARGET_SERIES}/test_status_statistics/?last=3&offset=2   3

Suite pass ratio data
    [Template]    Validate json with
    Valid status ratio data     /data/suite_status_statistics/
    Valid status ratio data     /data/suite_status_statistics/?series=${TARGET_SERIES}
    Valid status ratio data     /data/suite_status_statistics/?series=${TARGET_SERIES}&build=1          1
    Valid status ratio data     /data/suite_status_statistics/?series=${TARGET_SERIES}&last=3           3
    Valid status ratio data     /data/suite_status_statistics/?series=${TARGET_SERIES}&last=3&offset=2  3

    Valid status ratio data     /data/series/${TARGET_SERIES}/suite_status_statistics/
    Valid status ratio data     /data/series/${TARGET_SERIES}/suite_status_statistics/?last=3           3
    Valid status ratio data     /data/series/${TARGET_SERIES}/suite_status_statistics/?last=3&offset=2  3

Recently failing tests return valid data
    GET             /data/series/${TARGET_SERIES}/recently_failing_tests/
    Integer         response status     200
    Array           $.tests
    Object          $.tests[*]
    Integer         $.tests[*].id
    Integer         $.tests[*].suite_id
    String          $.tests[*].name
    String          $.tests[*].full_name
    Integer         $.tests[*].fails
    Number          $.tests[*].failiness

Recently failing suites return valid data
    GET             /data/series/${TARGET_SERIES}/recently_failing_suites/
    Integer         response status     200
    Array           $.suites
    Object          $.suites[*]
    Integer         $.suites[*].id
    String          $.suites[*].name
    String          $.suites[*].full_name
    Integer         $.suites[*].fails
    Number          $.suites[*].failiness

Ignoring and unignoring test runs should work
    GET                 /data/series/${TARGET_SERIES}/builds/
    Array               $.builds[0].test_run_ids  maxItems=1
    ${test_run_ids}=    Integer   $.builds[0].test_run_ids[0]
    ${test_run_id}=     Set Variable  ${test_run_ids}[0]
    GET             /data/test_run/${test_run_id}/
    Boolean         $.ignored   false
    POST            /data/test_run/${test_run_id}/ignore/
    Boolean         $.ignored   true
    GET             /data/test_run/${test_run_id}/
    Boolean         $.ignored   true
    POST            /data/test_run/${test_run_id}/ignore/
    Boolean         $.ignored   false
    GET             /data/test_run/${test_run_id}/
    Boolean         $.ignored   false


*** Keywords ***

Validate json from path with
    [Arguments]     ${validator}  ${field}  ${url}  @{args}
    GET             ${url}
    Integer         response status     200
    Run keyword     ${validator}        ${field}  @{args}

Validate json with
    [Arguments]     ${validator}  ${url}  @{args}
    GET             ${url}
    Integer         response status     200
    Run keyword     ${validator}        @{args}

Valid series data
    [Arguments]     ${path}
    Array           ${path}.series        minItems=1
    Object          ${path}.series[*]
    Integer         ${path}.series[*].id
    String          ${path}.series[*].team
    String          ${path}.series[*].name
    Integer         ${path}.series[*].builds
    Integer         ${path}.series[*].last_build

Valid results data
    Array                       $.builds
    Valid build object          $.builds[*]
    Array                       $.builds[*].suites
    Valid suite result object   $.builds[*].suites[*]

Valid suite result object
    [Arguments]     ${path}  ${detailed}=${False}
    Object          ${path}
    Integer         ${path}.id
    String          ${path}.name
    String          ${path}.full_name
    String          ${path}.repository

    Integer         ${path}.test_run_id
    String          ${path}.status
    String          ${path}.execution_status
    # String          ${path}.setup_status
    # String          ${path}.teardown_status

    String          ${path}.fingerprint
    # String          ${path}.setup_fingerprint
    String          ${path}.execution_fingerprint
    # String          ${path}.teardown_fingerprint

    #Run keyword if  ${detailed}  Valid keyword tree object  ${path}.setup
    #Run keyword if  ${detailed}  Valid keyword tree object  ${path}.teardown

    String          ${path}.start_time
    Integer         ${path}.elapsed
    # Integer         ${path}.elapsed
    # Integer         ${path}.elapsed
    # Integer         ${path}.elapsed

    Array           ${path}.metadata
    Object          ${path}.metadata[*]
    String          ${path}.metadata[*].name
    String          ${path}.metadata[*].value

    #Run keyword if  ${detailed}  Valid log message data  ${path}.log_messages[*]

    Array           ${path}.tests
    Valid test result object    ${path}.tests[*]  ${detailed}

Valid test result object
    [Arguments]     ${path}  ${detailed}=${False}
    Object          ${path}
    Integer         ${path}.id
    String          ${path}.name
    String          ${path}.full_name

    Integer         ${path}.test_run_id
    String          ${path}.status          FAIL  PASS
    Run keyword if  ${detailed}  String  ${path}.execution_status
    Run keyword if  ${detailed}  String  ${path}.setup_status
    Run keyword if  ${detailed}  String  ${path}.teardown_status

    String          ${path}.fingerprint
    Run keyword if  ${detailed}  String  ${path}.setup_fingerprint
    Run keyword if  ${detailed}  String  ${path}.execution_fingerprint
    Run keyword if  ${detailed}  String  ${path}.teardown_fingerprint

    Run keyword if  ${detailed}  Valid keyword tree object  ${path}.setup
    # Run keyword if  ${detailed}  Valid keyword tree object  ${path}.execution
    Run keyword if  ${detailed}  Valid keyword tree object  ${path}.teardown

    String          ${path}.start_time
    Integer         ${path}.elapsed

    Array           ${path}.tags
    String          ${path}.tags[*]

    Run keyword if  ${detailed}  Valid log message data  ${path}.log_messages[*]

Valid log message data
    [Arguments]     ${path}
    Object          ${path}
    String          ${path}.timestamp
    String          ${path}.message
    String          ${path}.log_level

Valid keyword tree object
    [Arguments]     ${path}
    Object          ${path}
    String          ${path}.fingerprint
    String          ${path}.keyword
    String          ${path}.library
    String          ${path}.status
    Array           ${path}.arguments
    Array           ${path}.children

Valid keyword stat object
    [Arguments]     ${path}
    Object          ${path}
    Integer         ${path}.calls
    Integer         ${path}.max_elapsed
    Integer         ${path}.min_elapsed
    Number          ${path}.avg_elapsed
    Integer         ${path}.max_call_depth

Valid status ratio data
    [Arguments]     ${max_builds}=${None}
    Valid status ratio object   $.total
    Run keyword if  ${max_builds} is not ${None}       Array   $.per_build     maxItems=${max_builds}
    Valid status ratio object   $.per_build[*]

Valid status ratio object
    [Arguments]     ${path}
    Object          ${path}
    Integer         ${path}.total
    Integer         ${path}.passed
    Integer         ${path}.failed
    Number          ${path}.pass_ratio
    Number          ${path}.fail_ratio

Valid build object
    [Arguments]     ${path}
    Object          ${path}
    Integer         ${path}.build_number
    String          ${path}.started_at
    Array           ${path}.test_run_ids
    Integer         ${path}.test_run_ids[*]


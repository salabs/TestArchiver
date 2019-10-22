TEST_SERIES = """
SELECT id, name, team,
        count(*) as builds,
        max(build_number) as last_build,
        max(generated) as last_generated,
        max(imported_at) as last_imported,
        max(start_time) as last_started
FROM (
    SELECT test_series.id, name, team, build_number,
            min(generated) as generated,
            min(imported_at) as imported_at,
            min(start_time) as start_time
    FROM test_series
    JOIN test_series_mapping as tsm ON tsm.series=test_series.id
    JOIN test_run ON tsm.test_run_id=test_run.id
    JOIN suite_result ON suite_result.test_run_id=test_run.id
    WHERE NOT ignored
    GROUP BY test_series.id, name, team, build_number
) AS builds
GROUP BY id, name, team
ORDER BY last_generated DESC, last_started DESC, last_imported DESC;
"""

TEST_SERIES_BY_TEAMS = """
SELECT id, name, team,
        count(*) as builds,
        max(build_number) as last_build,
        max(generated) as last_generated,
        max(imported_at) as last_imported,
        max(start_time) as last_started
FROM (
    SELECT test_series.id, name, team, build_number,
            min(generated) as generated,
            min(imported_at) as imported_at,
            min(start_time) as start_time
    FROM test_series
    JOIN test_series_mapping as tsm ON tsm.series=test_series.id
    JOIN test_run ON tsm.test_run_id=test_run.id
    JOIN suite_result ON suite_result.test_run_id=test_run.id
    WHERE NOT ignored
    GROUP BY test_series.id, name, team, build_number
) AS builds
GROUP BY id, name, team
ORDER BY team, last_generated DESC, last_started DESC, last_imported DESC;
"""

SUBTREES = """
SELECT keyword_tree.fingerprint, keyword, library, status, arguments, call_index
FROM keyword_tree
JOIN tree_hierarchy ON tree_hierarchy.subtree=keyword_tree.fingerprint
WHERE tree_hierarchy.fingerprint=%(fingerprint)s
ORDER BY call_index;
"""

METADATA = """
SELECT name, value, suite_id, test_run_id
FROM suite_metadata
JOIN test_run ON test_run.id=suite_metadata.test_run_id
WHERE test_run_id IN ({test_run_ids})
  AND NOT ignored
ORDER BY suite_id, test_run_id;
"""


def build_metadata(series, build_num):
    return METADATA.format(test_run_ids=test_run_ids(series, build_num))


def test_run_metadata(test_run_id):
    return METADATA.format(test_run_ids=int(test_run_id))

def test_run_data(test_run_id):
    return """
SELECT test_run.id, imported_at, archived_using, archiver_version,
       generator, generated, rpa, dryrun, ignored,
       min(start_time) as start_time, max(elapsed) as elapsed
FROM test_run
JOIN suite_result ON suite_result.test_run_id=test_run.id
WHERE test_run.id={}
GROUP BY test_run.id, imported_at, archived_using, generator, generated, rpa, dryrun, ignored
""".format(int(test_run_id))

def builds(series, build_num, last, offset):
    if build_num:
        build_number_filter = "AND build_number={}".format(int(build_num))
        last_limits = ""
    else:
        build_number_filter = ""
        last_limits = "LIMIT {last} OFFSET {offset}".format(last=int(last), offset=int(offset))
    return """
SELECT build_number, array_agg(test_run_id) as test_run_ids,
        min(started_at) as started_at
FROM (
    SELECT build_number, tsm.test_run_id, min(start_time) as started_at
    FROM test_series_mapping as tsm
    JOIN suite_result ON suite_result.test_run_id=tsm.test_run_id
    JOIN test_run ON test_run.id=tsm.test_run_id
    WHERE series={series} AND NOT ignored
        {build_number_filter}
    GROUP BY build_number, tsm.test_run_id
) as test_runs
GROUP BY build_number
ORDER BY build_number DESC
{last_limits}
""".format(series=int(series), build_number_filter=build_number_filter, last_limits=last_limits)


def latest_build_numbers(series, last, offset):
    return """
SELECT build_number
FROM test_series_mapping as tsm
JOIN test_run ON test_run.id=tsm.test_run_id
WHERE series={series}
  AND NOT ignored
ORDER BY build_number DESC
LIMIT {last} OFFSET {offset}
""".format(
        series=int(series),
        last=int(last),
        offset=int(offset),
    )


def test_run_ids(series=None, build_num=None, last=None, offset=None):
    filters = []
    if series:
        filters.append("series={series_id}".format(series_id=int(series)))
        if build_num:
            filters.append("build_number={}".format(int(build_num)))
        elif last:
            filters.append("build_number IN ({})".format(latest_build_numbers(series, last, offset)))

    return """
SELECT test_run_id
FROM test_series_mapping as tsm
JOIN test_run ON test_run.id=tsm.test_run_id
WHERE NOT ignored
{filters}
ORDER BY build_number, test_run_id
""".format(filters='AND ' + ' AND '.join(filters) if filters else '')


RESULTS_QUERY = """
SELECT * FROM (
    SELECT DISTINCT ON (suite.id, test_results.id)
        suite.id as suite_id, suite.name as suite_name, suite.full_name as suite_full_name,
        suite.repository as suite_repository,
        suite_result.test_run_id as suite_test_run_id,
        suite_result.status as suite_status,
        suite_result.setup_status as suite_setup_status,
        suite_result.execution_status as suite_execution_status,
        suite_result.teardown_status as suite_teardown_status,
        suite_result.fingerprint as suite_fingerprint,
        suite_result.setup_fingerprint as suite_setup_fingerprint,
        suite_result.execution_fingerprint as suite_execution_fingerprint,
        suite_result.teardown_fingerprint as suite_teardown_fingerprint,
        suite_result.start_time as suite_start_time,
        suite_result.elapsed as suite_elapsed,
        suite_result.setup_elapsed as suite_setup_elapsed,
        suite_result.execution_elapsed as suite_execution_elapsed,
        suite_result.teardown_elapsed as suite_teardown_elapsed,

        test_results.id as id, test_results.name as name, test_results.full_name as full_name,
        test_results.test_run_id as test_run_id,
        test_results.status as status,
        test_results.setup_status as setup_status,
        test_results.execution_status as execution_status,
        test_results.teardown_status as teardown_status,
        test_results.fingerprint as fingerprint,
        test_results.setup_fingerprint as setup_fingerprint,
        test_results.execution_fingerprint as execution_fingerprint,
        test_results.teardown_fingerprint as teardown_fingerprint,
        test_results.start_time as start_time,
        test_results.elapsed as elapsed,
        test_results.setup_elapsed as setup_elapsed,
        test_results.execution_elapsed as execution_elapsed,
        test_results.teardown_elapsed as teardown_elapsed,
        CASE WHEN tags IS NULL THEN '{array_literal}' ELSE tags END as tags
    FROM suite_result
    JOIN suite ON suite.id=suite_result.suite_id
    JOIN test_run ON test_run.id=suite_result.test_run_id
    LEFT OUTER JOIN (
        SELECT DISTINCT ON (test_case.id) *
        FROM test_result
        JOIN test_case ON test_case.id=test_result.test_id
        WHERE test_run_id IN ({test_run_ids})
        ORDER BY test_case.id, start_time DESC, test_run_id DESC
    ) as test_results ON test_results.suite_id=suite.id
                     AND test_results.test_run_id=suite_result.test_run_id
    LEFT OUTER JOIN (
        SELECT array_agg(tag ORDER BY tag) as tags, test_id, test_run_id
        FROM test_tag
        WHERE test_run_id IN ({test_run_ids})
        GROUP BY test_id, test_run_id
    ) as test_tags ON test_tags.test_id=test_results.test_id
                  AND test_tags.test_run_id=test_results.test_run_id
    WHERE suite_result.test_run_id IN ({test_run_ids})
      AND NOT ignored
    ORDER BY suite_id, test_results.id, suite_start_time DESC, suite_test_run_id DESC
) AS results
ORDER BY suite_full_name, start_time NULLS LAST, full_name
"""


def build_results(series, build_num):
    return RESULTS_QUERY.format(array_literal='{}', test_run_ids=test_run_ids(series, build_num))


def test_run_results(test_run_id):
    return RESULTS_QUERY.format(array_literal='{}', test_run_ids=int(test_run_id))


def single_test_result(test_run_id, test_id):
    return """
SELECT
    suite.id as suite_id, suite.name as suite_name, suite.full_name as suite_full_name,
    suite.repository as suite_repository,
    suite_result.test_run_id as suite_test_run_id,
    suite_result.status as suite_status,
    suite_result.setup_status as suite_setup_status,
    suite_result.execution_status as suite_execution_status,
    suite_result.teardown_status as suite_teardown_status,
    suite_result.fingerprint as suite_fingerprint,
    suite_result.setup_fingerprint as suite_setup_fingerprint,
    suite_result.execution_fingerprint as suite_execution_fingerprint,
    suite_result.teardown_fingerprint as suite_teardown_fingerprint,
    suite_result.start_time as suite_start_time,
    suite_result.elapsed as suite_elapsed,
    suite_result.setup_elapsed as suite_setup_elapsed,
    suite_result.execution_elapsed as suite_execution_elapsed,
    suite_result.teardown_elapsed as suite_teardown_elapsed,

    test_case.id as id, test_case.name as name, test_case.full_name as full_name,
    test_result.test_run_id as test_run_id,
    test_result.status as status,
    test_result.setup_status as setup_status,
    test_result.execution_status as execution_status,
    test_result.teardown_status as teardown_status,
    test_result.fingerprint as fingerprint,
    test_result.setup_fingerprint as setup_fingerprint,
    test_result.execution_fingerprint as execution_fingerprint,
    test_result.teardown_fingerprint as teardown_fingerprint,
    test_result.start_time as start_time,
    test_result.elapsed as elapsed,
    test_result.setup_elapsed as setup_elapsed,
    test_result.execution_elapsed as execution_elapsed,
    test_result.teardown_elapsed as teardown_elapsed,
    CASE WHEN tags IS NULL THEN '{array_literal}' ELSE tags END as tags
FROM test_result
JOIN test_case ON test_case.id=test_result.test_id
JOIN suite ON suite.id=test_case.suite_id
JOIN suite_result ON test_case.suite_id=suite_result.suite_id
                 AND test_result.test_run_id=suite_result.test_run_id
JOIN test_run ON test_run.id=test_result.test_run_id
LEFT OUTER JOIN (
    SELECT array_agg(tag ORDER BY tag) as tags, test_id
    FROM test_tag
    WHERE test_run_id={test_run_id} AND test_id={test_id}
    GROUP BY test_id
) as test_tags ON test_tags.test_id=test_result.test_id
WHERE test_result.test_run_id={test_run_id}
  AND test_result.test_id={test_id}
  AND suite_result.test_run_id={test_run_id}
  AND NOT ignored
""".format(test_run_id=int(test_run_id), test_id=int(test_id), array_literal='{}')

def _parent_suite_full_name(test_id):
    return """
SELECT full_name
FROM suite
WHERE id=(SELECT suite_id FROM test_case WHERE id={test_id})
""".format(test_id=int(test_id))

def parent_suite_results(test_run_id, test_id):
    return """
SELECT
    suite.id as suite_id, suite.name as suite_name, suite.full_name as suite_full_name,
    suite.repository as suite_repository,
    suite_result.test_run_id as suite_test_run_id,
    suite_result.status as suite_status,
    suite_result.setup_status as suite_setup_status,
    suite_result.execution_status as suite_execution_status,
    suite_result.teardown_status as suite_teardown_status,
    suite_result.fingerprint as suite_fingerprint,
    suite_result.setup_fingerprint as suite_setup_fingerprint,
    suite_result.execution_fingerprint as suite_execution_fingerprint,
    suite_result.teardown_fingerprint as suite_teardown_fingerprint,
    suite_result.start_time as suite_start_time,
    suite_result.elapsed as suite_elapsed,
    suite_result.setup_elapsed as suite_setup_elapsed,
    suite_result.execution_elapsed as suite_execution_elapsed,
    suite_result.teardown_elapsed as suite_teardown_elapsed
FROM suite_result
JOIN suite ON suite.id=suite_result.suite_id
WHERE suite_result.test_run_id={test_run_id}
  AND ({parent_suite_full_name}) ~ (full_name || '\..+')
ORDER BY suite_start_time NULLS LAST, suite_full_name""".format(
        test_run_id=int(test_run_id),
        parent_suite_full_name=_parent_suite_full_name(test_id),
    )

def included_in_builds(test_run_id):
    return """
SELECT test_series.id as series, name, team, test_series_mapping.build_number,
       min(start_time) as started_at, test_run_ids
FROM test_series_mapping
JOIN (
    SELECT series, build_number, array_agg(test_run_id ORDER BY test_run_id) as test_run_ids
    FROM test_series_mapping
    GROUP BY series, build_number
) AS other_builds ON test_series_mapping.series=other_builds.series
                 AND test_series_mapping.build_number=other_builds.build_number
JOIN test_series ON test_series_mapping.series=test_series.id
JOIN suite_result ON suite_result.test_run_id=test_series_mapping.test_run_id
WHERE test_series_mapping.test_run_id={}
GROUP BY test_series.id, name, team, test_series_mapping.build_number, test_run_ids
ORDER BY team, name, test_series_mapping.build_number DESC
""".format(int(test_run_id))


def status_ratios(object_type, series, last, offset, build_num, per_build):
    filters = []
    if series:
        filters.append(" tsm.series={} ".format(int(series)))
        filters.append(
            " tsm.test_run_id IN ({test_run_ids})".format(
                test_run_ids=test_run_ids(series, build_num, last, offset),
                )
        )
    target_table = ''
    if object_type == 'test':
        target_table = "FROM test_result as result"
    elif object_type == 'suite':
        target_table = ("FROM suite_result as result JOIN suite ON suite.id=result.suite_id "
                        "AND suite.id IN (SELECT suite_id FROM test_case)")
    return """
SELECT max(build_number) as build, series,
    count(*) as total,
    count(nullif(status<>'PASS', true)) as passed,
    count(nullif(status<>'FAIL', true)) as failed,
    CASE WHEN count(*)>0 THEN count(nullif(status<>'PASS', true))::float/count(*) ELSE 0 END as pass_ratio,
    CASE WHEN count(*)>0 THEN count(nullif(status<>'FAIL', true))::float/count(*) ELSE 0 END as fail_ratio
{target_table}
JOIN test_series_mapping as tsm ON result.test_run_id=tsm.test_run_id
JOIN test_run ON test_run.id=tsm.test_run_id
WHERE NOT ignored {filters}
{grouping}
{ordering}
""".format(
        target_table=target_table,
        filters="AND " + ' AND '.join(filters) if filters else '',
        grouping="GROUP BY series, build_number" if per_build else "GROUP BY series",
        ordering="ORDER BY series, build_number DESC" if per_build else "ORDER BY series",
    )


def recently_failing_tests(top, series_id, build_num, last, offset):
    return """
SELECT id, name, full_name, suite_id,
    count(nullif(status, 'PASS')) as fails,
    sum(failiness) as failiness
FROM (
    SELECT
        test_case.id, test_case.name, test_case.full_name, test_case.suite_id,
        result.status,
        CASE WHEN result.status = 'FAIL'
            THEN 1.0/sqrt(ROW_NUMBER() OVER (PARTITION BY test_case.id ORDER BY tsm.build_number DESC))
            ELSE 0
        END as failiness
    FROM test_result as result
    JOIN test_series_mapping as tsm ON tsm.test_run_id=result.test_run_id
    JOIN test_case ON test_case.id=result.test_id
    WHERE tsm.series={series_id}
        AND result.test_run_id IN ({test_run_ids})
) AS failinesses
GROUP BY id, name, full_name, suite_id
ORDER BY failiness DESC LIMIT {top};
""".format(
        test_run_ids=test_run_ids(series_id, build_num, last, offset),
        series_id=int(series_id),
        top=int(top),
    )


def recently_failing_suites(top, series_id, build_num, last, offset):
    return """
SELECT id, name, full_name,
    count(nullif(status, 'PASS')) as fails,
    sum(failiness) as failiness
FROM (
    SELECT
        suite.id, suite.name, suite.full_name,
        result.status,
        CASE WHEN result.status = 'FAIL'
            THEN 1.0/sqrt(ROW_NUMBER() OVER (PARTITION BY suite.id ORDER BY tsm.build_number DESC))
            ELSE 0
        END as failiness
    FROM suite_result as result
    JOIN test_series_mapping as tsm ON tsm.test_run_id=result.test_run_id
    JOIN suite ON suite.id=result.suite_id
    WHERE tsm.series={series_id}
        AND result.test_run_id IN ({test_run_ids})
        AND suite.id IN (SELECT suite_id FROM test_case)
) AS failinesses
GROUP BY id, name, full_name
ORDER BY failiness DESC LIMIT {top};
""".format(
        test_run_ids=test_run_ids(series_id, build_num, last, offset),
        series_id=int(series_id),
        top=int(top),
    )


def tree_execution_measures(fingerprint, series_id, build_num, last, offset):
    return """
SELECT sum(calls) as calls,
       max(max_execution_time) as max_elapsed,
       min(min_execution_time) as min_elapsed,
       sum(cumulative_execution_time)::float/sum(calls) as avg_elapsed,
       max(max_call_depth) as max_call_depth
FROM keyword_statistics as stats
JOIN keyword_tree as kw ON kw.fingerprint=stats.fingerprint
WHERE test_run_id IN ({test_run_ids}) AND stats.fingerprint='{fingerprint}'
GROUP BY keyword
ORDER BY calls desc;
""".format(
        test_run_ids=test_run_ids(series_id, build_num, last, offset),
        fingerprint=fingerprint,
    )

def log_messages(test_run_id):
    return """
SELECT test_run_id, test_id, suite_id,
       timestamp, log_level, message
FROM log_message
WHERE test_run_id={test_run_id}
ORDER BY timestamp, id
""".format(test_run_id=int(test_run_id))

if __name__ == '__main__':
    print(status_ratios('test', 8, 40, 10, 0, True))

def builds_by_time(series, build_num, last, offset, searchTimeStart, searchTimeEnd):
    if build_num:
        build_number_filter = "AND build_number={}".format(int(build_num))
        last_limits = ""
    else:
        build_number_filter = ""
        last_limits = "LIMIT {last} OFFSET {offset}".format(last=int(last), offset=int(offset))
    return """
SELECT build_number, array_agg(test_run_id) as test_run_ids,
        min(started_at) as started_at
FROM (
    SELECT build_number, tsm.test_run_id, min(start_time) as started_at
    FROM test_series_mapping as tsm
    JOIN suite_result ON suite_result.test_run_id=tsm.test_run_id
    JOIN test_run ON test_run.id=tsm.test_run_id
    WHERE series={series} AND suite_result.start_time BETWEEN '{searchTimeStart}' AND '{searchTimeEnd}' AND NOT ignored
        {build_number_filter}
    GROUP BY build_number, tsm.test_run_id
) as test_runs
GROUP BY build_number
ORDER BY build_number DESC
{last_limits}
""".format(series=int(series), build_number_filter=build_number_filter, last_limits=last_limits, searchTimeStart=searchTimeStart, searchTimeEnd=searchTimeEnd)

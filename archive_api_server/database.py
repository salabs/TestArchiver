import datetime
from collections import defaultdict

import urllib.parse
import queries
import sql_queries


class Database:

    def __init__(self, host, dbname, user, password):
        # Escape password as it may contain special characters.
        # Strip whitespace from other parameters.
        # Strip trailing '/' from host.
        connection_uri = 'postgresql://{user}:{pw}@{host}/{dbname}'.format(
            user=user.strip(),
            pw=urllib.parse.quote_plus(password),
            host=host.strip().rstrip('/'),
            dbname=dbname.strip(),
        )
        self.session = queries.TornadoSession(connection_uri)

    def test_series(self):
        return self.session.query(sql_queries.TEST_SERIES), list_of_dicts

    def teams(self):
        def series_by_team(rows):
            all_series = list_of_dicts(rows)
            teams = []
            current_team_name = None
            current_team = None
            for series in all_series:
                if current_team_name != series['team']:
                    if current_team:
                        teams.append(current_team)
                    current_team = {'name': series['team'], 'series_count': 0, 'series': []}
                current_team['series_count'] += 1
                current_team['series'].append(series)
                current_team_name = series['team']
            if current_team:
                teams.append(current_team)
            return teams
        return self.session.query(sql_queries.TEST_SERIES_BY_TEAMS), series_by_team

    def last_update(self):
        sql = "SELECT * FROM test_run ORDER BY id DESC LIMIT 1"
        return self.session.query(sql), single_dict
        
    def db_type(self):
        sql = "SELECT generator, archived_using FROM test_run ORDER BY id DESC LIMIT 1"
        return self.session.query(sql), single_dict

    def builds(self, series, build, last, offset):
        return self.session.query(sql_queries.builds(series, build, last, offset)), list_of_dicts

    def builds_by_time(self, series, build, last, offset, searchTimeStart, searchTimeEnd):
        return self.session.query(sql_queries.builds_by_time(series, build, last, offset, searchTimeStart, searchTimeEnd)), list_of_dicts

    def build_results(self, series, build_num):
        return self.session.query(sql_queries.build_results(series, build_num)), list_of_dicts

    def test_run_results(self, test_run_id):
        return self.session.query(sql_queries.test_run_results(test_run_id)), list_of_dicts

    def test_run_data(self, test_run_id):
        return self.session.query(sql_queries.test_run_data(test_run_id)), single_dict

    def ignore_test_run(self, test_run_id):
        sql = "UPDATE test_run SET ignored=NOT ignored WHERE id={} RETURNING id, ignored"
        return self.session.query(sql.format(int(test_run_id))), single_dict

    def ignore_build(self, build_id):
        sql = "UPDATE test_run SET ignored = true WHERE id IN (SELECT test_run_id FROM test_series_mapping WHERE build_number IN ({}))"
        return self.session.query(sql.format(int(build_id))), single_dict

    def single_test_case_results(self, test_run_id, test_id):
        return self.session.query(sql_queries.single_test_result(test_run_id, test_id)), single_dict

    def parent_suite_results(self, test_run_id, test_id):
        return self.session.query(sql_queries.parent_suite_results(test_run_id, test_id)), list_of_dicts

    def log_message_map(self, test_run_id):
        def log_message_mapper(rows):
            messages = list_of_dicts(rows)
            message_map = defaultdict(lambda: [])
            for message in messages:
                key = (message['suite_id'], message['test_id'])
                message_map[key].append(message)
            return message_map
        return self.session.query(sql_queries.log_messages(test_run_id)), log_message_mapper

    def build_metadata(self, series, build_num):
        return self.session.query(sql_queries.build_metadata(series, build_num)), metadata_dict

    def test_run_metadata(self, test_run_id):
        return self.session.query(sql_queries.test_run_metadata(test_run_id)), metadata_dict

    def included_in_builds(self, test_run_id):
        return self.session.query(sql_queries.included_in_builds(test_run_id)), list_of_dicts

    def suite_result_statistics(self, series, last, offset, build_num):
        sql = sql_queries.status_ratios('suite', series, last, offset, build_num, per_build=False)
        return self.session.query(sql), single_dict

    def test_result_statistics(self, series, last, offset, build_num):
        sql = sql_queries.status_ratios('test', series, last, offset, build_num, per_build=False)
        return self.session.query(sql), single_dict

    def suite_result_statistics_per_build(self, series, last, offset, build_num):
        sql = sql_queries.status_ratios('suite', series, last, offset, build_num, per_build=True)
        return self.session.query(sql), list_of_dicts

    def test_result_statistics_per_build(self, series, last, offset, build_num):
        sql = sql_queries.status_ratios('test', series, last, offset, build_num, per_build=True)
        return self.session.query(sql), list_of_dicts

    def recently_failing_tests(self, top, series, build_num, last, offset):
        sql = sql_queries.recently_failing_tests(top, series, build_num, last, offset)
        return self.session.query(sql), list_of_dicts

    def recently_failing_suites(self, top, series, build_num, last, offset):
        sql = sql_queries.recently_failing_suites(top, series, build_num, last, offset)
        return self.session.query(sql), list_of_dicts

    def keyword_tree(self, fingerprint):
        sql = "SELECT * FROM keyword_tree WHERE fingerprint=%(fingerprint)s"
        return self.session.query(sql, {'fingerprint': fingerprint}), single_dict

    def subtrees(self, fingerprint):
        return self.session.query(sql_queries.SUBTREES, {'fingerprint': fingerprint}), list_of_dicts

    def tree_execution_measures(self, fingerprint, series_id, build_num, last, offset):
        sql = sql_queries.tree_execution_measures(fingerprint, series_id, build_num, last, offset)
        return self.session.query(sql), single_dict


def single_dict(rows):
    return list_of_dicts(rows)[0] if rows else None


def list_of_dicts(rows):
    results = []
    for row in rows:
        for key in row:
            if isinstance(row[key], (datetime.time, datetime.date, datetime.datetime, datetime.timedelta)):
                row[key] = str(row[key])
        results.append(row)
    return results


def metadata_dict(rows):
    metadata = defaultdict(lambda: {})
    for row in rows:
        key = (row['suite_id'], row['test_run_id'])
        metadata[key][row['name']] = row['value']
    return metadata


if __name__ == '__main__':
    pass

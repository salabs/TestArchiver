import argparse
import json
import os
import sys
import datetime
import time


import database as db
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import gen

APP_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STATIC_DIRECTORY = os.path.abspath(os.path.join(APP_DIRECTORY, 'static'))
TEMPLATES_DIRECTORY = os.path.abspath(os.path.join(APP_DIRECTORY, 'templates'))


def load_config_file(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)


class Application(tornado.web.Application):
    def __init__(self, database, config):
        handlers = [
            (r"/data/last/", LastDataHandler),
            (r"/data/series/", SeriesDataHandler),
            (r"/data/teams/", TeamsDataHandler),
            (r"/data/type/", TypeDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/builds/", BuildsDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/results/", BuildResultsDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/results_by_time/(?P<start>[0-9]+)/", BuildResultsByTimeDataHandler1),
            (r"/data/series/(?P<series_id>[0-9]+)/results_by_time/(?P<start>[0-9]+)/(?P<end>[0-9]+)/", BuildResultsByTimeDataHandler1),
            (r"/data/series/(?P<series_id>[0-9]+)/results_by_time/(?P<startyear>[0-9]+)/(?P<startmonth>[0-9]+)/(?P<startday>[0-9]+)/(?P<starthour>[0-9]+)/(?P<startminute>[0-9]+)/offset/(?P<endyear>[0-9]+)/(?P<endmonth>[0-9]+)/(?P<endday>[0-9]+)/(?P<endhour>[0-9]+)/(?P<endminute>[0-9]+)/", BuildResultsByTimeDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/results_by_time/(?P<startyear>[0-9]+)/(?P<startmonth>[0-9]+)/(?P<startday>[0-9]+)/(?P<starthour>[0-9]+)/(?P<startminute>[0-9]+)/", BuildResultsByTimeDataHandler),
            (r"/data/test_run/(?P<test_run_id>[0-9]+)/", TestRunDataHandler),
            (r"/data/test_run/(?P<test_run_id>[0-9]+)/ignore/", IgnoreTestRunHandler),
            (r"/data/test_run/(?P<test_run_id>[0-9]+)/results/", TestRunResultsDataHandler),
            (r"/data/test_run/(?P<test_run_id>[0-9]+)/test_case/(?P<test_id>[0-9]+)/", TestCaseResultsDataHandler),
            (r"/data/keyword_tree/(?P<fingerprint>[0-9a-f]{40})/", KeywordTreeDataHandler),
            (r"/data/keyword_tree/(?P<fingerprint>[0-9a-f]{40})/stats", KeywordTreeStatsDataHandler),

            (r"/data/series/(?P<series_id>[0-9]+)/recently_failing_tests/", RecentlyFailingTestsDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/recently_failing_suites/", RecentlyFailingSuitesDataHandler),

            (r"/data/series/(?P<series_id>[0-9]+)/test_status_statistics/", TestStatusStatsDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/build/(?P<build>[0-9]+)/test_status_statistics/", TestStatusStatsDataHandler),
            (r"/data/test_status_statistics/", TestStatusStatsDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/suite_status_statistics/", SuiteStatusStatsDataHandler),
            (r"/data/series/(?P<series_id>[0-9]+)/build/(?P<build>[0-9]+)/suite_status_statistics/", SuiteStatusStatsDataHandler),
            (r"/data/suite_status_statistics/", SuiteStatusStatsDataHandler),

            # For query testing purposes only
            (r"/data/foo/", FooDataHandler),
        ]

        settings = dict(
            template_path=TEMPLATES_DIRECTORY,
            static_path=STATIC_DIRECTORY,
            debug=True,
        )
        self.database = database
        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    @property
    def database(self):
        return self.application.database

    @gen.coroutine
    def async_query(self, querer, *args, **kwargs):
        rows, formatter = querer(*args, **kwargs)
        rows = yield rows
        results = formatter(rows)
        if isinstance(rows, list):
            for connection in rows:
                connection.free()
        else:
            rows.free()
        return results

    @gen.coroutine
    def keyword_tree(self, fingerprint):
        if not fingerprint:
            return None
        keyword_tree = yield self.async_query(self.database.keyword_tree, fingerprint)
        if keyword_tree:
            keyword_tree['children'] = []
            keyword_tree = yield self.child_trees(keyword_tree)
            return keyword_tree
        else:
            return None

    @gen.coroutine
    def child_trees(self, keyword_tree):
        children = yield self.async_query(self.database.subtrees, keyword_tree['fingerprint'])
        for child in children:
            child_tree = yield self.child_trees(child)
            if 'children' not in keyword_tree:
                keyword_tree['children'] = []
            keyword_tree['children'].append(child_tree)
        return keyword_tree

class LastDataHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        last = yield self.async_query(self.database.last_update)
        self.write({'last': last})

class SeriesDataHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        series = yield self.async_query(self.database.test_series)
        self.write({'series': series})


class TeamsDataHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        teams = yield self.async_query(self.database.teams)
        self.write({'teams': teams})

class TypeDataHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        db_type = yield self.async_query(self.database.db_type)
        self.write({'db_type': db_type})

class BuildsDataHandler(BaseHandler):
    @gen.coroutine
    def get(self, series_id):
        last = self.get_argument('last', 10)
        offset = self.get_argument('offset', 0)
        build = self.get_argument('build', None)
        builds = yield self.async_query(self.database.builds, series_id, build, last, offset)
        self.write({'builds': builds})


class BuildResultsDataHandler(BaseHandler):

    @gen.coroutine
    def get(self, series_id, build=None):
        last = self.get_argument('last', 10)
        offset = self.get_argument('offset', 0)
        build = build if build else self.get_argument('build', None)
        builds = yield self.async_query(self.database.builds, series_id, build, last, offset)

        for build in builds:
            results, metadata = yield [
                self.async_query(self.database.build_results, series_id, build['build_number']),
                self.async_query(self.database.build_metadata, series_id, build['build_number']),
            ]
            previous_suite_id = None
            suite = None
            build['suites'] = []
            for result in results:
                if previous_suite_id != result['suite_id']:
                    if previous_suite_id:
                        build['suites'].append(suite)
                    suite = {key[6:]: result[key] for key in result if key.startswith('suite_')}
                    relevant_metadata = metadata[(suite['id'], suite['test_run_id'])]
                    suite['metadata'] = [{'name': name, 'value': relevant_metadata[name]} for name in relevant_metadata]
                    suite['tests'] = []

                if result['id']:
                    test = {key: result[key] for key in result if not key.startswith('suite_')}
                    suite['tests'].append(test)

                previous_suite_id = result['suite_id']
            if suite:
                build['suites'].append(suite)

        self.write({'builds': builds})

class BuildResultsByTimeDataHandler1(BaseHandler):
    
    @gen.coroutine
    def get(self, series_id, start, end=None, build=None):
        startInt = int(start)
        searchTimeStart = datetime.datetime.fromtimestamp(startInt)
        if end:
            endInt = int(end)
            searchTimeEnd = datetime.datetime.fromtimestamp(endInt)
        else:
            searchTimeEnd = datetime.datetime.now()
        last = self.get_argument('last', 100)
        offset = self.get_argument('offset', 0)
        build = build if build else self.get_argument('build', None)
        builds = yield self.async_query(self.database.builds_by_time, series_id, build, last, offset, searchTimeStart, searchTimeEnd)

        for build in builds:
            results, metadata = yield [
                self.async_query(self.database.build_results, series_id, build['build_number']),
                self.async_query(self.database.build_metadata, series_id, build['build_number']),
            ]
            previous_suite_id = None
            suite = None
            build['suites'] = []
            for result in results:
                if previous_suite_id != result['suite_id']:
                    if previous_suite_id:
                        build['suites'].append(suite)
                    suite = {key[6:]: result[key] for key in result if key.startswith('suite_')}
                    relevant_metadata = metadata[(suite['id'], suite['test_run_id'])]
                    suite['metadata'] = [{'name': name, 'value': relevant_metadata[name]} for name in relevant_metadata]
                    suite['tests'] = []

                if result['id']:
                    test = {key: result[key] for key in result if not key.startswith('suite_')}
                    suite['tests'].append(test)

                previous_suite_id = result['suite_id']
            if suite:
                build['suites'].append(suite)

        self.write({'builds': builds})

class BuildResultsByTimeDataHandler(BaseHandler):

    @gen.coroutine
    def get(self, series_id, startyear, startmonth, startday, starthour, startminute, endyear=None, endmonth=None, endday=None, endhour=None, endminute=None, build=None):
        searchTimeStart = datetime.datetime(int(startyear), int(startmonth), int(startday), int(starthour), int(startminute))
        if endyear:
            searchTimeEnd = datetime.datetime(int(endyear), int(endmonth), int(endday), int(endhour), int(endminute))
        else:
            searchTimeEnd = datetime.datetime.now()
        last = self.get_argument('last', 10)
        offset = self.get_argument('offset', 0)
        build = build if build else self.get_argument('build', None)
        builds = yield self.async_query(self.database.builds_by_time, series_id, build, last, offset, searchTimeStart, searchTimeEnd)

        for build in builds:
            results, metadata = yield [
                self.async_query(self.database.build_results, series_id, build['build_number']),
                self.async_query(self.database.build_metadata, series_id, build['build_number']),
            ]
            previous_suite_id = None
            suite = None
            build['suites'] = []
            for result in results:
                if previous_suite_id != result['suite_id']:
                    if previous_suite_id:
                        build['suites'].append(suite)
                    suite = {key[6:]: result[key] for key in result if key.startswith('suite_')}
                    relevant_metadata = metadata[(suite['id'], suite['test_run_id'])]
                    suite['metadata'] = [{'name': name, 'value': relevant_metadata[name]} for name in relevant_metadata]
                    suite['tests'] = []

                if result['id']:
                    test = {key: result[key] for key in result if not key.startswith('suite_')}
                    suite['tests'].append(test)

                previous_suite_id = result['suite_id']
            if suite:
                build['suites'].append(suite)

        self.write({'builds': builds})


class TestRunDataHandler(BaseHandler):

    @gen.coroutine
    def get(self, test_run_id):
        data = yield self.async_query(self.database.test_run_data, test_run_id)
        self.write(data)

class IgnoreTestRunHandler(BaseHandler):

    @gen.coroutine
    def post(self, test_run_id):
        data = yield self.async_query(self.database.ignore_test_run, test_run_id)
        self.write(data)


class TestRunResultsDataHandler(BaseHandler):

    @gen.coroutine
    def get(self, test_run_id):
        results, metadata, builds = yield [
            self.async_query(self.database.test_run_results, test_run_id),
            self.async_query(self.database.test_run_metadata, test_run_id),
            self.async_query(self.database.included_in_builds, test_run_id),
        ]
        previous_suite_id = None
        suite = None
        test_run = {'suites': []}
        for result in results:
            if previous_suite_id != result['suite_id']:
                if previous_suite_id:
                    test_run['suites'].append(suite)
                suite = {key[6:]: result[key] for key in result if key.startswith('suite_')}
                relevant_metadata = metadata[(suite['id'], suite['test_run_id'])]
                suite['metadata'] = [{'name': name, 'value': relevant_metadata[name]} for name in relevant_metadata]
                suite['tests'] = []

            if result['id']:
                test = {key: result[key] for key in result if not key.startswith('suite_')}
                suite['tests'].append(test)

            previous_suite_id = result['suite_id']
        if suite:
            test_run['suites'].append(suite)
        test_run['included_in_builds'] = builds
        self.write(test_run)

class TestCaseResultsDataHandler(BaseHandler):

    @gen.coroutine
    def get(self, test_run_id, test_id):
        suites = []
        parent_suite_results, test_results, metadata, log_message_map = yield [
                self.async_query(self.database.parent_suite_results, test_run_id, test_id),
                self.async_query(self.database.single_test_case_results, test_run_id, test_id),
                self.async_query(self.database.test_run_metadata, test_run_id),
                self.async_query(self.database.log_message_map, test_run_id),
            ]
        for results in parent_suite_results:
            suite = _suite_related_values(results)
            suite['setup'] = yield self.keyword_tree(suite['setup_fingerprint'])
            suite['teardown'] = yield self.keyword_tree(suite['teardown_fingerprint'])
            relevant_metadata = metadata[(suite['id'], suite['test_run_id'])]
            suite['metadata'] = [{'name': name, 'value': relevant_metadata[name]} for name in relevant_metadata]
            suite['log_messages'] = log_message_map[(suite['id'], None)]
            suites.append(suite)
        suite = _suite_related_values(test_results)
        suite['setup'] = yield self.keyword_tree(suite['setup_fingerprint'])
        suite['teardown'] = yield self.keyword_tree(suite['teardown_fingerprint'])
        suite['log_messages'] = log_message_map[(suite['id'], None)]
        test = _non_suite_related_values(test_results)
        test['setup'] = yield self.keyword_tree(test['setup_fingerprint'])
        test['execution'] = yield self.keyword_tree(test['execution_fingerprint'])
        test['teardown'] = yield self.keyword_tree(test['teardown_fingerprint'])
        test['log_messages'] = log_message_map[(suite['id'], test['id'])]
        suite['tests'] = [test]
        relevant_metadata = metadata[(suite['id'], suite['test_run_id'])]
        suite['metadata'] = [{'name': name, 'value': relevant_metadata[name]} for name in relevant_metadata]
        suites.append(suite)
        self.write({'suites': suites})


class TestStatusStatsDataHandler(BaseHandler):
    @gen.coroutine
    def get(self, series_id=None, build=None):
        series_id = series_id if series_id else self.get_argument('series', None)
        build = build if build else self.get_argument('build', None)
        last = self.get_argument('last', 10)
        offset = self.get_argument('offset', 0)
        total, per_build = yield [
            self.async_query(self.database.test_result_statistics, series_id, last, offset, build),
            self.async_query(self.database.test_result_statistics_per_build, series_id, last, offset, build),
        ]
        self.write({'total': total, 'per_build': per_build})


class KeywordTreeDataHandler(BaseHandler):
    @gen.coroutine
    def get(self, fingerprint):
        keyword_tree = yield self.keyword_tree(fingerprint)
        if keyword_tree:
            self.write(keyword_tree)
        else:
            self.set_status(404)
            self.write({'Error': "Not found!", 'fingerprint': fingerprint})



class KeywordTreeStatsDataHandler(BaseHandler):
    @gen.coroutine
    def get(self, fingerprint):
        series = self.get_argument('series', None)
        build = self.get_argument('build', None)
        last = self.get_argument('last', None)
        offset = self.get_argument('offset', 0)
        stats = yield self.async_query(self.database.tree_execution_measures, fingerprint,
                                       series, build, last, offset)
        if stats:
            self.write(stats)
        else:
            self.set_status(404)
            self.write({'Error': "Not found!", 'fingerprint': fingerprint})


class SuiteStatusStatsDataHandler(BaseHandler):
    @gen.coroutine
    def get(self, series_id=None, build=None):
        series_id = series_id if series_id else self.get_argument('series', None)
        build = build if build else self.get_argument('build', None)
        last = self.get_argument('last', 10)
        offset = self.get_argument('offset', 0)
        total, per_build = yield [
            self.async_query(self.database.suite_result_statistics, series_id, last, offset, build),
            self.async_query(self.database.suite_result_statistics_per_build, series_id, last, offset, build)
        ]
        self.write({'total': total, 'per_build': per_build})


class RecentlyFailingTestsDataHandler(BaseHandler):
    @gen.coroutine
    def get(self, series_id=None, build=None):
        series_id = series_id if series_id else self.get_argument('series', None)
        build = build if build else self.get_argument('build', None)
        top = self.get_argument('top', 10)
        last = self.get_argument('last', 10)
        offset = self.get_argument('offset', 0)
        tests = yield self.async_query(self.database.recently_failing_tests, top, series_id, build, last, offset)
        self.write({'tests': tests})


class RecentlyFailingSuitesDataHandler(BaseHandler):
    @gen.coroutine
    def get(self, series_id=None, build=None):
        series_id = series_id if series_id else self.get_argument('series', None)
        build = build if build else self.get_argument('build', None)
        top = self.get_argument('top', 10)
        last = self.get_argument('last', 10)
        offset = self.get_argument('offset', 0)
        suites = yield self.async_query(self.database.recently_failing_suites, top, series_id, build, last, offset)
        self.write({'suites': suites})


class FooDataHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        self.write({'suites': []})

def _suite_related_values(result):
    return {key[6:]: result[key] for key in result if key.startswith('suite_')}

def _non_suite_related_values(result):
    return {key: result[key] for key in result if not key.startswith('suite_')}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test manager backend server')
    parser.add_argument('--config', dest='config_file',
                        help='path to JSON config file containing database credentials')
    parser.add_argument('--database', help='database name')
    parser.add_argument('--host', help='databse host name', default=None)
    parser.add_argument('--user', help='database user')
    parser.add_argument('--pw', '--password', help='database password')
    parser.add_argument('--port', help='database port (default: 5432)', default=5432, type=int)
    args = parser.parse_args()

    if args.config_file:
        config = load_config_file(args.config_file)
    else:
        config = {
            'db_name': args.database,
            'db_user': args.user,
            'db_password': args.pw,
            'db_host': args.host,
            'port': args.port,
        }

    httpserver = tornado.httpserver.HTTPServer(
        Application(
            db.Database(
                config['db_host'],
                config['db_name'],
                config['db_user'],
                config['db_password']
            ), config
        )
    )
    httpserver.listen(int(config['port']))
    print("Server listening port {}".format(config['port']))
    tornado.ioloop.IOLoop.current().start()

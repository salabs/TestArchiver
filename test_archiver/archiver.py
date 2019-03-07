import json
from hashlib import sha1
from datetime import datetime

from database import PostgresqlDatabase, SQLiteDatabase

ARCHIVER_VERSION = "0.2"

ROBOT_TIMESTAMP_FORMAT = "%Y%m%d %H:%M:%S.%f"
MAX_LOG_MESSAGE_LENGTH = 2000

def read_config_file(file_name):
    with open(file_name, 'r') as config_file:
        return json.load(config_file)

class TestItem(object):
    def __init__(self, archiver):
        self.archiver = archiver

    def _item_type(self):
        raise NotImplementedError()

    def parent_suite(self):
        for item in reversed(self.archiver.stack):
            if item._item_type() == 'suite':
                return item
        return None

    def parent_test(self):
        for item in reversed(self.archiver.stack):
            if item._item_type() == 'test':
                return item
        return None

    def _parent_item(self):
        return self.archiver.stack[-1] if self.archiver.stack else None

class FingerprintedItem(TestItem):
    def __init__(self, archiver, name):
        super(FingerprintedItem, self).__init__(archiver)
        self.name = name
        self.parent_item = self._parent_item()
        parent_prefix = self.parent_item.full_name + '.' if self.parent_item else ''
        self.full_name = parent_prefix + self.name
        self.id = None

        self.status = None
        self.setup_status = None
        self.execution_status = None
        self.teardown_status = None

        self.start_time = None
        self.end_time = None

        self.kw_type = None
        self.library = None
        self.arguments = []
        self.tags = []
        self.metadata = {}
        self._last_metadata_name = None

        self.subtree_fingerprints = []
        self.fingerprint = None
        self.setup_fingerprint = None
        self.execution_fingerprint = None
        self.teardown_fingerprint = None

    def update_status(self, status, start_time, end_time):
        if status == 'NOT_RUN':
            # If some keyword is not executed the execution was a dryrun
            self.archiver.output_from_dryrun = True
        self.status = status
        self.start_time = datetime.strptime(start_time, ROBOT_TIMESTAMP_FORMAT)
        self.end_time = datetime.strptime(end_time, ROBOT_TIMESTAMP_FORMAT)
        self.elapsed_time = int((self.end_time - self.start_time).total_seconds()*1000)

    def _hashing_name(self):
        return self.full_name

    def finish(self):
        self.calculate_fingerprints()
        self.propagate_fingerprints_and_status()
        self.insert_results()

    def calculate_fingerprints(self):
        if self.subtree_fingerprints:
            execution = sha1()
            for child in self.subtree_fingerprints:
                execution.update(child.encode('utf-8'))
            self.execution_fingerprint = execution.hexdigest()

        fingerprint = sha1()
        fingerprint.update(self._hashing_name().encode('utf-8'))
        fingerprint.update(str(self.setup_fingerprint).encode('utf-8'))
        fingerprint.update(str(self.execution_fingerprint).encode('utf-8'))
        fingerprint.update(str(self.teardown_fingerprint).encode('utf-8'))
        fingerprint.update(self.status.encode('utf-8'))
        fingerprint.update(str(self.arguments).encode('utf-8'))
        self.fingerprint = fingerprint.hexdigest()

    def propagate_fingerprints_and_status(self):
        if self.kw_type == 'setup':
            self.parent_item.setup_fingerprint = self.fingerprint
            self.parent_item.setup_status = self.status
        elif self.kw_type == 'teardown':
            self.parent_item.teardown_fingerprint = self.fingerprint
            self.parent_item.teardown_status = self.status
        else:
            if self.parent_item:
                self.parent_item.subtree_fingerprints.append(self.fingerprint)
                if self.parent_item.execution_status != 'FAIL':
                    self.parent_item.execution_status = self.status

    def status_and_fingerprint_values(self):
        return {'status': self.status,
                'setup_status': self.setup_status,
                'execution_status': self.execution_status,
                'teardown_status': self.teardown_status,
                'start_time': self.start_time,
                'elapsed': self.elapsed_time,
                'fingerprint': self.fingerprint,
                'setup_fingerprint': self.setup_fingerprint,
                'execution_fingerprint': self.execution_fingerprint,
                'teardown_fingerprint': self.teardown_fingerprint}

class Suite(FingerprintedItem):
    def __init__(self, archiver, name, repository):
        super(Suite, self).__init__(archiver, name)
        data = {'full_name': self.full_name, 'name': name, 'repository': repository}
        self.id = self.archiver.db.insert_and_return_id('suite', data, ['repository', 'full_name'])

    def _item_type(self):
        return "suite"

    def insert_results(self):
        data = {'suite_id': self.id, 'test_run_id': self.archiver.test_run_id}
        data.update(self.status_and_fingerprint_values())
        self.archiver.db.insert('suite_result', data)
        self.insert_metadata()

    def insert_metadata(self):
        for name in self.metadata:
            content = self.metadata[name]
            data = {'name': name, 'value': content,
                    'suite_id': self.id, 'test_run_id': self.archiver.test_run_id}
            self.archiver.db.insert('suite_metadata', data)
            if name.startswith('series') and '#' in content:
                series_name, build_number = content.split('#')
                self.archiver.test_series[series_name] = build_number
            elif name == 'team':
                self.archiver.team = content

class Test(FingerprintedItem):
    def __init__(self, archiver, name):
        super(Test, self).__init__(archiver, name)
        data = {'full_name': self.full_name, 'name': name, 'suite_id': self.parent_item.id}
        self.id = self.archiver.db.insert_and_return_id('test_case', data, ['suite_id', 'name'])

    def _item_type(self):
        return "test"

    def insert_results(self):
        data = {'test_id': self.id, 'test_run_id': self.archiver.test_run_id}
        data.update(self.status_and_fingerprint_values())
        self.archiver.db.insert('test_result', data)
        if self.subtree_fingerprints:
            data = {'fingerprint': self.execution_fingerprint, 'keyword': None, 'library': None,
                'status': self.execution_status, 'arguments': self.arguments}
            self.archiver.db.insert_or_ignore('keyword_tree', data, ['fingerprint'])
        self.insert_subtrees()
        self.insert_tags()

    def insert_tags(self):
        for tag in self.tags:
            data = {'tag': tag, 'test_id': self.id, 'test_run_id': self.archiver.test_run_id}
            self.archiver.db.insert('test_tag', data)

    def insert_subtrees(self):
        call_index = 0
        for subtree in self.subtree_fingerprints:
            data = {'fingerprint': self.execution_fingerprint, 'subtree': subtree, 'call_index': call_index}
            key_values = ['fingerprint', 'subtree', 'call_index']
            self.archiver.db.insert_or_ignore('tree_hierarchy', data, key_values)
            call_index += 1


class Keyword(FingerprintedItem):
    def __init__(self, archiver, name, library, kw_type, arguments):
        super(Keyword, self).__init__(archiver, name)
        self.library = library
        self.kw_type = kw_type
        if arguments:
            self.arguments.extend(arguments)

    def _item_type(self):
        return "keyword"

    def insert_results(self):
        data = {'fingerprint': self.fingerprint, 'keyword': self.name, 'library': self.library,
                'status': self.status, 'arguments': self.arguments}
        self.archiver.db.insert_or_ignore('keyword_tree', data, ['fingerprint'])
        self.insert_subtrees()

    def insert_subtrees(self):
        call_index = 0
        for subtree in self.subtree_fingerprints:
            data = {'fingerprint': self.fingerprint, 'subtree': subtree, 'call_index': call_index}
            key_values = ['fingerprint', 'subtree', 'call_index']
            self.archiver.db.insert_or_ignore('tree_hierarchy', data, key_values)
            call_index += 1

    def _hashing_name(self):
        return self.library + '.' + self.name


class LogMessage(TestItem):
    def __init__(self, archiver, log_level, timestamp):
        self.archiver = archiver
        self.log_level = log_level
        self.timestamp = timestamp

    def _item_type(self):
        return "log_message"

    def insert(self, content):
        data = {'test_run_id': self.archiver.test_run_id, 'timestamp': self.timestamp,
                'log_level': self.log_level, 'message': content[:MAX_LOG_MESSAGE_LENGTH],
                'test_id': self.parent_test().id, 'suite_id': self.parent_suite().id}
        self.id = self.archiver.db.insert('log_message', data)



class Archiver(object):
    def __init__(self, db_engine, config):
        self.config = config
        self.test_run_id = None
        self.test_series = {}
        self.team = None
        self.repository = config['repository'] if 'repository' in config else 'default repo'
        self.output_from_dryrun = False
        self.db = self._db(db_engine)
        self.stack = []

    def _db(self, db_engine):
        if db_engine == 'postgresql':
            return PostgresqlDatabase(
                    self.config['database'],
                    self.config['host'],
                    self.config['port'],
                    self.config['user'],
                    self.config['password'],
                )
        elif db_engine == 'sqlite':
            return SQLiteDatabase(self.config['database'])
        else:
            raise Exception("Unsupported database type '{}'".format(db_engine))

    def _current_item(self):
        return self.stack[-1] if self.stack else None

    def begin_test_run(self, archived_using, generated, generator, rpa, dryrun):
        data = {
                'archived_using': archived_using + ARCHIVER_VERSION,
                'generated': generated,
                'generator': generator,
                'rpa': rpa,
                'dryrun': dryrun,
            }
        self.test_run_id = self.db.insert_and_return_id('test_run', data)

    def update_dryrun_status(self):
        data = {'dryrun': self.output_from_dryrun}
        self.db.update('test_run', data, {'id': self.test_run_id})

    def end_test_run(self):
        for name in self.test_series:
            self.report_series(name, self.test_series[name])
        if not self.test_series:
            self.report_series('default series', None)
        self.db._connection.commit()

    def report_series(self, name, build_number):
        data = {
                'team': self.team if self.team else 'No team',
                'name': name,
            }
        series_id = self.db.insert_and_return_id('test_series', data, ['team', 'name'])

        if not build_number:
            previous_build_number = self.db.max_value('test_series_mapping', 'build_number',
                                                      {'series': series_id})
            build_number = previous_build_number + 1 if previous_build_number else 1
        data = {
                'series': series_id,
                'test_run_id': self.test_run_id,
                'build_number': build_number,
            }
        self.db.insert('test_series_mapping', data)

    def begin_suite(self, name):
        self.stack.append(Suite(self, name, 'repo'))

    def end_suite(self, attributes):
        if attributes:
            self._current_item().update_status(attributes['status'], attributes['starttime'],
                                               attributes['endtime'])
            self._current_item().metadata = attributes['metadata']
        self.stack.pop().finish()

    def begin_test(self, name):
        self.stack.append(Test(self, name))

    def end_test(self, attributes):
        if attributes:
            self._current_item().update_status(attributes['status'], attributes['starttime'],
                                               attributes['endtime'])
            self._current_item().tags = attributes['tags']
        self.stack.pop().finish()

    def begin_status(self, status, start_time, end_time):
        self._current_item().update_status(status, start_time, end_time)

    def begin_keyword(self, name, library, kw_type, arguments=None):
        self.stack.append(Keyword(self, name, library, kw_type.lower(), arguments))

    def end_keyword(self, attributes):
        if attributes:
            self._current_item().update_status(attributes['status'], attributes['starttime'],
                                               attributes['endtime'])
        self.stack.pop().finish()

    def update_argumets(self, argument):
        self._current_item().arguments.append(argument)

    def update_tags(self, tag):
        self._current_item().tags.append(tag)

    def begin_metadata(self, name):
        self._current_item()._last_metadata_name = name

    def end_metadata(self, content):
        self._current_item().metadata[self._current_item()._last_metadata_name] = content

    def begin_log_message(self, level, timestamp):
        self.stack.append(LogMessage(self, level, timestamp))

    def end_log_message(self, content):
        self._current_item().insert(content)
        self.stack.pop()


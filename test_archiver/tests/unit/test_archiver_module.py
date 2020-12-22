# pylint: disable=W0212

import unittest
from mock import Mock

from test_archiver import configs, archiver

class TestTestItem(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.config = configs.Config(file_config={})
        self.archiver = archiver.Archiver(self.mock_db, self.config)
        self.item = archiver.TestItem(self.archiver)

    def test_parent_suite(self):
        self.assertEqual(self.item.parent_suite(), None)

        test_run = archiver.TestRun(self.archiver, 'unittests', 'never', 'unittests', None, None)
        self.archiver.stack.append(test_run)
        self.assertEqual(self.item.parent_suite(), None)

        suite1 = archiver.Suite(self.archiver, 'mock_suite1', 'mock_repo')
        self.archiver.stack.append(suite1)
        self.assertEqual(self.item.parent_suite(), suite1)

        suite2 = archiver.Suite(self.archiver, 'mock_suite2', 'mock_repo')
        self.archiver.stack.append(suite2)
        self.assertEqual(self.item.parent_suite(), suite2)

        test = archiver.Test(self.archiver, 'mock_test', None)
        self.archiver.stack.append(test)
        self.assertEqual(self.item.parent_suite(), suite2)

    def test_parent_test(self):
        self.assertEqual(self.item.parent_test(), None)

        test_run = archiver.TestRun(self.archiver, 'unittests', 'never', 'unittests', None, None)
        self.archiver.stack.append(test_run)
        self.assertEqual(self.item.parent_test(), None)

        suite1 = archiver.Suite(self.archiver, 'mock_suite1', 'mock_repo')
        self.archiver.stack.append(suite1)
        self.assertEqual(self.item.parent_test(), None)

        suite2 = archiver.Suite(self.archiver, 'mock_suite2', 'mock_repo')
        self.archiver.stack.append(suite2)
        self.assertEqual(self.item.parent_test(), None)

        test = archiver.Test(self.archiver, 'mock_test', None)
        self.archiver.stack.append(test)
        self.assertEqual(self.item.parent_test(), test)

        keyword = archiver.Keyword(self.archiver, 'mock_kw', None, None, None)
        self.archiver.stack.append(keyword)
        self.assertEqual(self.item.parent_test(), test)

    def test_parent_item(self):
        self.assertEqual(self.item._parent_item(), None)

        test_run = archiver.TestRun(self.archiver, 'unittests', 'never', 'unittests', None, None)
        self.archiver.stack.append(test_run)
        self.assertEqual(self.item._parent_item(), test_run)

        suite1 = archiver.Suite(self.archiver, 'mock_suite1', 'mock_repo')
        self.archiver.stack.append(suite1)
        self.assertEqual(self.item._parent_item(), suite1)

        suite2 = archiver.Suite(self.archiver, 'mock_suite2', 'mock_repo')
        self.archiver.stack.append(suite2)
        self.assertEqual(self.item._parent_item(), suite2)

        test = archiver.Test(self.archiver, 'mock_test', None)
        self.archiver.stack.append(test)
        self.assertEqual(self.item._parent_item(), test)

        keyword = archiver.Keyword(self.archiver, 'mock_kw', None, None, None)
        self.archiver.stack.append(keyword)
        self.assertEqual(self.item._parent_item(), keyword)

    def test_test_run_id(self):
        self.assertEqual(self.item.test_run_id(), None)

        self.mock_db.insert_and_return_id.return_value = 1234
        self.archiver.begin_test_run('unittests', 'never', 'unittests', None, None)
        self.assertEqual(self.item.test_run_id(), 1234)


class SutFingerprintedItem(archiver.FingerprintedItem):
    def _execution_path_identifier(self):
        return 'sut'


class TestFingerprintedItem(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.config = configs.Config(file_config={})
        self.archiver = archiver.Archiver(self.mock_db, self.config)
        self.item = SutFingerprintedItem(self.archiver, 'SUT item')

    def test_child_counter(self):
        self.assertEqual(self.item.child_counter('a'), 1)
        self.assertEqual(self.item.child_counter('a'), 2)
        self.assertEqual(self.item.child_counter('b'), 1)
        self.assertEqual(self.item.child_counter('b'), 2)
        self.assertEqual(self.item.child_counter('a'), 3)

    def test_execution_path(self):
        self.assertEqual(self.item.execution_path(), 'sut1')

        self.archiver.stack.append(self.item)
        item2 = SutFingerprintedItem(self.archiver, 'SUT item 2')
        self.archiver.stack.append(item2)
        self.assertEqual(item2.execution_path(), 'sut1-sut1')
        self.archiver.stack.pop(1)

        item3 = SutFingerprintedItem(self.archiver, 'SUT item 3')
        self.archiver.stack.append(item3)
        print(self.archiver.stack)
        self.assertEqual(item3.execution_path(), 'sut1-sut2')

        self.item._execution_path = 'path-to-foo'
        self.assertEqual(self.item.execution_path(), 'path-to-foo')


class TestCase(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()

    def test_keywords_are_not_archived(self):
        config = configs.Config(file_config={'archive_keywords': False})
        sut_archiver = archiver.Archiver(self.mock_db, config)
        sut_archiver.begin_suite('Some suite of tests')
        test_case = sut_archiver.begin_test('Some test case')
        test_case.subtree_fingerprints = ['abcdef1234567890']

        keyword = sut_archiver.begin_keyword('Fake kw', 'unittests', 'mock')
        keyword.subtree_fingerprints = ['abcdef1234567890']
        keyword.insert_results()
        test_case.insert_results()
        self.mock_db.insert_or_ignore.assert_not_called()
        self.assertEqual(len(sut_archiver.keyword_statistics), 0)


class TestKeyword(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()

    def test_keyword_is_inserted_by_default(self):
        config = configs.Config(file_config={})
        sut_archiver = archiver.Archiver(self.mock_db, config)
        sut_archiver.begin_suite('Some suite of tests')
        sut_archiver.begin_test('Some test case')

        keyword = sut_archiver.begin_keyword('Fake kw', 'unittests', 'mock')
        keyword.insert_results()
        self.mock_db.insert_or_ignore.assert_called_once()
        self.assertEqual(len(sut_archiver.keyword_statistics), 1)

    def test_keyword_statistics_are_not_collected(self):
        config = configs.Config(file_config={'archive_keyword_statistics': False})
        sut_archiver = archiver.Archiver(self.mock_db, config)
        sut_archiver.begin_suite('Some suite of tests')
        sut_archiver.begin_test('Some test case')

        keyword = sut_archiver.begin_keyword('Fake kw', 'unittests', 'mock')
        keyword.insert_results()
        self.mock_db.insert_or_ignore.assert_called_once()
        self.assertEqual(len(sut_archiver.keyword_statistics), 0)

    def test_keywords_are_not_archived(self):
        config = configs.Config(file_config={'archive_keywords': False})
        sut_archiver = archiver.Archiver(self.mock_db, config)
        sut_archiver.begin_suite('Some suite of tests')
        sut_archiver.begin_test('Some test case')

        keyword = sut_archiver.begin_keyword('Fake kw', 'unittests', 'mock')
        keyword.subtree_fingerprints = ['abcdef1234567890']
        keyword.insert_results()
        self.mock_db.insert_or_ignore.assert_not_called()
        self.assertEqual(len(sut_archiver.keyword_statistics), 0)


class TestLogMessage(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()

    def test_insert_not_ignored_by_default(self):
        config = configs.Config(file_config={})
        sut_archiver = archiver.Archiver(self.mock_db, config)
        sut_archiver.begin_suite('Some suite of tests')

        message = archiver.LogMessage(sut_archiver, 'WARN', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_called_once()
        message = archiver.LogMessage(sut_archiver, 'INFO', 'some_timestamp')
        message.insert('Some log message')
        self.assertEqual(self.mock_db.insert.call_count, 2)
        message = archiver.LogMessage(sut_archiver, 'TRACE', 'some_timestamp')
        message.insert('Some log message')
        self.assertEqual(self.mock_db.insert.call_count, 3)

    def test_insert_adheres_to_log_level_cut_off(self):
        config = configs.Config(file_config={'ignore_logs_below': 'WARN'})
        sut_archiver = archiver.Archiver(self.mock_db, config)
        sut_archiver.begin_suite('Some suite of tests')

        message = archiver.LogMessage(sut_archiver, 'WARN', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_called_once()
        message = archiver.LogMessage(sut_archiver, 'INFO', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_called_once()
        message = archiver.LogMessage(sut_archiver, 'TRACE', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_called_once()

    def test_logs_not_inserted_when_logs_ignored(self):
        config = configs.Config(file_config={'ignore_logs': True})
        sut_archiver = archiver.Archiver(self.mock_db, config)
        sut_archiver.begin_suite('Some suite of tests')

        message = archiver.LogMessage(sut_archiver, 'WARN', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_not_called()
        message = archiver.LogMessage(sut_archiver, 'INFO', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_not_called()
        message = archiver.LogMessage(sut_archiver, 'TRACE', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_not_called()
        message = archiver.LogMessage(sut_archiver, 'FOO', 'some_timestamp')
        message.insert('Some log message')
        self.mock_db.insert.assert_not_called()


class TestArchiverClass(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.config = configs.Config(file_config={})
        self.archiver = archiver.Archiver(self.mock_db, self.config)

    def test_suite_execution_paths_are_set_or_generated(self):
        suite1 = self.archiver.begin_suite('mock suite 1', execution_path='path-to-s1')
        self.assertEqual(suite1.execution_path(), 'path-to-s1')

        suite2 = self.archiver.begin_suite('mock suite 2')
        self.assertEqual(suite2.execution_path(), 'path-to-s1-s1')

        self.archiver.end_suite()
        suite3 = self.archiver.begin_suite('mock suite 3')
        self.assertEqual(suite3.execution_path(), 'path-to-s1-s2')

    def test_test_execution_paths_are_set(self):
        self.archiver.begin_test_run('unittests', 'never', 'unittests', None, None)
        suite1 = self.archiver.begin_suite('mock suite 1', execution_path='path-to-s1')
        self.assertEqual(suite1.execution_path(), 'path-to-s1')

        test1 = self.archiver.begin_test('mock test 1', execution_path='path-to-t3')
        self.assertEqual(test1.execution_path(), 'path-to-t3')
        self.archiver.end_test()

        suite2 = self.archiver.begin_suite('mock suite 2', execution_path='path-to-s11')
        self.assertEqual(suite2.execution_path(), 'path-to-s11')

        test2 = self.archiver.begin_test('mock test 2')
        self.assertEqual(test2.execution_path(), 'path-to-s11-t1')

        self.archiver.end_test()
        suite3 = self.archiver.begin_test('mock test 3')
        self.assertEqual(suite3.execution_path(), 'path-to-s11-t2')

    def test_keyword_and_log_message_execution_paths_are_generated(self):
        self.archiver.begin_test_run('unittests', 'never', 'unittests', None, None)
        suite1 = self.archiver.begin_suite('mock suite 1')
        self.assertEqual(suite1.execution_path(), 's1')

        keyword1 = self.archiver.begin_keyword('mock kw', 'unitests', 'setup')
        self.assertEqual(keyword1.execution_path(), 's1-k1')
        keyword2 = self.archiver.begin_keyword('mock kw', 'unitests', 'kw')
        self.assertEqual(keyword2.execution_path(), 's1-k1-k1')
        self.archiver.end_keyword()
        self.archiver.end_keyword()

        test1 = self.archiver.begin_test('mock test 1')
        self.assertEqual(test1.execution_path(), 's1-t1')

        keyword1 = self.archiver.begin_keyword('mock kw', 'unitests', 'setup')
        self.assertEqual(keyword1.execution_path(), 's1-t1-k1')
        keyword2 = self.archiver.begin_keyword('mock kw', 'unitests', 'kw')
        self.assertEqual(keyword2.execution_path(), 's1-t1-k1-k1')
        self.archiver.end_keyword()
        keyword3 = self.archiver.begin_keyword('mock kw', 'unitests', 'kw')
        self.assertEqual(keyword3.execution_path(), 's1-t1-k1-k2')

    def test_execution_context(self):
        self.assertEqual(self.archiver.execution_context, 'default')

    def test_changes(self):
        self.assertEqual(self.archiver.changes, [])


if __name__ == '__main__':
    unittest.main()

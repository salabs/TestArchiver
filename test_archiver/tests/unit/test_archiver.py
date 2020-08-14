# pylint: disable=W0212

import unittest
from mock import Mock

from configs import Config
from archiver import Archiver, FingerprintedItem, Suite, Keyword

# These classes are renamed to avoid problems with some test case collection scripts
from archiver import TestItem as ArchiverTestItem
from archiver import TestRun as ArchiverTestRun
from archiver import Test as ArchiverTestCase


class TestTestItem(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.config = Config(file_config={})
        self.archiver = Archiver(self.mock_db, self.config)
        self.item = ArchiverTestItem(self.archiver)

    def test_parent_suite(self):
        self.assertEqual(self.item.parent_suite(), None)

        test_run = ArchiverTestRun(self.archiver, 'unittests', 'never', 'unittests', None, None)
        self.archiver.stack.append(test_run)
        self.assertEqual(self.item.parent_suite(), None)

        suite1 = Suite(self.archiver, 'mock_suite1', 'mock_repo')
        self.archiver.stack.append(suite1)
        self.assertEqual(self.item.parent_suite(), suite1)

        suite2 = Suite(self.archiver, 'mock_suite2', 'mock_repo')
        self.archiver.stack.append(suite2)
        self.assertEqual(self.item.parent_suite(), suite2)

        test = ArchiverTestCase(self.archiver, 'mock_test', None)
        self.archiver.stack.append(test)
        self.assertEqual(self.item.parent_suite(), suite2)

    def test_parent_test(self):
        self.assertEqual(self.item.parent_test(), None)

        test_run = ArchiverTestRun(self.archiver, 'unittests', 'never', 'unittests', None, None)
        self.archiver.stack.append(test_run)
        self.assertEqual(self.item.parent_test(), None)

        suite1 = Suite(self.archiver, 'mock_suite1', 'mock_repo')
        self.archiver.stack.append(suite1)
        self.assertEqual(self.item.parent_test(), None)

        suite2 = Suite(self.archiver, 'mock_suite2', 'mock_repo')
        self.archiver.stack.append(suite2)
        self.assertEqual(self.item.parent_test(), None)

        test = ArchiverTestCase(self.archiver, 'mock_test', None)
        self.archiver.stack.append(test)
        self.assertEqual(self.item.parent_test(), test)

        keyword = Keyword(self.archiver, 'mock_kw', None, None, None)
        self.archiver.stack.append(keyword)
        self.assertEqual(self.item.parent_test(), test)

    def test_parent_item(self):
        self.assertEqual(self.item._parent_item(), None)

        test_run = ArchiverTestRun(self.archiver, 'unittests', 'never', 'unittests', None, None)
        self.archiver.stack.append(test_run)
        self.assertEqual(self.item._parent_item(), test_run)

        suite1 = Suite(self.archiver, 'mock_suite1', 'mock_repo')
        self.archiver.stack.append(suite1)
        self.assertEqual(self.item._parent_item(), suite1)

        suite2 = Suite(self.archiver, 'mock_suite2', 'mock_repo')
        self.archiver.stack.append(suite2)
        self.assertEqual(self.item._parent_item(), suite2)

        test = ArchiverTestCase(self.archiver, 'mock_test', None)
        self.archiver.stack.append(test)
        self.assertEqual(self.item._parent_item(), test)

        keyword = Keyword(self.archiver, 'mock_kw', None, None, None)
        self.archiver.stack.append(keyword)
        self.assertEqual(self.item._parent_item(), keyword)

    def test_test_run_id(self):
        self.assertEqual(self.item.test_run_id(), None)

        self.mock_db.insert_and_return_id.return_value = 1234
        self.archiver.begin_test_run('unittests', 'never', 'unittests', None, None)
        self.assertEqual(self.item.test_run_id(), 1234)


class SutFingerprintedItem(FingerprintedItem):
    def _execution_path_identifier(self):
        return 'sut'

class TestFingerprintedItem(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.config = Config(file_config={})
        self.archiver = Archiver(self.mock_db, self.config)
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


class TestArchiverClass(unittest.TestCase):

    def setUp(self):
        self.mock_db = Mock()
        self.config = Config(file_config={})
        self.archiver = Archiver(self.mock_db, self.config)

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

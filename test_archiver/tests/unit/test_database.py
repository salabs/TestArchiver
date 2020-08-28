# pylint: disable=W0212

import os
import shutil
import unittest
from mock import Mock

from test_archiver import database, configs


class TestSchemaCheckingAndUpdatesWithMockDatabase(unittest.TestCase):

    def setUp(self):
        class MockDatabase(database.BaseDatabase):
            def _db_engine_identifier(self):
                return 'mock'

        MockDatabase._connect = Mock()
        MockDatabase._latest_update_applied = Mock()
        MockDatabase._initialize_schema = Mock()
        MockDatabase._run_script = Mock()
        MockDatabase.fetch_one_value = Mock()
        self.mock_db_class = MockDatabase

    def test_check_and_update_schema_initializes_schema(self):
        mock_db = self.mock_db_class(configs.Config())
        mock_db._latest_update_applied.return_value = None
        mock_db._initialize_schema.return_value = True

        mock_db.check_and_update_schema()
        mock_db._initialize_schema.assert_called_once()
        mock_db._run_script.assert_not_called()

    def test_check_and_update_schema_runs_updates_on_v1_schema_when_allowed(self):
        config = configs.Config(file_config={'allow_major_schema_updates': True})
        mock_db = self.mock_db_class(config)
        mock_db._latest_update_applied.return_value = None
        mock_db._initialize_schema.return_value = False

        mock_db.check_and_update_schema()
        mock_db._initialize_schema.assert_called_once()
        self.assertEqual(mock_db._run_script.call_count, len(database.SCHEMA_UPDATES))

    def test_check_and_update_schema_runs_updates_on_v2_schema_when_allowed(self):
        config = configs.Config(file_config={'allow_major_schema_updates': True})
        mock_db = self.mock_db_class(config)
        mock_db._latest_update_applied.return_value = 1
        mock_db._initialize_schema.return_value = False
        mock_db._schema_updates = ((1001, False, 'major update'),)

        mock_db.check_and_update_schema()
        mock_db._initialize_schema.assert_not_called()
        self.assertEqual(mock_db._run_script.call_count, 1)

    def test_check_and_update_schema_does_not_run_any_updates_without_permission(self):
        mock_db = self.mock_db_class(configs.Config())
        mock_db._latest_update_applied.return_value = 0
        mock_db._initialize_schema.return_value = False

        mock_db._schema_updates = ((1001, False, 'major_update.sql'),)
        with self.assertRaises(database.ArchiverSchemaException):
            mock_db.check_and_update_schema()
        mock_db._run_script.assert_not_called()

        mock_db._schema_updates = ((1001, True, 'minor_update.sql'),)
        with self.assertRaises(database.ArchiverSchemaException):
            mock_db.check_and_update_schema()
        mock_db._run_script.assert_not_called()

    def test_check_and_update_schema_does_not_run_major_updates_without_permission(self):
        mock_db = self.mock_db_class(configs.Config(file_config={'allow_minor_schema_updates': True}))
        mock_db._latest_update_applied.return_value = 0
        mock_db._schema_updates = ((1001, False, 'major_update.sql'),)

        with self.assertRaises(database.ArchiverSchemaException):
            mock_db.check_and_update_schema()

    def test_check_and_update_schema_fails_when_schema_is_too_new(self):
        mock_db = self.mock_db_class(configs.Config(file_config={'allow_major_schema_updates': True}))
        mock_db._latest_update_applied.return_value = 10002
        mock_db.fetch_one_value.return_value = 'a.b.c'
        mock_db._schema_updates = ((1001, False, 'major_update.sql'),)

        with self.assertRaises(database.ArchiverSchemaException):
            mock_db.check_and_update_schema()
        mock_db._run_script.assert_not_called()


class TestSqliteDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dir_path = os.path.join(os.path.dirname(__file__), 'temp_sqlite_dbs')
        try:
            shutil.rmtree(cls.dir_path)
        except FileNotFoundError:
            pass
        os.mkdir(cls.dir_path)

    @classmethod
    def tearDownClass(cls):
        # Comment this if you need to inspect the databases
        shutil.rmtree(cls.dir_path)

    def setUp(self):
        # Create database file for each test case
        temp_db = '{}.{}.db'.format(self.__class__.__name__, self._testMethodName)
        full_path = os.path.join(self.__class__.dir_path, temp_db)
        self.database = database.SQLiteDatabase(configs.Config(file_config={'database': full_path}))
        self.assertTrue(self.database._initialize_schema())

    def tearDown(self):
        self.database._connection.commit()

    def test_initialize_schema(self):
        inital_update = self.database.fetch_one_value('schema_updates', 'initial_update', {'id': 1})
        self.assertTrue(inital_update)
        self.assertFalse(self.database._initialize_schema())

    def test_return_id_or_insert_and_return_id(self):
        data = {'name': 'First suite', 'full_name': 'First suite', 'repository': 'foo repo'}
        returned_id_1 = self.database.return_id_or_insert_and_return_id('suite', data, ['full_name'])
        returned_id_2 = self.database.return_id_or_insert_and_return_id('suite', data, ['full_name'])
        self.assertEqual(returned_id_1, returned_id_2)
        data = {'name': 'Second suite', 'full_name': 'Second suite', 'repository': 'foo repo'}
        returned_id_3 = self.database.return_id_or_insert_and_return_id('suite', data, ['full_name'])
        self.assertNotEqual(returned_id_1, returned_id_3)

    def test_insert_and_return_id(self):
        data = {'name': 'First suite', 'full_name': 'First suite', 'repository': 'foo repo'}
        returned_id_1 = self.database.insert_and_return_id('suite', data, ['full_name'])
        with self.assertRaises(database.IntegrityError):
            self.database.insert_and_return_id('suite', data, ['full_name'])
        data = {'name': 'Second suite', 'full_name': 'Second suite', 'repository': 'foo repo'}
        returned_id_2 = self.database.return_id_or_insert_and_return_id('suite', data, ['full_name'])
        self.assertNotEqual(returned_id_1, returned_id_2)

    def test_insert_or_ignore(self):
        data = {'fingerprint': '1234567890123456789012345678901234567890', 'status': 'PASS'}
        self.database.insert_or_ignore('keyword_tree', data, ['fingerprint'])
        self.database.insert_or_ignore('keyword_tree', data, ['fingerprint'])
        data = {'fingerprint': '0987654321098765432109876543210987654321', 'status': 'FAIL'}
        self.database.insert_or_ignore('keyword_tree', data, ['fingerprint'])
        row_count = self.database.fetch_one_value('keyword_tree', 'count(*)')
        self.assertEqual(row_count, 2)

    def test_update(self):
        data = {'fingerprint': '1234567890123456789012345678901234567890', 'status': 'PASS'}
        self.database.insert_or_ignore('keyword_tree', data, ['fingerprint'])
        self.database.update('keyword_tree', {'status': 'FAIL'},
                             {'fingerprint': '1234567890123456789012345678901234567890'})
        row_count = self.database.fetch_one_value('keyword_tree', 'count(*)')
        self.assertEqual(row_count, 1)
        updated = self.database.fetch_one_value('keyword_tree', 'status',
                                                {'fingerprint': '1234567890123456789012345678901234567890'})
        self.assertEqual(updated, 'FAIL')

    def test_insert(self):
        data = {'fingerprint': '1234567890123456789012345678901234567890', 'status': 'PASS'}
        self.database.insert('keyword_tree', data)
        with self.assertRaises(database.IntegrityError):
            self.database.insert('keyword_tree', data)
        data = {'fingerprint': '0987654321098765432109876543210987654321', 'status': 'FAIL'}
        self.database.insert('keyword_tree', data)
        row_count = self.database.fetch_one_value('keyword_tree', 'count(*)')
        self.assertEqual(row_count, 2)

    def test_applying_schema_updates(self):
        latest_update = self.database._latest_update_applied()
        self.assertTrue(latest_update < 10001)

        self.database._schema_updates = ((10001, True, 'testing/10001-minor_test_update1.sql'),)
        with self.assertRaises(database.ArchiverSchemaException):
            self.database.check_and_update_schema()
        self.assertTrue(latest_update < 10001)

        self.database.allow_minor_schema_updates = True
        self.database.check_and_update_schema()
        latest_update = self.database._latest_update_applied()
        self.assertEqual(latest_update, 10001)

        self.database._schema_updates = ((10001, True, 'testing/10001-minor_test_update1.sql'),
                                         (10002, True, 'testing/10002-minor_test_update2.sql'))
        self.database.check_and_update_schema()
        latest_update = self.database._latest_update_applied()
        self.assertEqual(latest_update, 10002)

        self.database._schema_updates = ((10001, True, 'testing/10001-minor_test_update1.sql'),
                                         (10002, True, 'testing/10002-minor_test_update2.sql'),
                                         (10003, False, 'testing/10003-major_test_update.sql'))
        with self.assertRaises(database.ArchiverSchemaException):
            self.database.check_and_update_schema()
        latest_update = self.database._latest_update_applied()
        self.assertEqual(latest_update, 10002)

        self.database.allow_major_schema_updates = True
        self.database.check_and_update_schema()
        latest_update = self.database._latest_update_applied()
        self.assertEqual(latest_update, 10003)

if __name__ == '__main__':
    unittest.main()

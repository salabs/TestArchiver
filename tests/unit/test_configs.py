
import argparse
import unittest
from datetime import date
from unittest import mock

from test_archiver import configs


# pylint: disable=protected-access


class TestHelperFunctions(unittest.TestCase):

    def test_parse_key_value_pairs(self):
        self.assertEqual(configs.parse_key_value_pairs(None), {})
        self.assertEqual(configs.parse_key_value_pairs([]), {})
        value_list = ['FOO:BAR', 'bar:1:2']
        expected = {'FOO': 'BAR', 'bar': '1:2'}
        self.assertEqual(configs.parse_key_value_pairs(value_list), expected)
        self.assertEqual(configs.parse_key_value_pairs({'a': 1, 'b': 2}), {'a': 1, 'b': 2})


FAKE_CONFIG_FILE_DATA = {'database': 'archive.db', 'user': 'worker_user', 'port': 1234,
                         'metadata': {'version': '1.2.3', 'environment': 'integration'}}

FAKE_CHANGES_FILE_DATA_1 = {
    "context": "Integration",
    "changes": [
        {
            "name": "/path/to/file.py",
            "repository": "RepoA",
            "item_type": "my_item_type",
            "subtype": "my_subtype"
        }
    ]
}

FAKE_CHANGES_FILE_DATA_2 = {
    "changes": [
        {
            "name": "/path/to/file.py",
            "repository": "RepoA",
            "item_type": "my_item_type",
            "subtype": "my_sub_item_type"
        }
    ]
}


class TestConfig(unittest.TestCase):

    def test_resolve_option(self):
        # pylint: disable=protected-access
        config = configs.Config()
        config._cli_args = argparse.Namespace()
        self.assertEqual(config.resolve_option('foo_option'), None)

        config._cli_args = argparse.Namespace()
        self.assertEqual(config.resolve_option('foo_option', default='bar'), 'bar')

        config._cli_args = argparse.Namespace(foo_option='100')
        self.assertEqual(config.resolve_option('foo_option', default=10, cast_as=int), 100)

        config._cli_args = argparse.Namespace(foo_option=100)
        self.assertEqual(config.resolve_option('foo_option', default=10, cast_as=int), 100)

        config._cli_args = argparse.Namespace(foo_option='foo')
        with self.assertRaises(ValueError):
            config.resolve_option('foo_option', cast_as=int)

        config._cli_args = argparse.Namespace(foo_option='full')
        self.assertEqual(config.resolve_option('foo_option', cast_as=configs._log_message_length), 0)

        config._cli_args = argparse.Namespace(foo_option='bar')
        with self.assertRaises(ValueError):
            config.resolve_option('foo_option', cast_as=configs._log_message_length)

    def test_default_configs_are_resolved(self):
        config = configs.Config()
        config.resolve()
        self.assertEqual(config.database, 'test_archive')
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.require_ssl, True)
        self.assertEqual(config.metadata, {})

    def test_file_configs_are_resolved(self):
        config = configs.Config()
        config.resolve(file_config=FAKE_CONFIG_FILE_DATA)
        self.assertEqual(config.database, 'archive.db')
        self.assertEqual(config.port, 1234)
        self.assertEqual(config.metadata, {'version': '1.2.3', 'environment': 'integration'})

    @mock.patch('test_archiver.configs.read_config_file', return_value=FAKE_CONFIG_FILE_DATA)
    def test_config_file_is_read(self, fake_read_config_file):
        config = configs.Config()
        config.resolve(file_config='foobar.json')
        fake_read_config_file.asser_called_once()

    def test_cli_configs_are_resolved(self):
        fake_cli_args = argparse.Namespace(user='cli_user', port=1234, metadata=['foo:bar'])
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.database, 'test_archive')
        self.assertEqual(config.user, 'cli_user')
        self.assertEqual(config.port, 1234)
        self.assertEqual(config.metadata, {'foo': 'bar'})

    def test_cli_configs_have_higher_precedence_than_config_files(self):
        fake_cli_args = argparse.Namespace(user='cli_user', port=4321,
                                           metadata=['version:3.2.1', 'cli_data:foobar'])
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args, file_config=FAKE_CONFIG_FILE_DATA)
        self.assertEqual(config.database, 'archive.db')
        self.assertEqual(config.user, 'cli_user')
        self.assertEqual(config.port, 4321)
        self.assertEqual(config.metadata, {'version': '3.2.1', 'cli_data': 'foobar',
                                           'environment': 'integration'})
        #'metadata': {'version': '1.2.3', 'environment': 'integration'}

    def test_allowing_major_schema_update_overrides_minor_updates(self):
        fake_cli_args = argparse.Namespace(allow_minor_schema_updates=True)
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.allow_minor_schema_updates, True)
        self.assertEqual(config.allow_major_schema_updates, False)

        fake_cli_args = argparse.Namespace(allow_major_schema_updates=True)
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.allow_minor_schema_updates, True)
        self.assertEqual(config.allow_major_schema_updates, True)

        fake_cli_args = argparse.Namespace(allow_major_schema_updates=True, allow_minor_schema_updates=False)
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.allow_minor_schema_updates, True)
        self.assertEqual(config.allow_major_schema_updates, True)

    def test_log_level_ignored(self):
        fake_cli_args = argparse.Namespace()
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertFalse(config.log_level_ignored('TRACE'))
        self.assertFalse(config.log_level_ignored('DEBUG'))
        self.assertFalse(config.log_level_ignored('INFO'))
        self.assertFalse(config.log_level_ignored('WARN'))
        self.assertFalse(config.log_level_ignored('ERROR'))
        self.assertFalse(config.log_level_ignored('FAIL'))
        self.assertFalse(config.log_level_ignored('OTHER_FOOBAR'))

        fake_cli_args = argparse.Namespace(ignore_logs_below='INFO')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertTrue(config.log_level_ignored('TRACE'))
        self.assertTrue(config.log_level_ignored('DEBUG'))
        self.assertFalse(config.log_level_ignored('INFO'))
        self.assertFalse(config.log_level_ignored('WARN'))
        self.assertFalse(config.log_level_ignored('ERROR'))
        self.assertFalse(config.log_level_ignored('FAIL'))
        self.assertFalse(config.log_level_ignored('OTHER_FOOBAR'))

        fake_cli_args = argparse.Namespace(ignore_logs_below='WARN')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertTrue(config.log_level_ignored('TRACE'))
        self.assertTrue(config.log_level_ignored('DEBUG'))
        self.assertTrue(config.log_level_ignored('INFO'))
        self.assertFalse(config.log_level_ignored('WARN'))
        self.assertFalse(config.log_level_ignored('ERROR'))
        self.assertFalse(config.log_level_ignored('FAIL'))
        self.assertFalse(config.log_level_ignored('OTHER_FOOBAR'))

    def test_max_log_message_length_is_handled_correctly(self):
        fake_cli_args = argparse.Namespace()
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.max_log_message_length, 2000)

        fake_cli_args = argparse.Namespace(max_log_message_length=None)
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.max_log_message_length, 2000)

        fake_cli_args = argparse.Namespace(max_log_message_length=0)
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.max_log_message_length, 0)

        fake_cli_args = argparse.Namespace(max_log_message_length='full')
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.max_log_message_length, 0)

        fake_cli_args = argparse.Namespace(max_log_message_length='bar')
        with self.assertRaises(ValueError):
            config.resolve(cli_args=fake_cli_args)

        fake_cli_args = argparse.Namespace(max_log_message_length=100)
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.max_log_message_length, 100)

        fake_cli_args = argparse.Namespace(max_log_message_length=-100)
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.max_log_message_length, -100)

class TestExecutionContext(unittest.TestCase):

    def test_execution_context(self):
        fake_cli_args = argparse.Namespace(execution_context='PR')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.execution_context, 'PR')

        fake_cli_args = argparse.Namespace()
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.execution_context, 'default')

    @mock.patch('test_archiver.configs.read_config_file', return_value=FAKE_CHANGES_FILE_DATA_1)
    def test_execution_context_and_changes(self, fake_changes_file_data):
        fake_cli_args = argparse.Namespace(execution_context='PR', changes='foobar.json')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.execution_context, 'PR')

        fake_cli_args = argparse.Namespace(changes='foobar.json')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.execution_context, 'Integration')

    @mock.patch('test_archiver.configs.read_config_file', return_value=FAKE_CHANGES_FILE_DATA_2)
    def test_execution_context_when_not_set_in_changes(self, fake_changes_file_data):
        fake_cli_args = argparse.Namespace(changes='foobar.json')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.execution_context, 'default')

    @mock.patch('test_archiver.configs.read_config_file', return_value=FAKE_CHANGES_FILE_DATA_1)
    def test_changes(self, fake_changes_file_data):
        fake_cli_args = argparse.Namespace(changes='foobar.json')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        changes = config.changes
        self.assertTrue(len(changes) == 1)
        self.assertEqual(changes[0]['name'], '/path/to/file.py')
        self.assertEqual(changes[0]['repository'], 'RepoA')
        self.assertEqual(changes[0]['item_type'], 'my_item_type')
        self.assertEqual(changes[0]['subtype'], 'my_subtype')

    @mock.patch('test_archiver.configs.read_config_file', return_value={})
    def test_changes_when_no_changes_in_file(self, fake_changes_file_data):
        fake_cli_args = argparse.Namespace(changes='foobar.json')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.changes, [])

    def test_changes_when_no_changes(self):
        fake_cli_args = argparse.Namespace()
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        self.assertEqual(config.changes, [])

    def test_execution_id(self):
        fake_cli_args = argparse.Namespace(execution_id='job_name_here')
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        assert config.execution_id == 'job_name_here', 'Execution-id should be correct'

        fake_cli_args = argparse.Namespace()
        config = configs.Config()
        config.resolve(cli_args=fake_cli_args)
        assert config.execution_id == 'Not set', 'Execution-id should be correct'


class TestHelperFunctions(unittest.TestCase):

    def test_parse_date(self):
        self.assertEqual(configs._parse_date("2024-01-01"), date(2024,1,1))
        with self.assertRaises(ValueError):
            configs._parse_date("foo")


if __name__ == '__main__':
    unittest.main()

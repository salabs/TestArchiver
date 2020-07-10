import unittest
import mock
import argparse

from configs import Config, parse_key_value_pairs


class TestHelperFunctions(unittest.TestCase):

    def test_parse_key_value_pairs(self):
        self.assertEqual(parse_key_value_pairs(None), {})
        self.assertEqual(parse_key_value_pairs([]), {})
        value_list = ['FOO:BAR', 'bar:1:2']
        expected = {'FOO': 'BAR', 'bar': '1:2'}
        self.assertEqual(parse_key_value_pairs(value_list), expected)
        self.assertEqual(parse_key_value_pairs({'a': 1, 'b': 2}), {'a': 1, 'b': 2})


FAKE_CONFIG_FILE_DATA = {'database': 'archive.db', 'user': 'worker_user', 'port': 1234,
                         'metadata': {'version': '1.2.3', 'environment': 'integration'}}

class TestConfig(unittest.TestCase):

    def test_default_configs_are_resolved(self):
        config = Config()
        self.assertEqual(config.database, 'test_archive')
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.require_ssl, True)
        self.assertEqual(config.metadata, {})

    def test_file_configs_are_resolved(self):
        config = Config(file_config=FAKE_CONFIG_FILE_DATA)
        self.assertEqual(config.database, 'archive.db')
        self.assertEqual(config.port, 1234)
        self.assertEqual(config.metadata, {'version': '1.2.3', 'environment': 'integration'})

    @mock.patch('configs.read_config_file', return_value=FAKE_CONFIG_FILE_DATA)
    def test_config_file_is_read(self, fake_read_config_file):
        Config(file_config='foobar.json')
        fake_read_config_file.asser_called_once()

    def test_cli_configs_are_resolved(self):
        fake_cli_args = argparse.Namespace(user='cli_user', port=1234, metadata=['foo:bar'])
        config = Config(cli_args=fake_cli_args)
        self.assertEqual(config.database, 'test_archive')
        self.assertEqual(config.user, 'cli_user')
        self.assertEqual(config.port, 1234)
        self.assertEqual(config.metadata, {'foo': 'bar'})

    def test_cli_configs_have_higher_precedence_than_config_files(self):
        fake_cli_args = argparse.Namespace(user='cli_user', port=4321,
                                           metadata=['version:3.2.1', 'cli_data:foobar'])
        config = Config(cli_args=fake_cli_args, file_config=FAKE_CONFIG_FILE_DATA)
        self.assertEqual(config.database, 'archive.db')
        self.assertEqual(config.user, 'cli_user')
        self.assertEqual(config.port, 4321)
        self.assertEqual(config.metadata, {'version': '3.2.1', 'cli_data': 'foobar',
                                           'environment': 'integration'})

    def test_allowing_major_schema_update_overrides_minor_updates(self):
        fake_cli_args = argparse.Namespace(allow_minor_schema_updates=True)
        config = Config(cli_args=fake_cli_args)
        self.assertEqual(config.allow_minor_schema_updates, True)
        self.assertEqual(config.allow_major_schema_updates, False)

        fake_cli_args = argparse.Namespace(allow_major_schema_updates=True)
        config = Config(cli_args=fake_cli_args)
        self.assertEqual(config.allow_minor_schema_updates, True)
        self.assertEqual(config.allow_major_schema_updates, True)

        fake_cli_args = argparse.Namespace(allow_major_schema_updates=True, allow_minor_schema_updates=False)
        config = Config(cli_args=fake_cli_args)
        self.assertEqual(config.allow_minor_schema_updates, True)
        self.assertEqual(config.allow_major_schema_updates, True)

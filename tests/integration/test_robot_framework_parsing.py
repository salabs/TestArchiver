
import unittest
import tempfile
from pathlib import Path

import robot

from test_archiver.output_parser import parse_xml
from test_archiver.configs import Config
from test_archiver.database import BaseDatabase, PostgresqlDatabase
from test_archiver.database import get_connection, get_connection_and_check_schema


class RobotFixtureTests(unittest.TestCase):

    def check_fixture_content(self, connection: BaseDatabase):
        self.assertEqual(connection.get_row_count('test_run'), 1)
        self.assertEqual(connection.get_row_count('test_case'), 74) # 63 tests - 2 duplicates = 61
        self.assertEqual(connection.get_row_count('test_result'), 74)

        self.assertEqual(connection.fetch_one_value('suite', 'name', where_data={'id': 1}),
                         'Tests')

        self.assertEqual(connection.fetch_one_value('suite', 'name', where_data={'id': 2}),
                         'Control Structures')
        self.assertEqual(
            connection.fetch_one_value('suite_result', 'fingerprint', where_data={'suite_id': 2}),
            '26f3bee0aa075611e3a2d52401b4cf11908551b5')

        self.assertEqual(connection.fetch_one_value('suite', 'name', where_data={'id': 14}),
                         'Top Suite')
        self.assertEqual(
            connection.fetch_one_value('suite_result', 'fingerprint', where_data={'suite_id': 14}),
            'ae39ac2af17cc96c78e16f2d77740fd196f3fe90')

    def fetch_full_fixture_fingerprint(self, connection: BaseDatabase) -> str:
        # First check that Full fixture suite is suite id 1
        self.assertEqual(connection.fetch_one_value('suite', 'name', where_data={'id': 1}), 'Tests')
        return connection.fetch_one_value('suite_result', 'fingerprint', where_data={'suite_id': 1})

    def normal_fixture_run(self):
        arguments = [
            "--console=none",
            "--pythonpath=robot_tests/libraries:robot_tests/resources",
            "--outputdir=robot_tests/normal",
            "--exclude=sleep",
            "--nostatusrc",
            "robot_tests/tests",
        ]
        robot.run_cli(arguments, exit=False)


class RobotFixtureArchivingPostgresTests(RobotFixtureTests):

    def setUp(self):
        self.connection: PostgresqlDatabase | None = None

    def tearDown(self):
        # pylint: disable=protected-access
        if self.connection:
            self.connection._connection.close()

    def _get_postgres_fixture_config(self):
        config = Config()
        config.resolve(file_config='fixture_config_postgres.json')
        return config

    def _clear_postgres_fixture_database(self):
        # pylint: disable=protected-access
        config = self._get_postgres_fixture_config()
        connection = None
        try:
            connection = get_connection_and_check_schema(config)
            connection._execute("DROP OWNED BY current_user;")
            connection._connection.commit()
        finally:
            if connection:
                connection._connection.close()

    def test_robot_fixture_with_listener(self):
        self._clear_postgres_fixture_database()
        arguments = [
            "--listener=test_archiver.ArchiverRobotListener:fixture_config_postgres.json",
            "--console=none",
            "--pythonpath=robot_tests/libraries:robot_tests/resources:src/",
            "--outputdir=robot_tests/listener",
            "--exclude=sleep",
            "--nostatusrc",
            "robot_tests/tests",
        ]
        robot.run_cli(arguments, exit=False)

        config = self._get_postgres_fixture_config()
        self.connection = get_connection_and_check_schema(config)
        self.check_fixture_content(self.connection)

    def test_parsing_robot_fixture(self):
        self.normal_fixture_run()
        self._clear_postgres_fixture_database()

        config = self._get_postgres_fixture_config()
        self.connection = get_connection_and_check_schema(config)
        parse_xml("robot_tests/normal/output.xml", 'robot', self.connection, config)
        self.check_fixture_content(self.connection)


class RobotFixtureArchivingSqliteTests(RobotFixtureTests):

    def test_robot_fixture_with_listener(self):
        config = Config()
        with tempfile.TemporaryDirectory() as temp_dir:
            arguments = [
                f"--listener=test_archiver.ArchiverRobotListener:{Path(temp_dir) / 'fixture.db'}:sqlite",
                "--console=none",
                "--pythonpath=robot_tests/libraries:robot_tests/resources:src/",
                "--outputdir=robot_tests/listener",
                "--exclude=sleep",
                "--nostatusrc",
                "robot_tests/tests",
            ]
            robot.run_cli(arguments, exit=False)

            config.resolve(file_config={"db_engine": "sqlite", "database": Path(temp_dir) / "fixture.db"})
            connection = get_connection(config)
            self.check_fixture_content(connection)

    def test_parsing_robot_fixture(self):
        self.normal_fixture_run()
        config = Config()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.resolve(file_config={"db_engine": "sqlite", "database": Path(temp_dir) / "fixture.db"})
            connection = get_connection_and_check_schema(config)
            parse_xml("robot_tests/normal/output.xml", 'robot', connection, config)
            self.check_fixture_content(connection)

    def test_listener_and_parser_create_same_fixture_fingerprint(self):
        listener_fingerprint = None
        parser_fingerprint = None
        config = Config()
        with tempfile.TemporaryDirectory() as temp_dir:
            arguments = [
                f"--listener=test_archiver.ArchiverRobotListener:{Path(temp_dir) / 'fixture.db'}:sqlite",
                "--console=none",
                "--pythonpath=robot_tests/libraries:robot_tests/resources:src/",
                "--outputdir=robot_tests/listener",
                "--exclude=sleep",
                "--exclude=listener_parser_mismatch",
                "--nostatusrc",
                "robot_tests/tests",
            ]
            robot.run_cli(arguments, exit=False)

            config.resolve(file_config={"db_engine": "sqlite", "database": Path(temp_dir) / "fixture.db"})
            connection = get_connection(config)
            listener_fingerprint = self.fetch_full_fixture_fingerprint(connection)

        config = Config()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.resolve(file_config={"db_engine": "sqlite", "database": Path(temp_dir) / "fixture.db"})
            connection = get_connection_and_check_schema(config)
            parse_xml("robot_tests/listener/output.xml", 'robot', connection, config)
            parser_fingerprint = self.fetch_full_fixture_fingerprint(connection)

        self.assertEqual(listener_fingerprint, parser_fingerprint)

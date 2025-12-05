
import unittest
import tempfile
from pathlib import Path

import robot

from test_archiver.output_parser import parse_xml
from test_archiver.configs import Config
from test_archiver.database import BaseDatabase, PostgresqlDatabase
from test_archiver.database import get_connection, get_connection_and_check_schema


EXPECTED_SUITE_FINGERPRINTS = (
    (28, "40f5672430d118af81cebe83ae19215bfa00c43b", "c5d127ec27b3e7cee7a1468cb7402ae9d5da43a8", "Variables"),
    (27, "626b7a1d92583433bb5aeeeeb06b768f8b688dea", "626b7a1d92583433bb5aeeeeb06b768f8b688dea", "Passing Suite2"),
    (26, "f605ea592cf7dd82cf416034b602262503453223", "f605ea592cf7dd82cf416034b602262503453223", "Passing Suite1"),
    (25, "c2a3400d50e0a52a8835b664ee3851d49b03082e", "c2a3400d50e0a52a8835b664ee3851d49b03082e", "Teardown Failure"),
    (24, "9fb1c4d300b79fa95199209f8d32a41d3802c3ad", "9fb1c4d300b79fa95199209f8d32a41d3802c3ad", "Skipping"),
    (23, "437154e64daa5673d1f1dfed7b197e5ec3324ebc", "437154e64daa5673d1f1dfed7b197e5ec3324ebc", "Passing tests"),
    (22, "3f9fe7b5b308fa539fcd944b245f5057438973bc", "3f9fe7b5b308fa539fcd944b245f5057438973bc", "Tagging"),
    (21, "964b22820abc48e24cd40c77376aabbc0e8a1a04", "964b22820abc48e24cd40c77376aabbc0e8a1a04", "Empty"),
    (20, "86cd41aec1024c33708f567df61bd98596612435", "86cd41aec1024c33708f567df61bd98596612435", "Embedded"),
    (19, "35a4859cbb96002f38f34910cf07e70a39fe2489", "35a4859cbb96002f38f34910cf07e70a39fe2489", "Documents"),
    (18, "89000e1ca6c885adad34ac26180b48751bc2191e", "89000e1ca6c885adad34ac26180b48751bc2191e", "Lower Suite"),
    (17, "6b7661113a2fe813ea92318813929019b1e0a3bb", "6b7661113a2fe813ea92318813929019b1e0a3bb", "Logging"),
    (16, "3ba443851e42cd88e8592eb7bf3860e16947dcb8", "3ba443851e42cd88e8592eb7bf3860e16947dcb8", "Failing tests"),
    (15, "0363aa40786bcbe4e2b5a047d6f95c393f75cebe", "0363aa40786bcbe4e2b5a047d6f95c393f75cebe", "Data-Driven"),
    (14, "ae39ac2af17cc96c78e16f2d77740fd196f3fe90", "ae39ac2af17cc96c78e16f2d77740fd196f3fe90", "Top Suite"),
    # (13, "8cc2febd046cba652abd871d359d667f09919f6a", "Random Pass"),
    # (12, "cfe075f0ea543b599d50d9f343cb777d0a110327", "Flaky"),
    # (11, "98da3249f2df4e6ac55292741b0976108dbe070c", "Bigrandom"),
    # (10, "df8c6f0cbe9b443cf5204ffdc148dd25484f7f9c", "Randomized Suite"),
     (9, "17c89565ddf7e7933f6520cfb2db67fb71a1b2b9", "485965eadb7125a53463303cda316042414988fe", "Errors"),
     (8, "e53f0c275eb32ade2f7d49fd50e0fde642f95ad2", "e53f0c275eb32ade2f7d49fd50e0fde642f95ad2", "While Loops"),
     (7, "a977de5415ac04b2b25642c6f2d7e2ee5aac0514", "a977de5415ac04b2b25642c6f2d7e2ee5aac0514", "Try Except"),
     (6, "ab1272aaec0bc45693def5fca31932a50925ded0", "ab1272aaec0bc45693def5fca31932a50925ded0", "Other Control Structures"),
     (5, "0cf39c21908fcfd2ea69038dbacba78619abfd54", "0cf39c21908fcfd2ea69038dbacba78619abfd54", "If Else"),
     (4, "582a72f2fa8a798466f82f820c3a9c2209795e1a", "582a72f2fa8a798466f82f820c3a9c2209795e1a", "Grouped Templates"),
     (3, "a642b51f46ca3f3169b431db8208e3af183648f4", "a642b51f46ca3f3169b431db8208e3af183648f4", "For Loops"),
     (2, "5a6a1de73088bce20ee3bf7da48c4cf620801888", "5a6a1de73088bce20ee3bf7da48c4cf620801888", "Control Structures"),
     #(1, "001ad0634fab318d8823fa722535b447e2c641b8", "Tests"),
)

class RobotFixtureTests(unittest.TestCase):


    def check_fixture_suite_fingerprints(self, connection: BaseDatabase, using_listener: bool):
        for suite_id, listener_fingerprint, parser_fingerprint, name in EXPECTED_SUITE_FINGERPRINTS:
            self.assertEqual(connection.fetch_one_value('suite', 'name', where_data={'id': suite_id}), name)
            fingerprint = listener_fingerprint if using_listener else parser_fingerprint
            self.assertEqual(
                connection.fetch_one_value('suite_result', 'fingerprint', where_data={'suite_id': suite_id}),
                fingerprint, f"Suite '{name}' has an unexpected fingerprint")

    def check_fixture_content(self, connection: BaseDatabase, using_listener: bool):
        self.assertEqual(connection.get_row_count('test_run'), 1)
        self.assertEqual(connection.get_row_count('test_case'), 75)
        self.assertEqual(connection.get_row_count('test_result'), 75)
        self.check_fixture_suite_fingerprints(connection, using_listener)

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
        self.check_fixture_content(self.connection, using_listener=True)

    def test_parsing_robot_fixture(self):
        self.normal_fixture_run()
        self._clear_postgres_fixture_database()

        config = self._get_postgres_fixture_config()
        self.connection = get_connection_and_check_schema(config)
        parse_xml("robot_tests/normal/output.xml", 'robot', self.connection, config)
        self.check_fixture_content(self.connection, using_listener=False)


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
            self.check_fixture_content(connection, using_listener=True)

    def test_parsing_robot_fixture(self):
        self.normal_fixture_run()
        config = Config()
        with tempfile.TemporaryDirectory() as temp_dir:
            config.resolve(file_config={"db_engine": "sqlite", "database": Path(temp_dir) / "fixture.db"})
            connection = get_connection_and_check_schema(config)
            parse_xml("robot_tests/normal/output.xml", 'robot', connection, config)
            self.check_fixture_content(connection, using_listener=False)

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

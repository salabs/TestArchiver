# pylint: disable=E1101

import os
import sqlite3
from pathlib import Path

try:
    import psycopg2
except ImportError:
    psycopg2 = None

from . import version, configs


SCHEMA_UPDATES = (
    #(update_id, minor, file)
    (1, False, '0001-schema_update_table_and_log_message_index.sql'),
    (2, True, '0002-execution_paths.sql'),
    # Updates are appended to the end
)


def get_connection_and_check_schema(config):
    connection = None
    if config.db_engine in ('postgresql', 'postgres'):
        connection = PostgresqlDatabase(config)
    elif config.db_engine in ('sqlite', 'sqlite3'):
        if config.host or config.user:
            raise Exception("--host or --user options should not be used "
                            "with default sqlite3 database engine")
        connection = SQLiteDatabase(config)
    if connection:
        connection.check_and_update_schema()
        return connection
    raise Exception("Unsupported database type '{}'".format(config.db_engine))


class IntegrityError(Exception):
    """Exception for uniformly communicating a database integrity error"""

class ArchiverSchemaException(Exception):
    """Exception for communicating a mismatch with database schema and TestArchiver version"""


class BaseDatabase:

    UndefinedTableError = None

    def __init__(self, config):
        self._schema_updates = SCHEMA_UPDATES
        self.database = config.database
        self.host = config.host
        self.port = config.port
        self.user = config.user
        self.password = config.password
        self.require_ssl = config.require_ssl
        self.allow_minor_schema_updates = config.allow_minor_schema_updates
        self.allow_major_schema_updates = config.allow_major_schema_updates
        self._connection = None
        self._connect()

    def current_schema_version(self):
        return self._schema_updates[-1][0]

    def _db_engine_identifier(self):
        raise NotImplementedError()

    def _connect(self):
        raise NotImplementedError()

    def commit(self):
        self._connection.commit()

    def _initialize_schema(self):
        raise NotImplementedError()

    def _run_script(self, script_file):
        raise NotImplementedError()

    def check_and_update_schema(self):
        latest_update_applied = self._latest_update_applied()
        if latest_update_applied is None:
            if self._initialize_schema():
                print('Test archive schema initialized')
                return
            latest_update_applied = 0
        if latest_update_applied < self._schema_updates[-1][0]:
            for update_id, is_minor, file in self._schema_updates:
                if update_id > latest_update_applied:
                    base_dir = Path(os.path.dirname(__file__))
                    script_file = base_dir / 'schemas/migrations' / self._db_engine_identifier() / file
                    if self.allow_major_schema_updates or (is_minor and self.allow_minor_schema_updates):
                        print('Running schema update {} from: {}'.format(update_id, script_file))
                        self._run_script(script_file)
                    elif is_minor:
                        raise ArchiverSchemaException('ERROR: pending minor schema update is needed.'
                                                      'Run with --allow-minor-schema-updates option to '
                                                      'update the schema to match the archiver version.')
                    else:
                        raise ArchiverSchemaException('ERROR: pending major schema update is needed.'
                                                      'Run with --allow-major-schema-updates option to '
                                                      'update the schema to match the archiver version.')

        elif latest_update_applied > self._schema_updates[-1][0]:
            # The schema is newer than the Archiver
            minimum_version = self.fetch_one_value('schema_updates', 'applied_by',
                                                   {'update_id': latest_update_applied})
            raise ArchiverSchemaException("ERROR: The version of TestArchiver is older than the schema. "
                                          "Please update to version '{}' or higher".format(minimum_version))

    def _latest_update_applied(self):
        try:
            return self.max_value('schema_updates', 'schema_version')
        except self.UndefinedTableError:
            self._connection.rollback()
        return None

    def _execute(self, sql, values=None):
        if values is None:
            values = []
        values = self._handle_values(values)
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, values)
        finally:
            cursor.close()

    def _execute_and_fetchone(self, sql, values=None):
        if values is None:
            values = []
        values = self._handle_values(values)
        cursor = self._connection.cursor()
        row = None
        try:
            cursor.execute(sql, values)
            row = cursor.fetchone()
        finally:
            cursor.close()
        return row

    def _handle_values(self, values):
        raise NotImplementedError()

    def _fetch_id(self, table, data, key_fields):
        raise NotImplementedError()

    def return_id_or_insert_and_return_id(self, table, data, key_fields):
        raise NotImplementedError()

    def insert_and_return_id(self, table, data, key_fields=None):
        raise NotImplementedError()

    def insert_or_ignore(self, table, data, key_fields=None):
        raise NotImplementedError()

    def update(self, table, data, key_data):
        raise NotImplementedError()

    def insert(self, table, data):
        raise NotImplementedError()

    def max_value(self, table, column, where_data=None):
        raise NotImplementedError()

    def fetch_one_value(self, table, column, where_data=None):
        raise NotImplementedError()


class PostgresqlDatabase(BaseDatabase):

    UndefinedTableError = psycopg2.errors.UndefinedTable if psycopg2 else None

    def _db_engine_identifier(self):
        return 'postgres'

    def _connect(self):
        if not psycopg2:
            raise Exception("ERROR: Trying to use Postgresql database but psycopg2 is not installed! "
                            "Try for example: 'pip install psycopg2-binary'")

        self._connection = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            sslmode='require' if self.require_ssl else 'prefer',
        )

    def _initialize_schema(self):
        try:
            self._execute("SELECT 'test_run'::regclass;")
        except psycopg2.ProgrammingError:
            self._connection.rollback()
            schema_file = os.path.join(os.path.dirname(__file__), 'schemas/schema_postgres.sql')
            self._run_script(schema_file)
            return True
        return False

    def _run_script(self, script_file):
        with open(script_file) as file:
            self._execute(file.read().format(applied_by=version.ARCHIVER_VERSION))
            self.commit()

    def _handle_values(self, values):
        return values

    def _fetch_id(self, table, data, key_fields):
        sql = "SELECT id FROM {table} WHERE {key_placeholders}"
        sql = sql.format(
            table=table,
            key_placeholders=' AND '.join(['{}=%s'.format(key) for key in key_fields])
            )
        row = self._execute_and_fetchone(sql, [data[key] for key in key_fields])
        if row:
            return row[0]
        return None

    def return_id_or_insert_and_return_id(self, table, data, key_fields):
        row_id = self._fetch_id(table, data, key_fields)
        if not row_id:
            sql = ("INSERT INTO {table}({fields}) VALUES ({value_placeholders}) "
                   "{conflict_statement} RETURNING id;")
            keys = list(data)
            on_conflict = ' ON CONFLICT ({}) DO NOTHING '.format(','.join(key_fields)) if key_fields else ''
            sql = sql.format(
                table=table,
                fields=','.join(keys),
                value_placeholders=','.join(['%s' for _ in keys]),
                conflict_statement=on_conflict,
                )
            row = self._execute_and_fetchone(sql, [data[key] for key in keys])
            (row_id, ) = row
        return row_id

    def insert_and_return_id(self, table, data, key_fields=None):
        sql = "INSERT INTO {table}({fields}) VALUES ({value_placeholders}) {conflict_statement} RETURNING id;"
        keys = list(data)
        on_conflict = ' ON CONFLICT ({}) DO NOTHING '.format(','.join(key_fields)) if key_fields else ''
        sql = sql.format(
            table=table,
            fields=','.join(keys),
            value_placeholders=','.join(['%s' for _ in keys]),
            conflict_statement=on_conflict,
            )
        row = self._execute_and_fetchone(sql, [data[key] for key in keys])
        if row:
            (row_id, ) = row
        else:
            row_id = self._fetch_id(table, data, key_fields)
        return row_id

    def insert_or_ignore(self, table, data, key_fields=None):
        sql = "INSERT INTO {table}({fields}) VALUES ({value_placeholders}) {conflict_statement};"
        keys = list(data)
        on_conflict = ' ON CONFLICT ({}) DO NOTHING '.format(','.join(key_fields)) if key_fields else ''
        sql = sql.format(
            table=table,
            fields=','.join(keys),
            value_placeholders=','.join(['%s' for _ in keys]),
            conflict_statement=on_conflict,
            )
        self._execute(sql, [data[key] for key in keys])

    def update(self, table, data, key_data):
        sql = "UPDATE {table} SET {updates} WHERE {key_fields};"
        keys = list(data)
        updates = ','.join(['{}=%s'.format(field) for field in data])
        key_fields = ' AND '.join(['{}=%s'.format(field) for field in key_data])
        sql = sql.format(
            table=table,
            updates=updates,
            key_fields=key_fields,
            )
        values = [data[key] for key in keys]
        values.extend([key_data[key] for key in key_data])
        self._execute(sql, values)

    def insert(self, table, data):
        sql = "INSERT INTO {table}({fields}) VALUES ({value_placeholders});"
        keys = list(data)
        sql = sql.format(
            table=table,
            fields=','.join(keys),
            value_placeholders=','.join(['%s' for _ in keys]),
            )
        try:
            self._execute(sql, [data[key] for key in keys])
        except (psycopg2.errors.UniqueViolation, psycopg2.errors.NotNullViolation):
            raise IntegrityError()


    def max_value(self, table, column, where_data=None):
        where_data = where_data or {}
        where_filters = ' AND '.join(['{}=%s'.format(col) for col in where_data])
        sql = "SELECT max({column}) FROM {table} {where};"
        sql = sql.format(
            table=table,
            column=column,
            where='WHERE {}'.format(where_filters) if where_data else '',
            )
        (value, ) = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        return value

    def fetch_one_value(self, table, column, where_data=None):
        where_data = where_data or {}
        sql = "SELECT {column} FROM {table} {where};"
        sql = sql.format(
            table=table,
            column=column,
            where='WHERE ' + ' AND '.join(['{}=%s'.format(col) for col in where_data]) if where_data else '',
            )
        row = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        if row:
            (value, ) = row
            return value
        return None


class SQLiteDatabase(BaseDatabase):

    UndefinedTableError = sqlite3.OperationalError

    def _db_engine_identifier(self):
        return 'sqlite'

    def _connect(self):
        self._connection = sqlite3.connect(self.database)

    def _initialize_schema(self):
        query = "SELECT 1 FROM sqlite_master WHERE type='table' AND name='test_run';"
        if not self._execute_and_fetchone(query):
            schema_file = os.path.join(os.path.dirname(__file__), 'schemas/schema_sqlite.sql')
            self._run_script(schema_file)
            return True
        return False

    def _run_script(self, script_file):
        with open(script_file) as file:
            self._connection.executescript(file.read().format(applied_by=version.ARCHIVER_VERSION))
            self.commit()

    def _handle_values(self, values):
        handled_values = []
        for value in values:
            if isinstance(value, list):
                handled_values.append(str(value))
            else:
                handled_values.append(value)
        return handled_values

    def _fetch_id(self, table, data, key_fields):
        row_id = None
        if not key_fields:
            sql = "SELECT last_insert_rowid()"
            (row_id, ) = self._execute_and_fetchone(sql)
        else:
            sql = "SELECT id FROM {table} WHERE {key_placeholders}"
            sql = sql.format(
                table=table,
                key_placeholders=' AND '.join(['{}=?'.format(key) for key in key_fields])
                )
            row = self._execute_and_fetchone(sql, [data[key] for key in key_fields])
            if row:
                row_id = row[0]
        return row_id

    def return_id_or_insert_and_return_id(self, table, data, key_fields):
        self.insert_or_ignore(table, data)
        return self._fetch_id(table, data, key_fields)

    def insert_and_return_id(self, table, data, key_fields=None):
        self.insert(table, data)
        return self._fetch_id(table, data, key_fields)

    def insert_or_ignore(self, table, data, key_fields=None):
        sql = "INSERT OR IGNORE INTO {table}({fields}) VALUES ({value_placeholders});"
        keys = list(data)
        sql = sql.format(
            table=table,
            fields=','.join(keys),
            value_placeholders=','.join(['?' for _ in keys]),
            )
        self._execute(sql, [data[key] for key in keys])

    def update(self, table, data, key_data):
        sql = "UPDATE {table} SET {updates} WHERE {key_fields};"
        keys = list(data)
        updates = ','.join(['{}=?'.format(field) for field in data])
        key_fields = ' AND '.join(['{}=?'.format(field) for field in key_data])
        sql = sql.format(
            table=table,
            updates=updates,
            key_fields=key_fields,
            )
        values = [data[key] for key in keys]
        values.extend([key_data[key] for key in key_data])
        self._execute(sql, values)

    def insert(self, table, data):
        sql = "INSERT INTO {table}({fields}) VALUES ({value_placeholders});"
        keys = list(data)
        sql = sql.format(
            table=table,
            fields=','.join(keys),
            value_placeholders=','.join(['?' for _ in keys]),
            )
        try:
            self._execute(sql, [data[key] for key in keys])
        except sqlite3.IntegrityError:
            raise IntegrityError()


    def max_value(self, table, column, where_data=None):
        where_data = where_data or {}
        where_filters = ' AND '.join(['{}=?'.format(col) for col in where_data])
        sql = "SELECT max({column}) FROM {table} {where};"
        sql = sql.format(
            table=table,
            column=column,
            where='WHERE {}'.format(where_filters) if where_data else '',
            )
        (value, ) = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        return value

    def fetch_one_value(self, table, column, where_data=None):
        where_data = where_data or {}
        sql = "SELECT {column} FROM {table} {where};"
        sql = sql.format(
            table=table,
            column=column,
            where='WHERE ' + ' AND '.join(['{}=?'.format(col) for col in where_data]) if where_data else '',
            )
        row = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        if row:
            (value, ) = row
            return value
        return None


def argument_parser():
    parser = configs.base_argument_parser('Initialize and update test archive schema.')
    return parser

def main():
    config, _ = configs.configuration(argument_parser)

    get_connection_and_check_schema(config)


if __name__ == '__main__':
    main()

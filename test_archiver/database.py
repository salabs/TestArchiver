import os
import sys

import sqlite3

try:
    import psycopg2
except ImportError:
    psycopg2 = None

class IntegrityError(Exception):
    """Exception for uniformly communicating a database integrity error"""


class Database:

    SCHEMA_UPDATES = None

    def __init__(self, db_name, db_host=None, db_port=None, db_user=None, db_password=None, require_ssl=True):
        self.database = db_name
        self.host = db_host
        self.port = db_port
        self.user = db_user
        self.password = db_password
        self.require_ssl = require_ssl
        self._connection = None
        self._connect()
        self._update_schema()

    def _connect(self):
        raise NotImplementedError()

    def _update_schema(self):
        updates_needed = []
        for check, update in self.SCHEMA_UPDATES:
            if self._execute_and_fetchone(check):
                break
            updates_needed.append(update)
        else:
            if self._initialize_schema():
                # No need for updates as current schema was initialized
                return

        for update in reversed(updates_needed):
            self._execute(update)

    def _initialize_schema(self):
        raise NotImplementedError()

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

    def max_value(self, table, column, where_data):
        raise NotImplementedError()

    def fetch_one_value(self, table, column, where_data):
        raise NotImplementedError()


class PostgresqlDatabase(Database):

    # pairs of queries (check, update)
    # Newest updates on top
    SCHEMA_UPDATES = [
        ("SELECT true FROM pg_class WHERE pg_class.relname = 'log_message_index';",
         "CREATE INDEX log_message_index ON log_message(test_run_id, suite_id, test_id);"),
    ]

    def _connect(self):
        if not psycopg2:
            print('ERROR: Trying to use Postgresql database but psycopg2 is not installed!')
            print("ERROR: For example: 'pip install psycopg2-binary'")
            sys.exit(1)

        self._connection = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            sslmode='require' if self.require_ssl else 'prefer',
        )

    def _initialize_schema(self):
        try:
            self._execute("SELECT 'keyword_statistics'::regclass;")
        except psycopg2.ProgrammingError:
            self._connection.rollback()
            schema_file = os.path.join(os.path.dirname(__file__), 'schemas/schema_postgres.sql')
            with open(schema_file) as schema:
                self._execute(schema.read())
            return True
        return False

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
        except psycopg2.errors.UniqueViolation:
            raise IntegrityError()


    def max_value(self, table, column, where_data):
        sql = "SELECT max({column}) FROM {table} WHERE {where};"
        sql = sql.format(
            table=table,
            column=column,
            where=' AND '.join(['{}=%s'.format(col) for col in where_data]),
            )
        (value, ) = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        return value

    def fetch_one_value(self, table, column, where_data):
        sql = "SELECT {column} FROM {table} WHERE {where};"
        sql = sql.format(
            table=table,
            column=column,
            where=' AND '.join(['{}=%s'.format(col) for col in where_data]),
            )
        row = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        if row:
            (value, ) = row
            return value
        return None


class SQLiteDatabase(Database):

    # pairs of queries (check, update)
    # Newest updates on top
    SCHEMA_UPDATES = [
        ("SELECT true FROM sqlite_master WHERE name = 'log_message_index';",
         "CREATE INDEX log_message_index ON log_message(test_run_id, suite_id, test_id);"),
    ]

    def __init__(self, db_name):
        super(SQLiteDatabase, self).__init__(db_name)

    def _connect(self):
        self._connection = sqlite3.connect(self.database)

    def _initialize_schema(self):
        query = "SELECT 1 FROM sqlite_master WHERE type='table' AND name='keyword_statistics';"
        if not self._execute_and_fetchone(query):
            schema_file = os.path.join(os.path.dirname(__file__), 'schemas/schema_sqlite.sql')
            with open(schema_file) as schema:
                self._connection.executescript(schema.read())
            return True
        return False

    def _handle_values(self, values):
        handled_values = []
        for value in values:
            if type(value) == list:
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
        sql = "INSERT OR IGNORE INTO {table}({fields}) VALUES ({value_placeholders});"
        keys = list(data)
        sql = sql.format(
            table=table,
            fields=','.join(keys),
            value_placeholders=','.join(['?' for _ in keys]),
            )
        self._execute(sql, [data[key] for key in keys])
        return self._fetch_id(table, data, key_fields)

    def insert_and_return_id(self, table, data, key_fields=None):
        sql = "INSERT OR IGNORE INTO {table}({fields}) VALUES ({value_placeholders});"
        keys = list(data)
        sql = sql.format(
            table=table,
            fields=','.join(keys),
            value_placeholders=','.join(['?' for _ in keys]),
            )
        self._execute(sql, [data[key] for key in keys])
        row_id = self._fetch_id(table, data, key_fields)
        return row_id

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


    def max_value(self, table, column, where_data):
        sql = "SELECT max({column}) FROM {table} WHERE {where};"
        sql = sql.format(
            table=table,
            column=column,
            where=' AND '.join(['{}=?'.format(col) for col in where_data]),
            )
        (value, ) = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        return value

    def fetch_one_value(self, table, column, where_data):
        sql = "SELECT max({column}) FROM {table} WHERE {where};"
        sql = sql.format(
            table=table,
            column=column,
            where=' AND '.join(['{}=?'.format(col) for col in where_data]),
            )
        row = self._execute_and_fetchone(sql, [where_data[key] for key in where_data])
        if row:
            (value, ) = row
            return value
        return None

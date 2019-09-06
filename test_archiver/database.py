import os


class Database:
    def __init__(self, db_name, db_host, db_port, db_user, db_password):
        self.database = db_name
        self.host = db_host
        self.port = db_port
        self.user = db_user
        self.password = db_password
        self._connection = None
        self._connect()

    def _connect(self):
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

    def fetch_one_value(self):
        raise NotImplementedError()


class PostgresqlDatabase(Database):

    def _connect(self):
        import psycopg2
        self._connection = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
            sslmode='require',
        )
        try:
            self._execute('SELECT 1 FROM keyword_statistics;')
        except psycopg2.ProgrammingError:
            self._connection.rollback()
            schema_file = os.path.join(os.path.dirname(__file__), 'schemas/schema_postgres.sql')
            with open(schema_file) as schema:
                self._execute(schema.read())

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
        else:
            return None

    def return_id_or_insert_and_return_id(self, table, data, key_fields):
        row_id = self._fetch_id(table, data, key_fields)
        if not row_id:
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
        self._execute(sql, [data[key] for key in keys])

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
        else:
            return None


class SQLiteDatabase(Database):

    def __init__(self, db_name):
        super(SQLiteDatabase, self).__init__(db_name, None, None, None, None)

    def _connect(self):
        import sqlite3
        self._connection = sqlite3.connect(self.database)
        try:
            self._execute('SELECT 1 FROM keyword_statistics;')
        except sqlite3.OperationalError:
            schema_file = os.path.join(os.path.dirname(__file__), 'schemas/schema_sqlite.sql')
            with open(schema_file) as schema:
                self._connection.executescript(schema.read())

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
        self._execute(sql, [data[key] for key in keys])

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
        else:
            return None

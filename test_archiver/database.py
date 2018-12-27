import psycopg2 as db_api

class Database(object):
    def __init__(self, db_name, db_host, db_port, db_user, db_password):
        self._connection = None
        self.database = db_name
        self.host = db_host
        self.port = db_port
        self.user = db_user
        self.password = db_password
        self._connect()

    def _connect(self):
        self._connection = db_api.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
            )

    def _fetch_id(self, table, data, key_fields):
        sql = "SELECT id FROM {table} WHERE {key_placeholders}"
        sql = sql.format(
                table=table,
                key_placeholders=' AND '.join(['{}=%s'.format(key) for key in key_fields])
            )
        row_id = None
        with self._connection.cursor() as cursor:
            cursor.execute(sql, [data[key] for key in key_fields])
            (row_id, ) = cursor.fetchone()
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
        row = None
        with self._connection.cursor() as cursor:
            cursor.execute(sql, [data[key] for key in keys])
            row = cursor.fetchone()
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
        with self._connection.cursor() as cursor:
            cursor.execute(sql, [data[key] for key in keys])


    def update(self, table, data, key_data):
        sql = "UPDATE {table} SET {updates} WHERE {key_fields};"
        keys = list(data)
        updates = ','.join(['{}=%s'.format(field) for field in data])
        key_fields = ','.join(['{}=%s'.format(field) for field in key_data])
        sql = sql.format(
                table=table,
                updates=updates,
                key_fields=key_fields,
            )
        values = [data[key] for key in keys]
        values.extend([key_data[key] for key in key_data])
        with self._connection.cursor() as cursor:
            cursor.execute(sql, values)

    def insert(self, table, data):
        sql = "INSERT INTO {table}({fields}) VALUES ({value_placeholders});"
        keys = list(data)
        sql = sql.format(
                table=table,
                fields=','.join(keys),
                value_placeholders=','.join(['%s' for _ in keys]),
            )
        with self._connection.cursor() as cursor:
            cursor.execute(sql, [data[key] for key in keys])

import json


def read_config_file(file_name):
    with open(file_name, 'r') as config_file:
        return json.load(config_file)

def parse_key_value_pairs(values):
    pairs = {}
    for item in values or []:
        try:
            name, value = item.split(':', 1)
            pairs[name] = value
        except Exception:
            raise Exception("Unsupported format for key-value pair: '{}' use NAME:VALUE".format(item))
    return pairs


class Config():

    def __init__(self, cli_args=None, file_config=None):
        self._cli_args = cli_args
        if isinstance(file_config, str):
            self._file_config = read_config_file(file_config)
        else:
            self._file_config = file_config or {}

        self.database = self.resolve_option('database', default='test_archive')
        self.user = self.resolve_option('user')
        self.password = self.resolve_option('password')
        self.host = self.resolve_option('host')
        self.port = self.resolve_option('port', default=5432, cast_as=int)
        self.db_engine = self.resolve_option('db_engine', default='sqlite')
        self.require_ssl = self.resolve_option('require_ssl', default=True, cast_as=bool)

        self.team = self.resolve_option('team')
        self.repository = self.resolve_option('repository', default='default repo')
        self.series = self.resolve_list_option('series')
        self.metadata = self.resolve_list_option('metadata', parse_key_value_pairs)

        self.change_engine_url = self.resolve_option('change_engine_url')


    def resolve_option(self, name, default=None, cast_as=str):
        value = None
        if self._cli_args and name in self._cli_args and self._cli_args.__getattribute__(name) is not None:
            value = self._cli_args.__getattribute__(name)
        else:
            value = self._file_config.get(name, default)
        if value is None:
            value = default
        try:
            return value if value is None else cast_as(value)
        except ValueError as value_error:
            print("Error: incompatiple value for option '{}'".format(name))
            raise value_error

    def resolve_list_option(self, name, value_handler=None):
        values = self._file_config.get(name, [])
        if self._cli_args and name in self._cli_args and self._cli_args.__getattribute__(name) is not None:
            values.extend(self._cli_args.__getattribute__(name))
        if value_handler:
            return value_handler(values)
        return values

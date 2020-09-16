import argparse
import json
import sys
from collections import defaultdict

from . import version

def read_config_file(file_name):
    with open(file_name, 'r') as config_file:
        return json.load(config_file)

def parse_key_value_pairs(values):
    if isinstance(values, dict):
        return values.copy()
    pairs = {}
    for item in values or []:
        try:
            name, value = item.split(':', 1)
            pairs[name] = value
        except Exception:
            raise Exception("Unsupported format for key-value pair: '{}' use NAME:VALUE".format(item))
    return pairs


LOG_LEVEL_MAP = defaultdict(lambda: 100)
LOG_LEVEL_MAP[None] = 0
LOG_LEVEL_MAP["TRACE"] = 1
LOG_LEVEL_MAP["DEBUG"] = 10
LOG_LEVEL_MAP["INFO"] = 20
LOG_LEVEL_MAP["WARN"] = 30
LOG_LEVEL_MAP["ERROR"] = 40
LOG_LEVEL_MAP["FAIL"] = 50

LOG_LEVEL_CUT_OFF_OPTIONS = ('TRACE', 'DEBUG', 'INFO', 'WARN')


class Config():

    def __init__(self, cli_args=None, file_config=None):
        self._cli_args = cli_args
        if isinstance(file_config, str):
            self._file_config = read_config_file(file_config)
        else:
            self._file_config = file_config or {}

        self._resolve_options()

    def _resolve_options(self):
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
        self.metadata = self.resolve_map_option('metadata')

        self.allow_major_schema_updates = self.resolve_option('allow_major_schema_updates',
                                                              default=False, cast_as=bool)
        self.allow_minor_schema_updates = self.resolve_option('allow_minor_schema_updates',
                                                              default=False, cast_as=bool)
        # If major updates are allowed then minor ones are as well
        self.allow_minor_schema_updates = self.allow_major_schema_updates or self.allow_minor_schema_updates

        self.archive_keywords = self.resolve_option('archive_keywords', default=True, cast_as=bool)
        self.archive_keyword_statistics = self.resolve_option('archive_keyword_statistics', default=True,
                                                              cast_as=bool)

        self.ignore_logs = self.resolve_option('ignore_logs', default=False, cast_as=bool)
        self.ignore_logs_below = self.resolve_option('ignore_logs_below', default=None)

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

    def resolve_list_option(self, name):
        values = self._file_config.get(name, [])
        if self._cli_args and name in self._cli_args and self._cli_args.__getattribute__(name) is not None:
            values.extend(self._cli_args.__getattribute__(name))
        return values

    def resolve_map_option(self, name):
        values = parse_key_value_pairs(self._file_config.get(name, []))
        if self._cli_args and name in self._cli_args and self._cli_args.__getattribute__(name) is not None:
            values.update(parse_key_value_pairs(self._cli_args.__getattribute__(name)))
        return values

    def log_level_ignored(self, log_level):
        return LOG_LEVEL_MAP[log_level] < LOG_LEVEL_MAP[self.ignore_logs_below]

def base_argument_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--version', '-v', action='version',
                        version='%(prog)s {}'.format(version.ARCHIVER_VERSION))
    parser.add_argument('--config', dest='config_file',
                        help='path to JSON config file containing database credentials')

    parser.add_argument('--dbengine', dest='db_engine',
                        help='Database engine, postgresql or sqlite (default)')
    parser.add_argument('--database', help='database name')
    parser.add_argument('--host', help='database host name', default=None)
    parser.add_argument('--user', help='database user')
    parser.add_argument('--pw', '--password', dest='password', help='database password')
    parser.add_argument('--port', help='database port (default: 5432)')
    parser.add_argument('--dont-require-ssl', dest='require_ssl', action='store_false', default=None,
                        help='Disable the default behavior to require ssl from the target database.')
    parser.add_argument('--allow-minor-schema-updates', action='store_true', default=None,
                        help=('Allow TestArchiver to perform MINOR (backwards compatible) schema '
                              'updates the test archive'))
    parser.add_argument('--allow-major-schema-updates', action='store_true', default=None,
                        help=('Allow TestArchiver to perform MAJOR (backwards incompatible) schema '
                              'updates the test archive'))
    parser.add_argument('--no-keywords', dest='archive_keywords', action='store_false',
                        default=None, help='Do not archive keyword data')
    parser.add_argument('--no-keyword-stats', dest='archive_keyword_statistics', action='store_false',
                        default=None, help='Do not archive keyword statistics')
    parser.add_argument('--ignore-logs-below', default=None, choices=LOG_LEVEL_CUT_OFF_OPTIONS,
                        help=('Sets a cut off level for archived log messages. '
                              'By default archives all available log messages.'))
    parser.add_argument('--ignore-logs', action='store_true', help='Do not archive any log messages')
    return parser

def configuration(argument_parser):
    if sys.version_info[0] < 3:
        sys.exit('Unsupported Python version (' + str(sys.version_info.major) + '). Please use version 3.')

    args = argument_parser().parse_args()
    return Config(args, args.config_file), args

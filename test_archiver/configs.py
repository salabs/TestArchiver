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


class Config:

    def __init__(self, cli_args=None, file_config=None):
        self._cli_args = cli_args
        if isinstance(file_config, str):
            self._file_config = read_config_file(file_config)
        else:
            self._file_config = file_config or {}
        self._changes = 'changes'
        self._default = 'default'
        self._resolve_options()

    def _resolve_options(self):
        # Database connection
        self.database = self.resolve_option('database', default='test_archive')
        self.user = self.resolve_option('user')
        self.password = self.resolve_option('password')
        self.host = self.resolve_option('host')
        self.port = self.resolve_option('port', default=5432, cast_as=int)
        self.db_engine = self.resolve_option('db_engine', default='sqlite')
        self.require_ssl = self.resolve_option('require_ssl', default=True, cast_as=bool)

        # Test metadata
        self.team = self.resolve_option('team')
        self.repository = self.resolve_option('repository', default='default repo')
        self.series = self.resolve_list_option('series')
        self.metadata = self.resolve_map_option('metadata')

        # Schema updates
        self.allow_major_schema_updates = self.resolve_option('allow_major_schema_updates',
                                                              default=False, cast_as=bool)
        self.allow_minor_schema_updates = self.resolve_option('allow_minor_schema_updates',
                                                              default=False, cast_as=bool)
        # If major updates are allowed then minor ones are as well
        self.allow_minor_schema_updates = self.allow_major_schema_updates or self.allow_minor_schema_updates

        # Limit archived data
        self.archive_keywords = self.resolve_option('archive_keywords', default=True, cast_as=bool)
        self.archive_keyword_statistics = self.resolve_option('archive_keyword_statistics', default=True,
                                                              cast_as=bool)
        self.ignore_logs = self.resolve_option('ignore_logs', default=False, cast_as=bool)
        self.ignore_logs_below = self.resolve_option('ignore_logs_below', default=None)

        # Adjust timestamps
        self.time_adjust_secs = self.resolve_option('time_adjust_secs', default=0, cast_as=int)
        self.time_adjust_with_system_timezone = self.resolve_option('time_adjust_with_system_timezone',
                                                                    default=False, cast_as=bool)
        # ChangeEngine listener
        self.change_engine_url = self.resolve_option('change_engine_url')
        self.execution_context = self.resolve_execution_context()
        self.changes = self.resolve_changes()

    def resolve_option(self, name, default=None, cast_as=str):
        if self._cli_args and name in self._cli_args and self._cli_args.__getattribute__(name) is not None:
            value = self._cli_args.__getattribute__(name)
        else:
            value = self._file_config.get(name, default)
        if value is None:
            value = default
        try:
            return value if value is None else cast_as(value)
        except ValueError as value_error:
            print("Error: incompatible value for option '{}'".format(name))
            raise value_error

    def resolve_execution_context(self):
        execution_context = self.resolve_option('execution_context')
        if execution_context is None:
            changes = self.resolve_option(self._changes)
            if changes is None:
                execution_context = self._default
            else:
                data = read_config_file(changes)
                execution_context = data.get('context', self._default)
        return execution_context

    def resolve_changes(self):
        changes_file = self.resolve_option(self._changes)
        if changes_file is None:
            return []
        data = read_config_file(changes_file)
        return data.get(self._changes, [])

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
                        help=('Path to JSON config file containing database credentials and other '
                              'configurations. Options given on command line will override options '
                              'set in a config file.'))

    group = parser.add_argument_group('Database connection')
    group.add_argument('--dbengine', dest='db_engine',
                       help='Database engine, postgresql or sqlite (default)')
    group.add_argument('--database', help='database name')
    group.add_argument('--host', help='database host name', default=None)
    group.add_argument('--user', help='database user')
    group.add_argument('--pw', '--password', dest='password', help='database password')
    group.add_argument('--port', help='database port (default: 5432)')
    group.add_argument('--dont-require-ssl', dest='require_ssl', action='store_false', default=None,
                       help='Disable the default behavior to require ssl from the target database.')

    group = parser.add_argument_group('Schema updates')
    group.add_argument('--allow-minor-schema-updates', action='store_true', default=None,
                       help=('Allow TestArchiver to perform MINOR (backwards compatible) schema '
                             'updates the test archive'))
    group.add_argument('--allow-major-schema-updates', action='store_true', default=None,
                       help=('Allow TestArchiver to perform MAJOR (backwards incompatible) schema '
                             'updates the test archive'))

    group = parser.add_argument_group('Limit archived data')
    group.add_argument('--no-keywords', dest='archive_keywords', action='store_false',
                       default=None, help='Do not archive keyword data')
    group.add_argument('--no-keyword-stats', dest='archive_keyword_statistics', action='store_false',
                       default=None, help='Do not archive keyword statistics')
    group.add_argument('--ignore-logs-below', default=None, choices=LOG_LEVEL_CUT_OFF_OPTIONS,
                       help=('Sets a cut off level for archived log messages. '
                             'By default archives all available log messages.'))
    group.add_argument('--ignore-logs', action='store_true', default=None,
                       help='Do not archive any log messages')

    group = parser.add_argument_group('Adjust timestamps')
    group.add_argument('--time-adjust-secs', dest='time_adjust_secs',
                       help='Adjust time in timestamps by given seconds. This can be used to change time '
                            'to utc before writing the results to database, especially if the test system '
                            'uses local time, such as robot framework. '
                            'For example if test were run in Finland (GMT+3) in summer (+1hr), calculate '
                            'total hours by minutes and seconds and invert to adjust in correct direction,'
                            ' i.e. -(3+1)*60*60, so --time-adjust-secs -14400. '
                            'This option is useful if you are archiving in a different location to where '
                            'tests are run.'
                            'If you are running tests and archiving in same timezone, '
                            'time-adjust-with-system-timezone may be a better option. '
                            'This option may be used in conjunction with '
                            '--time-adjust-with-system-timezone if desired.')
    group.add_argument('--time-adjust-with-system-timezone', dest='time_adjust_with_system_timezone',
                       default=None, action='store_true',
                       help='Adjust the time in timestamps by the system timezone (including daylight '
                            'savings adjust). If you are archiving tests in the same timezone as you are '
                            'running tests, setting this option will ensure time written to the database '
                            'is in UTC/GMT time. This assumes that if multiple computers are used that '
                            'their timezone and daylight savings settings are identical. '
                            'Take care also that you do not run tests just before a daylight savings time '
                            'adjust and archive just after, as times will be out by one hour. This could '
                            'easily happen if long running tests cross a timezone adjust boundary. '
                            'This option may be used in conjunction with --time-adjust-secs.')
    return parser


def configuration(argument_parser):
    if sys.version_info[0] < 3:
        sys.exit('Unsupported Python version (' + str(sys.version_info.major) + '). Please use version 3.')

    args = argument_parser().parse_args()
    return Config(args, args.config_file), args

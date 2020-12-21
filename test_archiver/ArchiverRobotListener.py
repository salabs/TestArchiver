# pylint: disable=C0103
# Module name "ArchiverRobotListener" doesn't conform to snake_case naming style (invalid-name)
# Because Robot Framework needs it to have the same name as the listener class
# pylint: disable=W0613
# Listener methods have unused arguments

from . import archiver, configs

class ArchiverRobotListener:
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, config_file_or_database,
                 db_engine=None, user=None, pw=None, host=None, port=5432, adjust_with_system_timezone=False):
        if not db_engine:
            config = configs.Config(file_config=config_file_or_database)
        else:
            config = configs.Config(file_config={
                'database': config_file_or_database,
                'db_engine': db_engine,
                'user': user,
                'password': pw,
                'host': host,
                'port': port,
                'time_adjust_with_system_timezone': adjust_with_system_timezone})

        database = archiver.database_connection(config)
        self.archiver = archiver.Archiver(database, config)
        self.archiver.test_type = "Robot Framework"
        self.rpa = False
        self.dry_run = False
        self.generator = None

    def start_suite(self, name, attrs):
        if not self.archiver.test_run_id:
            self.archiver.begin_test_run('ArchiverListener',
                                         None,
                                         self.generator,
                                         self.rpa,
                                         self.dry_run)
        self.archiver.begin_suite(name)

    def end_suite(self, name, attrs):
        self.archiver.end_suite(attrs)

    def start_test(self, name, attrs):
        self.archiver.begin_test(name)

    def end_test(self, name, attrs):
        self.archiver.end_test(attrs)

    def start_keyword(self, name, attrs):
        self.archiver.begin_keyword(attrs['kwname'], attrs['libname'], attrs['type'], attrs['args'])

    def end_keyword(self, name, attrs):
        self.archiver.end_keyword(attrs)

    def log_message(self, message):
        self.archiver.begin_log_message(message['level'], message['timestamp'])
        self.archiver.end_log_message(message['message'])

    def message(self, message):
        if not self.generator:
            self.generator = message['message']
        elif message['message'].startswith('Settings:'):
            self.process_settings(message['message'])

    def process_settings(self, settings):
        settings = dict([row.split(':', 1) for row in settings.split('\n')])

        self.rpa = bool('RPA' in settings and settings['RPA'].strip() == 'True')
        self.dry_run = bool(settings['DryRun'].strip() == 'True')

    def close(self):
        self.archiver.end_test_run()

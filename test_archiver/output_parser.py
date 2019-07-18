import argparse
import os.path
import sys
import xml.sax

from archiver import Archiver, read_config_file, ARCHIVED_LOG_LEVELS

SUPPORTED_OUTPUT_FORMATS = (
        'robot', 'robotframework',
        'xunit',
        'junit',
        'mocha-junit',
    )

DEFAULT_SUITE_NAME = 'Unnamed suite'


class XmlOutputParser(xml.sax.handler.ContentHandler):
    def __init__(self, archiver):
        self.archiver = archiver
        self._current_content = []
        self.excluding = False
        self.dryrun = False
        self.skipping_content = False

    def startElement(self, name, attrs):
        raise NotImplementedError

    def endElement(self, name):
        raise NotImplementedError

    def content(self):
        cont = ''.join(self._current_content).strip(' \n')
        self._current_content = []
        return cont

    def characters(self, content):
        if not self.skipping_content:
            if content.strip('\n'):
                self._current_content.append(content)


class RobotFrameworkOutputParser(XmlOutputParser):
    EXCLUDED_SECTIONS = ('statistics', 'errors')

    def __init__(self, archiver):
        super(RobotFrameworkOutputParser, self).__init__(archiver)

    def startElement(self, name, attrs):
        if name in RobotFrameworkOutputParser.EXCLUDED_SECTIONS:
            self.excluding = True
        elif self.excluding:
            self.skipping_content = True
        elif name == 'robot':
            self.archiver.begin_test_run('RF parser',
                                         attrs.get('generated'),
                                         attrs.get('generator'),
                                         attrs.get('rpa') if 'rpa' in attrs.getNames() else False,
                                         None,
                                         )
        elif name == 'suite':
            self.archiver.begin_suite(attrs.getValue('name'))
        elif name == 'test':
            self.archiver.begin_test(attrs.getValue('name'))
        elif name == 'kw':
            name = attrs.getValue('name') if 'name' in attrs.getNames() else '${EMPTY}'
            kw_type = attrs.getValue('type') if 'type' in attrs.getNames() else 'Keyword'
            library = attrs.getValue('library') if 'library' in attrs.getNames() else ''
            self.archiver.begin_keyword(name, library, kw_type)
        elif name == 'arg':
            pass
        elif name == 'msg':
            self.archiver.begin_log_message(attrs.getValue('level'), attrs.getValue('timestamp'))
            if attrs.getValue('level') not in ARCHIVED_LOG_LEVELS:
                self.skipping_content = True
        elif name == 'status':
            self.archiver.begin_status(attrs.getValue('status'), attrs.getValue('starttime'),
                                       attrs.getValue('endtime'))
        elif name == 'assign':
            pass
        elif name == 'var':
            pass
        elif name == 'timeout':
            pass
        elif name == 'tag':
            pass
        elif name == 'item':  # metadata item
            self.archiver.begin_metadata(attrs.getValue('name'))
        elif name == 'doc':
            pass
        elif name in ('arguments', 'tags', 'metadata'):
            pass
        else:
            print("WARNING: begin unknown item '{}'".format(name))

    def endElement(self, name):
        if name in RobotFrameworkOutputParser.EXCLUDED_SECTIONS:
            self.excluding = False
        elif self.excluding:
            self.skipping_content = False
        elif name == 'robot':
            self.archiver.update_dryrun_status()
        elif name == 'suite':
            self.archiver.end_suite()
        elif name == 'test':
            self.archiver.end_test()
        elif name == 'kw':
            self.archiver.end_keyword()
        elif name == 'arg':
            self.archiver.update_arguments(self.content())
        elif name == 'msg':
            self.archiver.end_log_message(self.content())
            self.skipping_content = False
        elif name == 'status':
            pass
        elif name == 'assign':
            pass
        elif name == 'var':
            pass
        elif name == 'timeout':
            pass
        elif name == 'tag':
            self.archiver.update_tags(self.content())
        elif name == 'item':  # metadata item
            self.archiver.end_metadata(self.content())
        elif name == 'doc':
            pass
        elif name in ('arguments', 'tags', 'metadata'):
            pass
        else:
            print("WARNING: ending unknown item '{}'".format(name))
        self._current_content = []


class XUnitOutputParser(XmlOutputParser):
    def __init__(self, archiver):
        super(XUnitOutputParser, self).__init__(archiver)

    def startElement(self, name, attrs):
        if name in []:
            self.excluding = True
        elif self.excluding:
            self.skipping_content = True
        elif name in ('testsuite', 'testsuites'):
            if not self.archiver.test_run_id:
                self.archiver.begin_test_run(
                    'xUnit parser', None, 'xUnit', False, None
                    )
            suite_name = attrs.getValue('name') if 'name' in attrs.getNames() else DEFAULT_SUITE_NAME
            self.archiver.begin_suite(suite_name)
            errors = int(attrs.getValue('errors')) if 'errors' in attrs.getNames() else 0
            failures = int(attrs.getValue('failures')) if 'failures' in attrs.getNames() else 0
            suite_status = 'PASS' if errors + failures == 0 else 'FAIL'
            elapsed = int(float(attrs.getValue('time'))*1000) if 'time' in attrs.getNames() else None
            timestamp = attrs.getValue('timestamp') if 'timestamp' in attrs.getNames() else None
            self.archiver.begin_status(suite_status, start_time=timestamp, elapsed=elapsed)
        elif name == 'testcase':
            class_name = attrs.getValue('classname')
            self.archiver.begin_test(attrs.getValue('name'), class_name)
            elapsed = int(float(attrs.getValue('time'))*1000)
            status = attrs.getValue('status') if 'status' in attrs.getNames() else 'PASS'
            self.archiver.begin_status('PASS', elapsed=elapsed)
        elif name == 'failure':
            self.archiver.update_status('FAIL')
            self.archiver.log_message('FAIL', attrs.getValue('message'))
        elif name == 'error':
            self.archiver.update_status('FAIL')
            self.archiver.log_message('ERROR', attrs.getValue('message'))
        elif name == 'skipped':
            self.archiver.update_status('SKIPPED')
            if 'message' in attrs.getNames():
                self.archiver.log_message('INFO', attrs.getValue('message'))
        elif name in ('system-out', 'system-err'):
            pass
        elif name == 'properties':
            pass
        elif name == 'property':
            self.archiver.metadata(attrs.getValue('name'), attrs.getValue('value'))
        else:
            print("WARNING: begin unknown item '{}'".format(name))

    def endElement(self, name):
        if name in []:
            self.excluding = False
        elif self.excluding:
            self.skipping_content = False
        elif name in ('testsuite', 'testsuites'):
            self.archiver.end_suite()
        elif name == 'testcase':
            self.archiver.end_test()
        elif name == 'failure':
            self.archiver.log_message('FAIL', self.content())
        elif name == 'error':
            self.archiver.log_message('ERROR', self.content())
        elif name == 'system-out':
            self.archiver.log_message('INFO', self.content())
        elif name == 'system-err':
            self.archiver.log_message('ERROR', self.content())
        elif name in ('properties', 'property'):
            pass
        elif name == 'skipped':
            pass
        else:
            print("WARNING: ending unknown item '{}'".format(name))
        self._current_content = []


class JUnitOutputParser(XmlOutputParser):
    def __init__(self, archiver):
        super(JUnitOutputParser, self).__init__(archiver)

    def _report_test_run(self):
        self.archiver.begin_test_run('JUnit parser', None, 'JUnit', False, None)

    def startElement(self, name, attrs):
        if name in []:
            self.excluding = True
        elif self.excluding:
            self.skipping_content = True
        elif name == 'testrun':
            self._report_test_run()
            if 'project' in attrs.getNames():
                self.archiver.metadata['project'] = attrs.getValue('project')
            if 'name' in attrs.getNames():
                self.archiver.metadata['test run name'] = attrs.getValue('name')
        elif name in ('testsuite', 'testsuites'):
            if not self.archiver.test_run_id:
                self._report_test_run()
            suite_name = attrs.getValue('name') if 'name' in attrs.getNames() else DEFAULT_SUITE_NAME
            self.archiver.begin_suite(suite_name)
            errors = int(attrs.getValue('errors')) if 'errors' in attrs.getNames() else 0
            failures = int(attrs.getValue('failures')) if 'failures' in attrs.getNames() else 0
            suite_status = 'PASS' if errors + failures == 0 else 'FAIL'
            elapsed = int(float(attrs.getValue('time'))*1000) if 'time' in attrs.getNames() else None
            timestamp = attrs.getValue('timestamp') if 'timestamp' in attrs.getNames() else None
            self.archiver.begin_status(suite_status, start_time=timestamp, elapsed=elapsed)
        elif name == 'testcase':
            class_name = attrs.getValue('classname')
            self.archiver.begin_test(attrs.getValue('name'), class_name)
            elapsed = int(float(attrs.getValue('time'))*1000)
            status = attrs.getValue('status') if 'status' in attrs.getNames() else 'PASS'
            self.archiver.begin_status('PASS', elapsed=elapsed)
        elif name == 'failure':
            self.archiver.update_status('FAIL')
            self.archiver.log_message('FAIL', attrs.getValue('message'))
        elif name == 'error':
            self.archiver.update_status('FAIL')
            self.archiver.log_message('ERROR', attrs.getValue('message'))
        elif name == 'skipped':
            self.archiver.update_status('SKIPPED')
            if 'message' in attrs.getNames():
                self.archiver.log_message('INFO', attrs.getValue('message'))
        elif name in ('system-out', 'system-err'):
            pass
        elif name == 'properties':
            pass
        elif name == 'property':
            self.archiver.metadata(attrs.getValue('name'), attrs.getValue('value'))
        else:
            print("WARNING: begin unknown item '{}'".format(name))

    def endElement(self, name):
        if name in []:
            self.excluding = False
        elif self.excluding:
            self.skipping_content = False
        elif name == 'testrun':
            pass
        elif name in ('testsuite', 'testsuites'):
            self.archiver.end_suite()
        elif name == 'testcase':
            self.archiver.end_test()
        elif name == 'failure':
            self.archiver.log_message('FAIL', self.content())
        elif name == 'error':
            self.archiver.log_message('ERROR', self.content())
        elif name == 'system-out':
            self.archiver.log_message('INFO', self.content())
        elif name == 'system-err':
            self.archiver.log_message('ERROR', self.content())
        elif name in ('properties', 'property'):
            pass
        elif name == 'skipped':
            pass
        else:
            print("WARNING: ending unknown item '{}'".format(name))
        self._current_content = []



class MochaJUnitOutputParser(XmlOutputParser):
    def __init__(self, archiver):
        super(MochaJUnitOutputParser, self).__init__(archiver)
        self.in_setup_or_teardown = False

    def _end_previous_test(self):
        if self.archiver._current_item()._item_type() == 'test':
            self.archiver.end_test()

    def _end_suite(self):
        suite = self.archiver.current_suite()
        if suite.execution_status and suite.execution_status != 'PASS':
            self.archiver.update_status('FAIL')
        self.archiver.end_suite()

    def startElement(self, name, attrs):
        if name == 'testsuites':
            self.archiver.begin_test_run('Mocha-JUnit parser', None, attrs.getValue('name'), False, None)
            #self.archiver.begin_suite(attrs.getValue('name'))
        elif name == 'testsuite':
            suite_name = attrs.getValue('name')
            if not suite_name:
                # The root suite name can be overridden in the reporter options
                # but then the full suite hierarchy will break in the top
                suite_name = "Root Suite"
            while (self.archiver.current_suite()
                   and not suite_name.startswith(self.archiver.current_suite().full_name + '.')):
                self._end_suite()
            parent_suite = self.archiver.current_suite()
            if parent_suite:
                suite_name = suite_name.split('.')[-1]
            self.archiver.begin_suite(suite_name)
            elapsed = int(float(attrs.getValue('time'))*1000) if 'time' in attrs.getNames() else None
            timestamp = attrs.getValue('timestamp') if 'timestamp' in attrs.getNames() else None
            self.archiver.begin_status('PASS', start_time=timestamp, elapsed=elapsed)
        elif name == 'testcase':
            class_name = attrs.getValue('classname')
            elapsed = int(float(attrs.getValue('time'))*1000)
            # If test name contains substring "hook for" it is actually a setup/teardown phase
            # for another test or suite
            if "hook for" in str(class_name):
                self.in_setup_or_teardown = True
                hook_prefix = class_name.split(" hook for ")[0]
                hook_postfix = class_name.split(" hook for ")[1]
                if "before all" in hook_prefix:
                    self.archiver.update_status('FAIL')
                    self.archiver.begin_keyword('before all hook', 'mocha', 'setup')
                if "after all" in hook_prefix:
                    self._end_previous_test()
                    self.archiver.update_status('FAIL')
                    self.archiver.begin_keyword('after all hook', 'mocha', 'teardown')
                if "before each" in hook_prefix:
                    hooked_testname = hook_postfix.strip('"')
                    self.archiver.begin_test(hooked_testname)
                    self.archiver.update_status('FAIL')
                    self.archiver.begin_keyword('before each hook', 'mocha', 'setup')
                if "after each" in hook_prefix:
                    hooked_testname = str(hook_prefix.split("after each")[0][:-2])
                    self.archiver.update_status('FAIL')
                    self.archiver.begin_keyword('after each hook', 'mocha', 'teardown')
            else:
                self._end_previous_test()
                self.archiver.begin_test(attrs.getValue('name'))
                self.archiver.keyword('Passing execution', 'mocha', 'kw', 'PASS')
                self.archiver.begin_status('PASS', elapsed=elapsed)
        elif name == 'failure':
            self.archiver.begin_keyword(attrs.getValue('type'), 'failure', 'failure')
            self.archiver.update_status('FAIL')
            self.archiver.log_message('FAIL', attrs.getValue('message'))
        elif name == 'error':
            self.archiver.begin_keyword(attrs.getValue('type'), 'error', 'error')
            self.archiver.update_status('FAIL')
            self.archiver.log_message('ERROR', attrs.getValue('message'))
        elif name == 'skipped':
            self.archiver.update_status('SKIPPED')
            if 'message' in attrs.getNames():
                self.archiver.log_message('INFO', attrs.getValue('message'))
        elif name in ('system-out', 'system-err'):
            pass
        elif name == 'properties':
            pass
        elif name == 'property':
            self.archiver.metadata(attrs.getValue('name'), attrs.getValue('value'))
        else:
            print("WARNING: begin unknown item '{}'".format(name))

    def endElement(self, name):
        if name == 'testsuites':
            while self.archiver._current_item()._item_type() == 'suite':
                self._end_suite()
        elif name == 'testsuite':
            self._end_previous_test()
        elif name == 'testcase':
            if self.in_setup_or_teardown:
                self.in_setup_or_teardown = False
                self.archiver.end_keyword()
                self._end_previous_test()
        elif name == 'failure':
            self.archiver.log_message('FAIL', self.content())
            self.archiver.end_keyword()
            self.archiver.update_status('FAIL')
        elif name == 'error':
            self.archiver.log_message('ERROR', self.content())
            self.archiver.end_keyword()
            self.archiver.update_status('FAIL')
        elif name == 'system-out':
            self.archiver.log_message('INFO', self.content())
        elif name == 'system-err':
            self.archiver.log_message('ERROR', self.content())
        elif name in ('properties', 'property'):
            pass
        elif name == 'skipped':
            pass
        else:
            print("WARNING: ending unknown item '{}'".format(name))
        self._current_content = []


def parse_xml(xml_file, output_format, db_engine, config):
    if not os.path.exists(xml_file):
        sys.exit('Could not find input file: ' + xml_file)
    BUFFER_SIZE = 65536
    archiver = Archiver(db_engine, config)
    if output_format.lower() in ('rf', 'robot', 'robotframework'):
        handler = RobotFrameworkOutputParser(archiver)
    elif output_format.lower() == 'xunit':
        handler = XUnitOutputParser(archiver)
    elif output_format.lower() == 'junit':
        handler = JUnitOutputParser(archiver)
    elif output_format.lower() == 'mocha-junit':
        handler = MochaJUnitOutputParser(archiver)
    else:
        raise Exception("Unsupported report format '{}'".format(output_format))
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    with open(xml_file) as file:
        buffer = file.read(BUFFER_SIZE)
        while buffer:
            parser.feed(buffer)
            buffer = file.read(BUFFER_SIZE)
    if len(archiver.stack) != 1:
        raise Exception('File parse error. Please check you used proper output format (default: robotframework).')
    else:
        archiver.end_test_run()


def parse_metadata_args(metadata_args):
    metadata = {}
    if metadata_args:
        for item in metadata_args:
            try:
                name, value = item.split(':', 1)
                metadata[name] = value
            except Exception:
                raise Exception("Unsupported format for metadata: '{}' use NAME:VALUE".format(item))
    return metadata


if __name__ == '__main__':
    if sys.version_info[0] < 3:
        sys.exit('Unsupported Python version (' + str(sys.version_info.major) + '). Please use version 3.')
    parser = argparse.ArgumentParser(description='Parse Robot Framework output.xml files to SQL database.')
    parser.add_argument('output_files', nargs='+')
    parser.add_argument('--config', dest='config_file',
                        help='path to JSON config file containing database credentials')
    parser.add_argument('--dbengine', default='sqlite',
                        help='Database engine, postgresql or sqlite (default)')
    parser.add_argument('--database', help='database name')
    parser.add_argument('--host', help='databse host name', default=None)
    parser.add_argument('--user', help='database user')
    parser.add_argument('--pw', '--password', help='database password')
    parser.add_argument('--port', help='database port (default: 5432)', default=5432, type=int)
    parser.add_argument('--format', help='output format (default: robotframework)', default='robotframework',
                        choices=SUPPORTED_OUTPUT_FORMATS, type=str.lower)
    parser.add_argument('--team', help='Team name for the test series', default=None)
    parser.add_argument('--series', action='append',
                        help="Name of the testseries (and optionally build number 'SERIES_NAME#BUILD_NUM')")
    parser.add_argument('--metadata', action='append',
                        help="Adds given metadata to the testrun. expected_format 'NAME:VALUE'")
    args = parser.parse_args()

    if args.config_file:
        config = read_config_file(args.config_file)
        db_engine = config['db_engine']
    else:
        db_engine = args.dbengine
        config = {
            'database': args.database,
            'user': args.user,
            'password': args.pw,
            'host': args.host,
            'port': args.port,
            }
    config['series'] = args.series
    if args.team:
        config['team'] = args.team
    metadata = parse_metadata_args(args.metadata)
    if 'metadata' in config:
        config['metadata'].update(metadata)
    else:
        config['metadata'] = metadata
    if len(args.output_files) > 1:
        config['multirun'] = {}

    for output_file in args.output_files:
        print("Parsing: '{}'".format(output_file))
        parse_xml(output_file, args.format, db_engine, config)

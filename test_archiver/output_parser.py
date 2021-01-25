# pylint: disable=R0912,R0915

import os.path
import sys
import xml.sax
import datetime
from . import archiver, configs


DEFAULT_SUITE_NAME = 'Unnamed suite'


class XmlOutputParser(xml.sax.handler.ContentHandler):
    def __init__(self, archiver_instance):
        super(XmlOutputParser, self).__init__()
        self.archiver = archiver_instance
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
            if content:
                self._current_content.append(content)


class RobotFrameworkOutputParser(XmlOutputParser):
    EXCLUDED_SECTIONS = ('statistics', 'errors')

    def __init__(self, archiver_instance):
        super(RobotFrameworkOutputParser, self).__init__(archiver_instance)
        self.archiver.test_type = "Robot Framework"

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
            execution_path = attrs.getValue('id') if 'id' in attrs.getNames() else None
            self.archiver.begin_suite(attrs.getValue('name'), execution_path=execution_path)
        elif name == 'test':
            execution_path = attrs.getValue('id') if 'id' in attrs.getNames() else None
            self.archiver.begin_test(attrs.getValue('name'), execution_path=execution_path)
        elif name == 'kw':
            name = attrs.getValue('name') if 'name' in attrs.getNames() else '${EMPTY}'
            kw_type = attrs.getValue('type') if 'type' in attrs.getNames() else 'Keyword'
            library = attrs.getValue('library') if 'library' in attrs.getNames() else ''
            self.archiver.begin_keyword(name, library, kw_type)
            #self.archiver.set_execution_path(attrs.getValue('id'))
        elif name == 'arg':
            pass
        elif name == 'msg':
            self.archiver.begin_log_message(attrs.getValue('level'), attrs.getValue('timestamp'))
            if self.archiver.config.log_level_ignored(attrs.getValue('level')):
                self.skipping_content = True
        elif name == 'status':
            critical = attrs.getValue('critical') == 'yes' if 'critical' in attrs.getNames() else None
            self.archiver.begin_status(attrs.getValue('status'), attrs.getValue('starttime'),
                                       attrs.getValue('endtime'), critical=critical)
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
            if self.archiver.current_item_is_test():
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
    def __init__(self, archiver_instance):
        super(XUnitOutputParser, self).__init__(archiver_instance)
        self.archiver.test_type = "xunit"

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
            self.archiver.begin_test(attrs.getValue('name'), class_name=class_name)
            elapsed = int(float(attrs.getValue('time'))*1000)
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
    def __init__(self, archiver_instance):
        super(JUnitOutputParser, self).__init__(archiver_instance)
        self.archiver.test_type = "junit"

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
            self.archiver.begin_test(attrs.getValue('name'), class_name=class_name)
            elapsed = int(float(attrs.getValue('time'))*1000)
            self.archiver.begin_status('PASS', elapsed=elapsed)
        elif name == 'failure':
            self.archiver.update_status('FAIL')
            try:
                self.archiver.log_message('FAIL', attrs.getValue('message'))
            except KeyError:
                print("Ignoring empty message attribute in failure element")
                # jest-junit does not add 'message' attribute to 'failure' xml element
                # https://github.com/jest-community/jest-junit
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
    def __init__(self, archiver_instance):
        super(MochaJUnitOutputParser, self).__init__(archiver_instance)
        self.in_setup_or_teardown = False
        self.archiver.test_type = "mocha-junit"

    def _end_previous_test(self):
        if self.archiver.current_item_is_test():
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
                    self._end_previous_test()
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
            while self.archiver.current_item_is_suite():
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


class PytestJUnitOutputParser(XmlOutputParser):
    def __init__(self, archiver_instance):
        super(PytestJUnitOutputParser, self).__init__(archiver_instance)
        self.in_setup_or_teardown = False
        self._current_class_name = None
        self._current_test_name = None
        self.archiver.test_type = "pytest-junit"

    def _report_test_run(self):
        self.archiver.begin_test_run('pytest JUnit parser', None, 'pytest', False, None)

    def _handle_suites_from_class_name(self, class_name):
        next_suite_stack = class_name.split('.')
        current_suites = self.archiver.current_suites()
        next_suite_stack.insert(0, current_suites[0].name)
        common_suites = 0
        for i, current_suite in enumerate(current_suites):
            if i >= len(next_suite_stack) or current_suite.name != next_suite_stack[i]:
                break
            common_suites += 1
        for i in range(common_suites, len(current_suites)):
            self.archiver.end_suite()
        for i in range(common_suites, len(next_suite_stack)):
            self.archiver.begin_suite(next_suite_stack[i])

    def _parse_error_to_keyword(self, error, log_level='ERROR'):
        if ':' in error:
            exception, message = error.split(': ', 1)
            self.archiver.begin_keyword(exception, 'python', 'kw', [message])
            self.archiver.update_status('FAIL')
        elif error == 'test setup failure':
            self.archiver.keyword('failed by class setUp', 'python', 'kw', 'FAIL')
            self.archiver.end_test()
            if self.archiver.current_suite().setup_status is None:
                self.archiver.begin_keyword('setUpClass', 'python', 'setup')
                self.archiver.update_status('FAIL')
                self.in_setup_or_teardown = True
        elif error == 'test teardown failure':
            self.in_setup_or_teardown = True
        else:
            self.archiver.log_message(log_level, error)

    def _detect_test_setup_or_teardown_from_stack_trace(self, trace):
        if 'def tearDown(self' in trace:
            self.archiver.keyword('test', 'python', 'teardown', 'FAIL')
        elif 'def tearDownClass(cls' in trace:
            self.archiver.end_test()
            self.archiver.keyword('tearDownClass', 'python', 'teardown', 'FAIL')
        elif 'def setUp(self' in trace:
            keyword = self.archiver.current_keyword()
            keyword.kw_type = 'setup'
            self.archiver.end_keyword()

    def _begin_new_test(self, class_name, test_name):
        self._handle_suites_from_class_name(class_name)
        self._current_class_name = class_name
        self.archiver.begin_test(test_name)
        self._current_test_name = test_name

    def startElement(self, name, attrs):
        if name in []:
            self.excluding = True
        elif self.excluding:
            self.skipping_content = True
        elif name == 'testsuites':
            pass
        elif name == 'testsuite':
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
            test_name = attrs.getValue('name')
            if self.archiver.current_item_is_test():
                current_test = self.archiver.current_item()
                if class_name != self._current_class_name or current_test.name != test_name:
                    self.archiver.end_test()
                    self._begin_new_test(class_name, test_name)
            else:
                self._begin_new_test(class_name, test_name)
            elapsed = int(float(attrs.getValue('time'))*1000)
            self.archiver.begin_status('PASS', elapsed=elapsed)
        elif name == 'failure':
            self.archiver.update_status('FAIL')
            self._parse_error_to_keyword(attrs.getValue('message'), 'FAIL')
        elif name == 'error':
            self.archiver.update_status('FAIL')
            self._parse_error_to_keyword(attrs.getValue('message'), 'ERROR')
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
        elif name == 'testsuites':
            pass
        elif name == 'testsuite':
            if self.archiver.current_item_is_test():
                self.archiver.end_test()
            while self.archiver.current_suite():
                self.archiver.end_suite()
        elif name == 'testcase':
            while self.archiver.current_item_is_keyword():
                self.archiver.end_keyword()
        elif name == 'failure':
            content = self.content()
            self._detect_test_setup_or_teardown_from_stack_trace(content)
            self.archiver.log_message('FAIL', content)
        elif name == 'error':
            content = self.content()
            self._detect_test_setup_or_teardown_from_stack_trace(content)
            self.archiver.log_message('ERROR', content)
        elif name == 'system-out':
            self.archiver.log_message('INFO', self.content())
        elif name == 'system-err':
            self.archiver.log_message('ERROR', self.content())
        elif name in ('properties', 'property'):
            pass
        elif name == 'skipped':
            self.archiver.log_message('INFO', self.content())
        else:
            print("WARNING: ending unknown item '{}'".format(name))
        self._current_content = []

class PhpJUnitOutputParser(XmlOutputParser):

    def __init__(self, archiver_instance):
        super(PhpJUnitOutputParser, self).__init__(archiver_instance)
        self.archiver.test_type = "php-junit"

    def _report_test_run(self):
        self.archiver.begin_test_run('php JUnit parser', None, 'phpunit', False, None)

    def _detect_test_setup_or_teardown_from_stack_trace(self, trace):
        if 'tearDownAfterClass' in trace:
            self.archiver.keyword('tearDownClass', 'phpunit', 'teardown', 'FAIL')

    def startElement(self, name, attrs):
        if name == 'testrun':
            self._report_test_run()
            if 'project' in attrs.getNames():
                self.archiver.metadata['project'] = attrs.getValue('project')
            if 'name' in attrs.getNames():
                self.archiver.metadata['test run name'] = attrs.getValue('name')
        elif name in ('testsuite', 'testsuites'):
            if not self.archiver.test_run_id:
                self._report_test_run()
            if('file' not in attrs.getNames() and 'name' in attrs.getNames()):
                suite_name = attrs.getValue('name').split('/')[-1]
            elif name == 'testsuites':
                suite_name = 'phpunit'
            else:
                suite_name = attrs.getValue('name') if 'name' in attrs.getNames() else DEFAULT_SUITE_NAME
            self.archiver.begin_suite(suite_name)
            errors = int(attrs.getValue('errors')) if 'errors' in attrs.getNames() else 0
            failures = int(attrs.getValue('failures')) if 'failures' in attrs.getNames() else 0
            suite_status = 'PASS' if errors + failures == 0 else 'FAIL'
            elapsed = int(float(attrs.getValue('time'))*1000) if 'time' in attrs.getNames() else None
            time_now = datetime.datetime.now().isoformat()
            timestamp = attrs.getValue('timestamp') if 'timestamp' in attrs.getNames() else time_now
            self.archiver.begin_status(suite_status, start_time=timestamp, elapsed=elapsed)
        elif name == 'testcase':
            class_name = attrs.getValue('classname')
            self.archiver.begin_test(attrs.getValue('name'), class_name=class_name)
            elapsed = int(float(attrs.getValue('time'))*1000)
            self.archiver.begin_status('PASS', elapsed=elapsed)
        elif name == 'failure':
            self.archiver.update_status('FAIL')
            try:
                self.archiver.log_message('FAIL', attrs.getValue('type'))
                self.archiver.keyword(attrs.getValue('type'), 'phpunit', 'kw', 'FAIL')
            except KeyError:
                print("Ignoring empty message attribute in failure element")
                # jest-junit does not add 'message' attribute to 'failure' xml element
                # https://github.com/jest-community/jest-junit
        elif name == 'error':
            self.archiver.update_status('FAIL')
            try:
                self.archiver.log_message('ERROR', attrs.getValue('type'))
            except KeyError:
                print("Ignoring empty message attribute in failure element")
                # jest-junit does not add 'message' attribute to 'failure' xml element
                # https://github.com/jest-community/jest-junit
        elif name == 'skipped':
            self.archiver.update_status('SKIPPED')
            if 'message' in attrs.getNames():
                self.archiver.log_message('INFO', attrs.getValue('type'))
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
            content = self.content()
            self._detect_test_setup_or_teardown_from_stack_trace(content)
            self.archiver.log_message('FAIL', content)
        elif name == 'error':
            content = self.content()
            self.archiver.log_message('ERROR', content)
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


class MSTestOutputParser(XmlOutputParser):
    # Currently only inital support for unittests
    def __init__(self, archiver_instance):
        super(MSTestOutputParser, self).__init__(archiver_instance)
        self.archiver.test_type = "mstest"

    EXCLUDED_SECTIONS = ('TestSettings', 'ResultSummary', 'TestDefinitions', 'TestLists', 'TestEntries')
    STATUS_MAPPING = {
        'Passed': 'PASS',
        'Failed': 'FAIL',
        }

    def _report_test_run(self):
        self.archiver.begin_test_run('MSTest parser', None, 'MSTest', False, None)

    @staticmethod
    def _sanitise_timestamp_format(timestamp):
        # MSTest output timestamps use 7 digits for second fractions while python
        # only parses up to 6. Leaving out the last digit and colon in the timezone
        return timestamp[:26] + timestamp[27:30] + timestamp[31:]

    def startElement(self, name, attrs):
        if name in MSTestOutputParser.EXCLUDED_SECTIONS:
            self.excluding = True
        elif self.excluding:
            self.skipping_content = True
        elif name == 'TestRun':
            self.archiver.begin_test_run('MSTest parser', None, attrs.getValue('name'), False, None)
            self.archiver.begin_suite('Root suite')
        elif name == 'Times':
            start = self._sanitise_timestamp_format(attrs.getValue('start'))
            end = self._sanitise_timestamp_format(attrs.getValue('finish'))
            self.archiver.begin_status('PASS', start, end)
        elif name == 'UnitTestResult':
            self.archiver.begin_test(attrs.getValue('testName'))
            start = self._sanitise_timestamp_format(attrs.getValue('startTime'))
            end = self._sanitise_timestamp_format(attrs.getValue('endTime'))
            status = MSTestOutputParser.STATUS_MAPPING[attrs.getValue('outcome')]
            self.archiver.begin_status(status, start, end)
        elif name == 'StdOut':
            self.archiver.begin_log_message('INFO')
        elif name == 'DebugTrace':
            self.archiver.begin_log_message('DEBUG')
        elif name == 'TraceInfo':
            self.archiver.begin_log_message('TRACE')
        elif name in ('StdErr', 'Message', 'StackTrace'):
            self.archiver.begin_log_message('ERROR')
        elif name in ('Results', 'Output', 'ErrorInfo'):
            pass
        else:
            print("WARNING: begin unknown item '{}'".format(name))

    def endElement(self, name):
        if name in MSTestOutputParser.EXCLUDED_SECTIONS:
            self.excluding = False
        elif self.excluding:
            self.skipping_content = False
        elif name == 'TestRun':
            self.archiver.end_suite()
            self.archiver.end_test_run()
        elif name == 'Times':
            pass
        elif name == 'UnitTestResult':
            self.archiver.end_test()
        elif name == 'StdOut':
            self.archiver.end_log_message(self.content())
        elif name == 'DebugTrace':
            self.archiver.end_log_message(self.content())
        elif name == 'TraceInfo':
            self.archiver.end_log_message(self.content())
        elif name in ('StdErr', 'Message', 'StackTrace'):
            self.archiver.end_log_message(self.content())
        elif name in ('Results', 'Output', 'ErrorInfo'):
            pass
        else:
            print("WARNING: ending unknown item '{}'".format(name))
        self._current_content = []


SUPPORTED_OUTPUT_FORMATS = {
    'robot': RobotFrameworkOutputParser,
    'robotframework': RobotFrameworkOutputParser,
    'xunit': XUnitOutputParser,
    'junit': JUnitOutputParser,
    'mocha-junit': MochaJUnitOutputParser,
    'pytest-junit': PytestJUnitOutputParser,
    'mstest': MSTestOutputParser,
    'php-junit': PhpJUnitOutputParser,
}


def parse_xml(xml_file, output_format, connection, config, build_number_cache):
    output_format = output_format.lower()
    if not os.path.exists(xml_file):
        sys.exit('Could not find input file: ' + xml_file)
    buffer_size = 65536
    test_archiver = archiver.Archiver(connection, config, build_number_cache=build_number_cache)
    if output_format in SUPPORTED_OUTPUT_FORMATS:
        handler = SUPPORTED_OUTPUT_FORMATS[output_format](test_archiver)
    else:
        raise Exception("Unsupported report format '{}'".format(output_format))
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    with open(xml_file, encoding="UTF-8") as file:
        buffer = file.read(buffer_size)
        while buffer:
            parser.feed(buffer)
            buffer = file.read(buffer_size)
    if len(test_archiver.stack) != 1:
        raise Exception('File parse error. Please check you used proper output format '
                        '(default: robotframework).')
    return test_archiver.end_test_run()


def argument_parser():
    changes_help = """\
Json file which contains information from the changed files for each repo. The file should be formatted like this:

{
    "context": "The execution context, same as --execution-context and command line will override this setting.",
    "changes": [
        {
            "name": "string representing the changed item, for example file path", 
            "repository": "Repository (optional), for separating between changed items with identical names.",
            "item_type": "Separating items (optional) and for filtering subsets when prioritising",
            "subtype": "(optional, for separating items for filtering subsets when prioritising"
        }
    ]
}
    """
    parser = configs.base_argument_parser('Parse test automation output.xml files to SQL database.')
    parser.add_argument('output_files', nargs='+',
                        help='list of test output files to parse in to the test archive')

    parser.add_argument('--format', help='output format (default: robotframework)', default='robotframework',
                        choices=SUPPORTED_OUTPUT_FORMATS, type=str.lower)

    parser.add_argument('--repository', default=None,
                        help=('The repository of the test cases. Used to differentiate between test with '
                              'same name in different projects.'))
    parser.add_argument('--team', help='Team name for the test series', default=None)
    parser.add_argument('--series', action='append',
                        help=("Name of the test series (and optionally build number 'SERIES_NAME#BUILD_NUM' "
                              "or build id 'SERIES_NAME#BUILD_ID')"))
    parser.add_argument('--metadata', action='append', metavar='NAME:VALUE',
                        help="Adds given metadata to the test run. Expected format: 'NAME:VALUE'")

    group = parser.add_argument_group('ChangeEngine')
    group.add_argument('--change-engine-url', default=None,
                       help="Starts a listener that feeds results to ChangeEngine")
    group.add_argument('--execution-context', default='default',
                       help='To separate data from different build pipelines for ChangeEngine '
                            'prioritization. Example if same changes or tests may be used to '
                            'verify app in Android and iOS platforms, then it would be good to '
                            'separate the result from different builds pipelines/platforms. The '
                            'ChangeEngine prioritization might not give correct result if different '
                            'results from different platforms are mixed together.')
    group.add_argument('--changes', default=None,
                       help=changes_help)
    return parser


def main():
    config, args = configs.configuration(argument_parser)
    connection = archiver.database_connection(config)

    build_number_cache = {}
    for output_file in args.output_files:
        print("Parsing: '{}'".format(output_file))
        build_number_cache = parse_xml(output_file, args.format, connection, config, build_number_cache)


if __name__ == '__main__':
    main()

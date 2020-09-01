import json
from urllib.request import Request, urlopen

class DefaultListener():
    def __init__(self, archiver):
        self.archiver = archiver
        self.suites = []
        self.tests = []

    def suite_result(self, suite):
        self.suites.append(suite)
        # print(suite.full_name)
        # print(suite.status)

    def test_result(self, test):
        self.tests.append(test)
        # print(test.full_name)
        # print(test.status)

    def end_run(self):
        pass


class ChangeEngineListener(DefaultListener):

    def __init__(self, archiver, change_engine_url):
        super(ChangeEngineListener, self).__init__(archiver)
        self.change_engine_url = change_engine_url

    def end_run(self):
        top_suite = self.suites[-1]
        changes = top_suite.metadata['changes'] if 'changes' in top_suite.metadata else None
        changes = changes.split('\n') if changes else []
        self.report_changes(self.tests, changes)

    def report_changes(self, tests, changes):
        tests_data = []
        for test in tests:
            tests_data.append({'name': test.full_name, 'status': test.status,
                               'subtype': self.archiver.test_type, 'repository': self.archiver.repository})
        data = {"tests": tests_data, "changes": changes}
        url = "{}/result/".format(self.change_engine_url)
        request = Request(url)
        request.add_header('Content-Type', 'application/json;')
        body = json.dumps(data)
        response = urlopen(request, body.encode("utf-8"))
        if response.getcode() != 200:
            print("ERROR: ChangeEngine update failed. Return code: {}".format(response.getcode()))
            print(response.read())

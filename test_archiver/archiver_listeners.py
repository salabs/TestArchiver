import json
from urllib.request import Request, urlopen


class DefaultListener:
    def __init__(self, archiver):
        self.archiver = archiver
        self.suites = []
        self.tests = []

    def suite_result(self, suite):
        self.suites.append(suite)

    def test_result(self, test):
        self.tests.append(test)

    def end_run(self):
        pass


class ChangeEngineListener(DefaultListener):

    def __init__(self, archiver, change_engine_url):
        super(ChangeEngineListener, self).__init__(archiver)
        self.change_engine_url = change_engine_url

    def end_run(self):
        self.report_changes(self.tests)

    def report_changes(self, tests):
        url = "{}/result/".format(self.change_engine_url)
        request = Request(url)
        request.add_header('Content-Type', 'application/json;')
        body = json.dumps(self._format_body(tests))
        response = urlopen(request, body.encode("utf-8"))
        if response.getcode() != 200:
            print("ERROR: ChangeEngine update failed. Return code: {}".format(response.getcode()))
            print(response.read())

    def _filter_tests(self, tests):
        return [
            {
                'name': test.full_name,
                'status': test.status,
                'subtype': self.archiver.test_type,
                'repository': self.archiver.repository
            } for test in tests if test.status != "SKIPPED"
        ]

    def _format_changes(self):
        metadata_changes = self._get_metadata_changes()
        if metadata_changes:
            return metadata_changes
        return self.archiver.changes

    def _get_metadata_changes(self):
        top_suite = self.suites[-1]
        changes = top_suite.metadata['changes'] if 'changes' in top_suite.metadata else None
        changes = changes.split('\n') if changes else []
        return changes

    def _format_body(self, tests):
        return {
            "tests": self._filter_tests(tests),
            "changes": self._format_changes(),
            "context": self.archiver.execution_context
        }

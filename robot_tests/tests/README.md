
## loop_suite
Contains two robot suites using for-loop.

`for_tests.robot`       Different ways to use loops.

`loops.robot`           Loop generating random strings.
## randomized_suite
Contains three suites, which are meant to produce randomized fails.

`bigrandom.robot`       Ten tests with different passing rates.

`flaky.robot`           Test generating fails with different ways.

`random_pass.robot`     Generates random passes.
## sleep_suite
Contains two suites, that generates also timedata for log.

`Behavior-driven.robot` Behavior-Driven sleep tests.

`sleeper.robot`         Data-Driven sleep tests.
## top_suite
Upper suite for some basic tests.

`Data-Driven.robot`     Example of Data-Driven design on tests.

`Failing_tests.robot`   Three test that produces fail.

`Logging.robot`         Example of different types of logging.

`Passing_tests.robot`   Pass and use things.
### lower_suite
Child suite for top_suite

`documents.robot`       Test generating documentation.

`embedded.robot`        Embedded example tests.

`empty.robot`           "Stupid" tests that pass, but teardown breaks.

`tagging.robot`         Example tests doing tagging.

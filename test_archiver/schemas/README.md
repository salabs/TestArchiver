# What is archived?

Since the TestArchivers data model mostly follows the data model of Robot Framework, this generic model mapping also works as the model mapping for the Robot Framework in general.

## Test items

### Test run

Each test set execution or parsed output file is mapped as a test_run in the database. Each test run receives a unique id and is fingerprinted so that each test run can only be insert once. All result items have a reference to a test run that they belong to. Test runs have some metadata:

-   `imported_at` timestamp when the test run was imported to the archive
-   `archived_using` the archiver method used to import the data (i.e. Parser type or listener)
-   `archiver_version` version of the archiver that was used to import the results
-   `generator` metadata on the tool that produced the parsed output file (for Robot Framework the the robot and python version that were used to produce the output.xml)
-   `generated` timestamp when the parsed output file was generated
-   `rpa` boolean whether the execution was actually a RPA (Robotic Process Automation task). This is mainly applicable to Robot Framework.
-   `dryrun` boolean whether this execution was actually a dryrun and not real tests against any system under test
-   `ignored` boolean whether this run is for some reason or another ignored as invalid results and therefore by default should be hidden from most APIs

### Test series

Test series are used to collect test results into series of builds that comprise of the actual test runs. A test series can correspond to a CI job, version control branch, release or any other meaningful sequence of consecutive execution of a set test cases.

-   `id`
-   `name`
-   `team`

### Builds

Builds are sets of the runs that are mapped to some test series with a specific build number.

-   `build_number` every build uses either the build number specified when the results where archived or automatically assigned by the archiver when not specified. The build number should form an increasing series for one test series but may skip values. Ideally these should
-   `build_id` a possible identifier string of the build, ideally allows for mapping the builds for example to the builds in a CI environment
-   `test_runs`

### Suite

Suites are collections of test cases that contain other subsuites or test cases. The suites can have their own setups and teardowns. The suites usually represent the folders in the test code directory. In test archiver each suite is supposed to receive its own unique id based on the `full_name` and the source `repository`. The for most frameworks (like Robot Framework) the full name is the full path of parent suite names joined by `.` characters.

Suite fields:

-   `id`
-   `name`
-   `full_name` fully identifiable suite path of this suite
-   `repository` used to identify suites that have have otherwise completely same full_name but coming from e.g. different projects

### Test case

Test case fields:

-   `id`
-   `name`
-   `full_name` fully identifiable name at least in the context of the parent suite but often (e.g. Robot Framework) the name prefixed by the full name of the parent suite
-   `suite_id` points to the parent suite containing the test case

### Result objects (for both suites and test cases)

For both suites and test cases the result objects contain the start_time, status, fingerprint and elapsed time. The status, fingerprint and elapsed time are also presented separately for the setup execution, actual test case execution and teardown execution when that kind of data is available from the frame work.

Result fields are:

-   `status` General status of the item

-   `setup_status` status of the possible setup

-   `execution_status`  status of the actual test execution or the combined status of the subsuites or test cases of a suite

-   `setup_status` status of the possible teardown

-   `setup_fingerprint` fingerprint of the keyword tree of the item setup (see: Fingerprints and keyword tree)

-   `execution_fingerprint` fingerprint status of the actual test execution or the combined fingerprint of the subsuites or test cases of a suite (see: Fingerprints and keyword tree)

-   `teardown_fingerprint` fingerprint of the keyword tree of the item teardown (see: Fingerprints and keyword tree)

-   `fingerprint` Fingerprint of the result, hash calculated from the combination of item name and subfingerprints

-   `execution_path` Execution path of the result i.e. where in the execution tree of the test run the item was executed. E.g. `s1-s2-t3` means the third test in the second subsuite of the top suite.

-   `start_time` timestamp

-   `elapsed` total time of the item execution (milliseconds)

-   `setup_elapsed` total time of the item setup (milliseconds)

-   `execution_elapsed` total time of the actual test execution or the combined elapsed time of the subsuites or test cases of a suite (milliseconds)

-   `setup_elapsed` total time of the item setup (milliseconds)

-   `critical` whether the test is critical or not (boolean, Robot Framework specific null in other cases)

### Data linked to results objects

-   `log_messages` timestamp, log_level, execution path and message string up to 2000 characters

-   `test_tags` tags set for the test case

-   `suite_metadata` name-value pairs that are tied to specific suites. Metadata for the top level suite is considered related to the entire test run.

## Fingerprints and Keyword trees

Tests usually consist of steps that can consist of substeps that form a tree structure. For each of these trees, TestArchiver calculates sha1 fingerprint that represents that particular subtree. In the case of Robot Framework the tree for keywords (that represent the substeps of the execution) is calculated from:

-   keyword name
-   library
-   status
-   arguments
-   fingerprints for sub keywords called

How the fingerprints are calculated for other frameworks depends on what data of the substeps is available. For many frameworks there are no substeps reported when the test cases passes but when failures occur the fingerprint of that error is usually used.

The fingerprints can be used to compare executions of test cases. When the fingerprints differ between two consecutive executions of the same test case we can infer that the execution of the test case changed some how. On the other if two executions of a test case fail with the same fingerprint, the test encountered a similar problem (possibly the same issue).

## Schema versioning
From version 2.0.0 onwards the tool will manage and enforce that the schema version of the database matches that of the archiver. The tool can perform the schema updates when explicitly allowed. But in most cases it is recommended to run the updates manually using the `database.py` script. The schema version and all the updates performed are recorded to `schema_updates` table. The updates are categorized to major and minor updates and allowing each type of update is handled separately. Minor (`--allow_minor_schema_updates`) updates should only include changes that keep the database compatible to anyone reading the archive. Major (`--allow_major_schema_updates`) updates can include changes that can be incompatible to services reading the database.

```
python3 test_archiver/database.py --database test_archive.db --allow-major-schema-updates
```

# Fixture Robot Framework tests

The fixture tests are used to generate test data for the archiver and the same test data is assumed by the [archiver API server](/archive_api_server) tests. Here you can find the documentation on how these test outputs are mapped to the archivers data model. The script [run_fixture_robot.sh](/run_fixture_robot.sh) executes the Robot Framework [fixture test set](/robot_tests/) 10 times and parses those results in to a test database.

## Test runs to builds mapping

Fixture test set is executed 10 times. Once using the Robot Listener and then 9 times using the parser.

| Series name               | Fixture | Robot listener | Parser | All builds |
| ------------------------- | ------- | -------------- | ------ | ---------- |
| **Test run/build number** |         |                |        |            |
| Run1                      | 1       | 1              | -      | 1          |
| Run2                      | 2       | -              | 1      | 2          |
| Run3                      | 3       | -              | 2      | 3          |
| Run4                      | 4       | -              | 3      | 4          |
| Run5                      | 5       | -              | 4      | 5          |
| Run6                      | 6       | -              | 5      | 6          |
| Run7                      | 7       | -              | 6      | 7          |
| Run8                      | 8       | -              | 7      | 8          |
| Run9                      | 9       | -              | 8      | 9          |
| Run10                     | 10      | -              | 9      | 10         |

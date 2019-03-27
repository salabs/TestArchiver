# TestArchiver
TestArchiver is a tool for archiving your test results to a sql database.

# Supported databases

## Sqlite
[SQLite](www.sqlite.org) default database for the archiver and is mainly useful for testing and demo purposes. Sqlite3 driver is part of the python standard library so there are no additional dependencies for trying out the archiver.

## Postgresql
[Postgresql](www.postgresql.org) is the currently supported database for real projects. For accessing Postgresql databases the script uses psycopg2 module: `pip install psycopg2`


# Basic usage with Robot Framework

## With output parser
The robot output.xml files can be imported using `test_archiver/output_parser.py`.

```
python3 test_archiver/output_parser.py --database test_archive.db output.xml
```
This will create a SQLite databse file named `test_archive.db` that contains the results.

For list of other options: `python3 test_archiver/output_parser.py --help`

## With listener
The project includes a listener that allows archiving the results using Robot Frameworks [Listener interface](http://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#listener-interface)
```
robot --pythonpath /path/to/test_archiver/ --listener ArchiverListener:test_archive.db:sqlite3 my_tests.robot
```
This will create a SQLite databse file named `test_archive.db` that contains the results.

`ArchiverListener:DBNAME:DBNEGINE[:DBUSER[:DBPASSWORD[:DBHOST:[DBPORT]]]]`

## Useful metadata and test series
There are some meta data that is useful to add with the results.

### Test series
The results can be organized in different series. By default if no series is specified the results are linked to an autoincrementing default series. Each test run can belong to one or more test series. The series can also be differentiated by team name.

For example when the test are run in Jenkins builds, the metadata from the build can be used as a series.

With ouput_parser `--team A-Team --series JENKINS_JOB_NAME#BUILD_NUMBER`

With listener by using robots metadata `--metadata team:A-Team --metadata: series:JENKINS_JOB_NAME#BUILD_NUMBER`

# What is archived?
## From Robot Framework

A simple overview:
- Test cases and Suites
  * Status (including individual statuses for setup, execution and teardown)
  * Execution time
  * Hashes for the keyword execution trees
- Log messages
  * Log levels can be excluded
  * up to 2000 chars
- Test tags
- Suite metadata
- Different keyword execution trees
  * Can be disabled
  * The hash is calculated from:
    - keyword name
    - library
    - status
    - arguments
    - hashes for sub keywords called

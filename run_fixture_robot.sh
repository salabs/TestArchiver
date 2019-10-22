#!/bin/bash

# This script is used to run and archive the Robot Framework fixture test that
# are also used as the test data for the archiver API server.

DB_NAME="fixture_archive"
DB_USER="robot"
DB_PASSWORD="robot"
DB_HOST="localhost"
DB_PORT=5432

PYTHONPATH="robot_tests/libraries:robot_tests/resources:test_archiver"

# Comment this if you would like to run the fixture tests with sleeps
# that are useful as more interesting running time data
EXCLUDE_SLEEP="--exclude sleep"

###############################################################################

psql -c "DROP DATABASE ${DB_NAME};"
psql -c "CREATE DATABASE ${DB_NAME} OWNER robot;"

echo "----------------------------------------"
echo " First archive one round of robot tests with a listener"
echo "----------------------------------------"

robot --listener ArchiverListener:${DB_NAME}:postgresql:${DB_USER}:${DB_PASSWORD}:${DB_HOST}:${DB_PORT} \
      --pythonpath ${PYTHONPATH} ${EXCLUDE_SLEEP} \
      --outputdir robot_tests/run1 \
      --metadata team:"TestArchiver" \
      --metadata series:"Robot listener" \
      --metadata series2:Fixture#1 \
      robot_tests

for RUN in 2 3 4 5 6 7 8 9 10
do
  echo "----------------------------------------"
  echo " Run robot tests and and archive with parser (${RUN}/4)"
  echo "----------------------------------------"
  robot --pythonpath ${PYTHONPATH} ${EXCLUDE_SLEEP} \
        --outputdir robot_tests/run${RUN} \
        robot_tests

  python3 test_archiver/output_parser.py robot_tests/run${RUN}/output.xml \
          --database ${DB_NAME} --user ${DB_USER} --dbengine postgresql \
          --team "TestArchiver" --series Fixture#${RUN} --series "Parser"
done

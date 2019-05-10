ALTER TABLE suite_result ADD column setup_elapsed int;
ALTER TABLE suite_result ADD column execution_elapsed int;
ALTER TABLE suite_result ADD column teardown_elapsed int;

ALTER TABLE test_result ADD column setup_elapsed int;
ALTER TABLE test_result ADD column execution_elapsed int;
ALTER TABLE test_result ADD column teardown_elapsed int;
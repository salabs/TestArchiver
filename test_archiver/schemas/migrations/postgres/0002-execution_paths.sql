-- Adds columns to record execution paths
ALTER TABLE suite_result ADD COLUMN execution_path text DEFAULT NULL;
ALTER TABLE test_result ADD COLUMN execution_path text DEFAULT NULL;
ALTER TABLE log_message ADD COLUMN execution_path text DEFAULT NULL;

INSERT INTO schema_updates (schema_version, applied_by)
VALUES (2, '{applied_by}');

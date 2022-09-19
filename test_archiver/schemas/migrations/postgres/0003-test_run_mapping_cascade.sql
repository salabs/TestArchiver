-- 1. -----------------
-- Adds ON DELETE CASCADE for test series mappings
ALTER TABLE test_series_mapping
DROP CONSTRAINT test_series_mapping_series_fkey,
ADD CONSTRAINT test_series_mapping_series_fkey
   FOREIGN KEY (series)
   REFERENCES test_series(id)
   ON DELETE CASCADE;

ALTER TABLE test_series_mapping
DROP CONSTRAINT test_series_mapping_test_run_id_fkey,
ADD CONSTRAINT test_series_mapping_test_run_id_fkey
   FOREIGN KEY (test_run_id)
   REFERENCES test_run(id)
   ON DELETE CASCADE;

-- 2. -----------------
-- Udate tree_hierarchy table call index as integer as it should be
ALTER TABLE tree_hierarchy
ALTER COLUMN call_index SET DATA TYPE int USING call_index::int;


INSERT INTO schema_updates (schema_version, applied_by)
VALUES (3, '{applied_by}');

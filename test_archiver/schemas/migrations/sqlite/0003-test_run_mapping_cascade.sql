-- 1. -----------------
-- Adds ON DELETE CASCADE for test series mappings
-- Only approach with SQLite3 is to rewrite the table definition
PRAGMA writable_schema=1;
UPDATE sqlite_master SET sql=
'CREATE TABLE test_series_mapping (
    series int REFERENCES test_series(id) ON DELETE CASCADE,
    test_run_id int REFERENCES test_run(id) ON DELETE CASCADE,
    build_number int NOT NULL,
    build_id text,
    PRIMARY KEY (series, test_run_id, build_number)
);'
WHERE type='table' AND name='test_series_mapping';
PRAGMA writable_schema=0;

-- 2. -----------------
-- Udate tree_hierarchy table call index as integer as it should be
CREATE TABLE new_tree_hierarchy (
    fingerprint text REFERENCES keyword_tree(fingerprint),
    subtree text REFERENCES keyword_tree(fingerprint),
    call_index int,
    PRIMARY KEY (fingerprint, subtree, call_index)
);
-- Old data to copy of table
INSERT INTO new_tree_hierarchy(fingerprint, subtree, call_index)
SELECT fingerprint, subtree, CAST(call_index AS INTEGER)
FROM tree_hierarchy;
-- Drop old table and rename the new
DROP TABLE tree_hierarchy;
ALTER TABLE new_tree_hierarchy RENAME TO tree_hierarchy;


INSERT INTO schema_updates (schema_version, applied_by)
VALUES (3, '{applied_by}');

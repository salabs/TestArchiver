-- Start versioning the schema and record updates
CREATE TABLE schema_updates (
    id integer PRIMARY KEY AUTOINCREMENT,
    schema_version int UNIQUE NOT NULL,
    applied_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    initial_update boolean DEFAULT false,
    applied_by text
);
-- Pre 2.0 Schema is version 0
INSERT INTO schema_updates (schema_version, initial_update, applied_by)
VALUES (0, 1, '{applied_by}');

-- Add schema_version column to test_runs.
-- Makes the schema incompatible for older versions of TestArchiver on purpose.
ALTER TABLE test_run ADD COLUMN schema_version int DEFAULT 0;
CREATE TABLE temp_test_run (
    id integer PRIMARY KEY AUTOINCREMENT,
    imported_at timestamp DEFAULT CURRENT_TIMESTAMP,
    archived_using text,
    archiver_version text,
    generator text,
    generated timestamp,
    rpa boolean,
    dryrun boolean,
    ignored boolean DEFAULT false,
    schema_version int REFERENCES schema_updates(schema_version) NOT NULL
);
INSERT INTO temp_test_run SELECT * FROM test_run;
DROP TABLE test_run;
ALTER TABLE temp_test_run RENAME TO test_run;

-- Adds missing index for log_message table
CREATE INDEX test_log_message_index ON log_message(test_run_id, suite_id, test_id);

INSERT INTO schema_updates (schema_version, applied_by)
VALUES (1, '{applied_by}');

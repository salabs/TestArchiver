-- Adds new column that enables the archiver to set the build number
-- by some build id string (e.g. commit hash)
ALTER TABLE test_series_mapping ADD COLUMN build_id text;

-- Separates the archiver version and parser type to different columsn
ALTER TABLE test_run ADD COLUMN archiver_version text;
UPDATE test_run
SET archiver_version=substring(archived_using, '^.+(\d+.\d+.\d+)$'),
    archived_using=substring(archived_using, '^(.+)\d+.\d+.\d+$');

-- Fixes two annoying typos in the schema
ALTER TABLE keyword_statistics ADD COLUMN max_execution_time int;
UPDATE keyword_statistics SET max_execution_time=max_exection_time;
ALTER TABLE keyword_statistics DROP COLUMN max_exection_time;

ALTER TABLE keyword_statistics ADD COLUMN min_execution_time int;
UPDATE keyword_statistics SET min_execution_time=min_exection_time;
ALTER TABLE keyword_statistics DROP COLUMN min_exection_time;

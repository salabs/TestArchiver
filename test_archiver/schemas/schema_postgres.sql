CREATE TABLE schema_updates (
    id serial PRIMARY KEY,
    schema_version int UNIQUE NOT NULL,
    applied_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    initial_update boolean DEFAULT false,
    applied_by text
);
INSERT INTO schema_updates(schema_version, initial_update, applied_by)
VALUES (2, true, '{applied_by}');

CREATE TABLE test_series (
    id serial PRIMARY KEY,
    name text NOT NULL,
    team text NOT NULL
);
CREATE UNIQUE INDEX unique_test_series_idx ON test_series(team, name);

CREATE TABLE test_run (
    id serial PRIMARY KEY,
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

CREATE TABLE test_series_mapping (
    series int REFERENCES test_series(id),
    test_run_id int REFERENCES test_run(id),
    build_number int NOT NULL,
    build_id text,
    PRIMARY KEY (series, test_run_id, build_number)
);

CREATE TABLE suite (
    id serial PRIMARY KEY,
    name text,
    full_name text NOT NULL,
    repository text NOT NULL
);
CREATE UNIQUE INDEX unique_suite_idx ON suite(repository, full_name);

CREATE TABLE suite_result (
    suite_id int REFERENCES suite(id) ON DELETE CASCADE NOT NULL,
    test_run_id int REFERENCES test_run(id) ON DELETE CASCADE NOT NULL,
    status text,
    setup_status text,
    execution_status text,
    teardown_status text,
    start_time timestamp,
    elapsed int,
    setup_elapsed int,
    execution_elapsed int,
    teardown_elapsed int,
    fingerprint text,
    setup_fingerprint text,
    execution_fingerprint text,
    teardown_fingerprint text,
    execution_path text,
    PRIMARY KEY (test_run_id, suite_id)
);
CREATE UNIQUE INDEX unique_suite_result_idx ON suite_result(start_time, fingerprint);

CREATE TABLE test_case (
    id serial PRIMARY KEY,
    name text NOT NULL,
    full_name text NOT NULL,
    suite_id int REFERENCES suite(id) ON DELETE CASCADE NOT NULL
);
CREATE UNIQUE INDEX unique_test_case_idx ON test_case(full_name, suite_id);

CREATE TABLE test_result (
    test_id int REFERENCES test_case(id) ON DELETE CASCADE NOT NULL,
    test_run_id int REFERENCES test_run(id) ON DELETE CASCADE NOT NULL,
    status text,
    setup_status text,
    execution_status text,
    teardown_status text,
    start_time timestamp,
    elapsed int,
    setup_elapsed int,
    execution_elapsed int,
    teardown_elapsed int,
    critical boolean,

    fingerprint text,
    setup_fingerprint text,
    execution_fingerprint text,
    teardown_fingerprint text,
    execution_path text,
    PRIMARY KEY (test_run_id, test_id)
);

CREATE TABLE log_message (
    id serial PRIMARY KEY,
    execution_path text,
    test_run_id int REFERENCES test_run(id) ON DELETE CASCADE NOT NULL,
    test_id int REFERENCES test_case(id) ON DELETE CASCADE,
    suite_id int REFERENCES suite(id) ON DELETE CASCADE NOT NULL,
    timestamp timestamp,
    log_level text NOT NULL,
    message text
);
CREATE INDEX test_log_message_index ON log_message(test_run_id, suite_id, test_id);

CREATE TABLE suite_metadata (
    suite_id int REFERENCES suite(id) ON DELETE CASCADE NOT NULL,
    test_run_id int REFERENCES test_run(id) ON DELETE CASCADE NOT NULL,
    name text NOT NULL,
    value text,
    PRIMARY KEY (test_run_id, suite_id, name)
);

CREATE TABLE test_tag (
    test_id int REFERENCES test_case(id) ON DELETE CASCADE NOT NULL,
    test_run_id int REFERENCES test_run(id) ON DELETE CASCADE NOT NULL,
    tag text  NOT NULL,
    PRIMARY KEY (test_run_id, test_id, tag)
);

CREATE TABLE keyword_tree (
    fingerprint text PRIMARY KEY,
    keyword text,
    library text,
    status text,
    arguments text[]
);

CREATE TABLE tree_hierarchy (
    fingerprint text REFERENCES keyword_tree(fingerprint),
    subtree text REFERENCES keyword_tree(fingerprint),
    call_index text,
    PRIMARY KEY (fingerprint, subtree, call_index)
);

CREATE TABLE keyword_statistics (
    test_run_id int REFERENCES test_run(id) ON DELETE CASCADE NOT NULL,
    fingerprint text REFERENCES keyword_tree(fingerprint),
    calls int,
    max_execution_time int,
    min_execution_time int,
    cumulative_execution_time int,
    max_call_depth int,
    PRIMARY KEY (test_run_id, fingerprint)
);

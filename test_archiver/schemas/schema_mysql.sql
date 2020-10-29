SET SESSION sql_mode = 'ANSI_QUOTES';
CREATE TABLE schema_updates (
    id serial PRIMARY KEY,
    schema_version int UNIQUE NOT NULL,
    applied_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    initial_update boolean DEFAULT false,
    applied_by varchar(200)
);
INSERT INTO schema_updates(schema_version, initial_update, applied_by) VALUES (2, true, '{applied_by}');

CREATE TABLE test_series (
    id serial PRIMARY KEY,
    name varchar(200) NOT NULL,
    team varchar(200) NOT NULL
);
CREATE UNIQUE INDEX unique_test_series_idx ON test_series(team, name);

CREATE TABLE test_run (
    id serial PRIMARY KEY,
    imported_at timestamp DEFAULT CURRENT_TIMESTAMP,
    archived_using varchar(200),
    archiver_version varchar(200),
    generator varchar(200),
    "generated" timestamp,
    rpa boolean,
    dryrun boolean,
    ignored boolean DEFAULT false,
    schema_version int NOT NULL REFERENCES schema_updates(schema_version)
);

CREATE TABLE test_series_mapping (
    series int REFERENCES test_series(id),
    test_run_id int REFERENCES test_run(id),
    build_number int NOT NULL,
    build_id varchar(500),
    PRIMARY KEY (series, test_run_id, build_number)
);

CREATE TABLE suite (
    id serial PRIMARY KEY,
    name varchar(200),
    full_name varchar(200) NOT NULL,
    repository varchar(200) NOT NULL
);
CREATE UNIQUE INDEX unique_suite_idx ON suite(repository, full_name);

CREATE TABLE suite_result (
    suite_id int NOT NULL REFERENCES suite(id) ON DELETE CASCADE,
    test_run_id int NOT NULL REFERENCES test_run(id) ON DELETE CASCADE,
    status varchar(20),
    setup_status varchar(20),
    execution_status varchar(20),
    teardown_status varchar(20),
    start_time timestamp,
    elapsed int,
    setup_elapsed int,
    execution_elapsed int,
    teardown_elapsed int,
    fingerprint varchar(100),
    setup_fingerprint varchar(100),
    execution_fingerprint varchar(100),
    teardown_fingerprint varchar(100),
    execution_path text,
    PRIMARY KEY (test_run_id, suite_id)
);
CREATE UNIQUE INDEX unique_suite_result_idx ON suite_result(start_time, fingerprint);

CREATE TABLE test_case (
    id serial PRIMARY KEY,
    name varchar(200) NOT NULL,
    full_name varchar(200) NOT NULL,
    suite_id int NOT NULL REFERENCES suite(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX unique_test_case_idx ON test_case(full_name, suite_id);

CREATE TABLE test_result (
    test_id int NOT NULL REFERENCES test_case(id) ON DELETE CASCADE,
    test_run_id int NOT NULL REFERENCES test_run(id) ON DELETE CASCADE,
    status varchar(50),
    setup_status varchar(50),
    execution_status varchar(50),
    teardown_status varchar(50),
    start_time timestamp,
    elapsed int,
    setup_elapsed int,
    execution_elapsed int,
    teardown_elapsed int,
    critical boolean,

    fingerprint varchar(100),
    setup_fingerprint varchar(100),
    execution_fingerprint varchar(100),
    teardown_fingerprint varchar(100),
    execution_path varchar(200),
    PRIMARY KEY (test_run_id, test_id)
);

CREATE TABLE log_message (
    id serial PRIMARY KEY,
    execution_path text,
    test_run_id int NOT NULL REFERENCES test_run(id) ON DELETE CASCADE,
    test_id int REFERENCES test_case(id) ON DELETE CASCADE,
    suite_id int NOT NULL REFERENCES suite(id) ON DELETE CASCADE,
    timestamp timestamp,
    log_level varchar(200) NOT NULL,
    message text
);
CREATE INDEX test_log_message_index ON log_message(test_run_id, suite_id, test_id);

CREATE TABLE suite_metadata (
    suite_id int NOT NULL REFERENCES suite(id) ON DELETE CASCADE,
    test_run_id int NOT NULL REFERENCES test_run(id) ON DELETE CASCADE,
    name varchar(200) NOT NULL,
    value text,
    PRIMARY KEY (test_run_id, suite_id, name)
);

CREATE TABLE test_tag (
    test_id int NOT NULL REFERENCES test_case(id) ON DELETE CASCADE,
    test_run_id int NOT NULL REFERENCES test_run(id) ON DELETE CASCADE,
    tag varchar(200)  NOT NULL,
    PRIMARY KEY (test_run_id, test_id, tag)
);

CREATE TABLE keyword_tree (
    fingerprint varchar(100) PRIMARY KEY,
    keyword text,
    library text,
    status text,
    arguments json
);

CREATE TABLE tree_hierarchy (
    fingerprint varchar(100) REFERENCES keyword_tree(fingerprint),
    subtree varchar(100) REFERENCES keyword_tree(fingerprint),
    call_index varchar(200),
    PRIMARY KEY (fingerprint, subtree, call_index)
);

CREATE TABLE keyword_statistics (
    test_run_id int NOT NULL REFERENCES test_run(id) ON DELETE CASCADE,
    fingerprint varchar(100) REFERENCES keyword_tree(fingerprint),
    calls int,
    max_execution_time int,
    min_execution_time int,
    cumulative_execution_time int,
    max_call_depth int,
    PRIMARY KEY (test_run_id, fingerprint)
);

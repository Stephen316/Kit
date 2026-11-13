CREATE TABLE settings (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
CREATE TABLE bindings (name TEXT PRIMARY KEY, sha256 TEXT NOT NULL);
CREATE TABLE resources (name TEXT PRIMARY KEY, available INTEGER NOT NULL CHECK (available IN (0,1)));
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    definition TEXT NOT NULL,
    definition_hash TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('queued','running','waiting_evidence','waiting_ci','waiting_application','completed','rejected','failed')),
    generation INTEGER NOT NULL DEFAULT 0,
    fingerprint TEXT,
    snapshot TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    parked INTEGER NOT NULL DEFAULT 0,
    next_run REAL NOT NULL DEFAULT 0,
    receipt TEXT,
    result TEXT,
    reason TEXT,
    worker TEXT,
    token_hash TEXT,
    lease_until REAL,
    deadline REAL,
    active_attempt INTEGER,
    created REAL NOT NULL
);
CREATE TABLE dependencies (
    job_id TEXT NOT NULL REFERENCES jobs(id),
    dependency TEXT NOT NULL,
    PRIMARY KEY (job_id, dependency)
);
CREATE TABLE attempts (
    id INTEGER PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    generation INTEGER NOT NULL,
    number INTEGER NOT NULL,
    fingerprint TEXT NOT NULL,
    worker TEXT NOT NULL,
    started REAL NOT NULL,
    ended REAL,
    outcome TEXT,
    receipt TEXT
);
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    at REAL NOT NULL,
    job_id TEXT,
    action TEXT NOT NULL,
    detail TEXT NOT NULL
);
CREATE INDEX jobs_ready ON jobs(state, next_run, created);
CREATE INDEX dependency_children ON dependencies(dependency);

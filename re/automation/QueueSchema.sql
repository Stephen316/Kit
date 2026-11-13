CREATE TABLE dirty (job_id TEXT PRIMARY KEY REFERENCES jobs(id));
CREATE TABLE job_inputs (job_id TEXT NOT NULL REFERENCES jobs(id), binding TEXT NOT NULL, PRIMARY KEY (job_id,binding));
CREATE TABLE job_resources (job_id TEXT NOT NULL REFERENCES jobs(id), resource TEXT NOT NULL, PRIMARY KEY (job_id,resource));
CREATE INDEX input_jobs ON job_inputs(binding,job_id);
CREATE INDEX resource_jobs ON job_resources(resource,job_id);
CREATE INDEX jobs_claim ON jobs(state,created,id);
CREATE INDEX jobs_leases ON jobs(state,lease_until,deadline);

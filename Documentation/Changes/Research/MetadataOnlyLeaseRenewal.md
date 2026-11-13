# Metadata-only controller lease renewal

## Behavior

The A03 controller renews leases without reading bound artifact contents inside its SQLite write transaction.
It checks the token, execution deadline and current prerequisite digests.
Heartbeat output includes `artifact_bytes_hashed`, which remains zero for renewal.
It does not reconcile unrelated jobs.

Claims, result submission, status and explicit artifact reads retain full integrity verification.
A successful heartbeat does not attest that artifact contents are valid.
No schema migration is required, and schema version 3 remains unchanged.
The future A08a version-4 migration retains its planned scope.

## Usage and limits

The existing `heartbeat --lease FILE` command is unchanged.
Use `finish` to validate and submit a worker result.
Changed prerequisite identities, stale tokens and expired deadlines still prevent renewal.
See the [controller guide](../../Reference/Research/ResearchController.md) and [write-lock gotcha](../../Gotchas/Research/HeartbeatArtifactHashing.md).

## Verification

A remote process scenario binds a real 64 MiB input, claims a job and checks three renewals report zero hashed bytes.
It then corrupts the stored input and requires result submission to fail.
The existing recovery, invalidation, concurrency and lease scenarios remain enabled.
Source inspection and permitted static checks run locally without executing tests.
Exact-revision remote results belong in the step register and PR comments.

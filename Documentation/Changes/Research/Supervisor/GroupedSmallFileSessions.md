# Grouped small-file research sessions

A08b adds optional group protocol 1 to the research supervisor and A03 adapter.
A group runs 2–20 jobs in one physical process.
Every job retains its own lease token, generation, fingerprint, counted resources, outcome, result and accepted output manifest.
The controller still counts each logical job against `max_running`.

## Configuration and runner contract

A runner opts in with `group_protocol: 1` and an explicit `group_peak_memory_mib` floor.
The same command must also support the existing single-job `job.json` contract.
`group_limit_bytes` defaults to 1,048,576 and accepts 1–268,435,456 bytes.
The group must remain strictly below this aggregate limit.
The footprint counts each member separately, including its immutable definition, distinct bound input objects, dependency receipts/results and accepted dependency outputs.
Repeated hashes within one member count once; the same input used by two members counts twice.
Jobs without bound inputs remain single jobs.

All members must have identical `kind`, `tool_version` and `rule_version`.
The controller considers the oldest runnable job first and applies logical concurrency and resource capacities before issuing leases.
When that job cannot group, or the group memory estimate does not fit, the supervisor uses its existing single-job claim path.
A runner or adapter without the optional capability retains single-job operation.
A custom adapter that advertises `GroupClaimsVersion = 1` must provide `ClaimGroup`, `RenewGroup` and `FinishGroup`.
A boolean or unsupported version is rejected.

The worker receives `group.json` with `group_session_version: 1` and ordered paths such as `jobs/00/job.json`.
Each member directory contains its own version 1 `job.json`, `inputs/`, `work/` and `result.json`.
The physical session also has `work/`, logs and its process receipt.
Tokens remain in the supervisor's private claim directory and are absent from worker manifests.
Opaque numeric member paths avoid platform-specific job-name interpretation.

## Lease, output and failure handling

A03 renews members together in one controller process during execution and input preparation.
Group completion renews remaining leases during metadata reads and before each member's intake.
The finish command reads bounded member records once before publishing outputs and enforces a 256 MiB total declared output limit across the group.
Each member's outputs use the existing private-root, file-handle, digest and size verification.
An invalid member cannot supply another member's accepted output.
Valid members can finish while an invalid member retries.
For a shared nonzero process exit, each affected member stores the bounded tail from the physical session’s `stderr.log` before cleanup.
The [crash-tail gotcha](../../../Gotchas/Research/Supervisor/GroupedCrashTails.md) explains why the source must be shared.
Lease and execution deadlines still fence slow copies; renewal does not extend the execution deadline.

A crash, stop, stale lease, setup failure or invalid member result retries affected unfinished jobs singly.
The optional version 1 `group_solo` store extension records this decision against each job's generation and fingerprint.
The marker survives supervisor restart; changed evidence permits a new grouping decision.
Claim directories publish atomically before transaction commit, and recovery handles claims issued before a session starts.

CPU and process-memory budgets count the physical group once.
Adaptive stop accounting deduplicates physical session identities.
Only a group whose members all finish accepted and completed contributes one group-memory sample.
Group histories are separate for each actual size, 2–20, and separate from single-job history.
The explicit group memory floor always bounds learned group estimates from below.
Preclaim admission conservatively uses the largest group estimate across sizes and versions for the kind.
This can reserve more memory than a small group needs.

## Verification and limits

Local validation ran source AST parsing, pinned Black, Mypy, Pyright and repository Steering checks.
No tests or decoder reproductions ran locally.
The new remote process fixtures drive actual supervisor, controller, SQLite store and runner processes.
They cover 20-member caps, short leases, per-member accepted files, aggregate size and output limits, version boundaries, resource counts, single-job fallback, invalid capability declarations, stale input fencing, durable crash/restart retries, per-member durable crash stderr and physical memory/deadline accounting.
Remote results must be recorded on the tested commit before treating these cases as verified.

These fixtures use synthetic input bytes and verify the supervisor, controller and artifact intake through real process boundaries.
Calibration and the unattended pilot remain separate work.

The first macOS run at `6e2da255` stopped before process execution because the new fence module collided with an existing unpackaged pytest module. The new module is renamed to `GroupedFenceTests.py`; [the basename gotcha](../../../Gotchas/Ci/Collection/PytestBasenameCollision.md) links the failure. Both case selections and their assertions remain enabled.

The macOS gate at `3327f7fe` passed all fifty cases in 382.80 seconds, including fourteen grouped cases. [Hosted macOS gate](https://github.com/TryUniCAD/Kit/actions/runs/43673846094/job/132689552836)

The Windows process job selects the existing group-cap and group-crash cases. They verify the 20-member ceiling, separate accepted files and receipts, a real worker crash, and exactly one singleton retry per affected member. The fixture writes the same crash diagnostic bytes on each host.

At `edd09981`, the Windows job passed 54 cases, including the group-cap case. The group-crash case reached temporary-directory cleanup, where an open SQLite fixture reader prevented Windows from deleting the private ledger. The diagnostic readers now close their connections explicitly. Hosted verification of the corrected cleanup is pending. [Fixture gotcha](../../../Gotchas/Research/Supervisor/SqliteContextLeavesHandle.md) [Hosted job](https://github.com/TryUniCAD/Kit/actions/runs/43715564751/job/132816225586)

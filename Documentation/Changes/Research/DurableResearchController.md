# A03 durable evidence store and job controller

## Behavior and usage

Adds standard-library research orchestration under `re/automation/` on PR #94.
The [controller guide](../../Reference/Research/ResearchController.md) describes initialization, named evidence bindings, strict job records, claims, private lease files, heartbeats, results, waits, resources and reports.

SQLite persists transactional metadata with a rollback journal and full synchronization.
SHA-256 files preserve immutable definitions, snapshots, evidence, results and receipts.
Changed prerequisites invalidate dependent jobs and revoke stale tokens.
Reconciliation uses an adjacency queue rather than repeated pending-set scans; bounded batch submission avoids one full sweep per initial job.
Interrupted work recovers through bounded leases, retries and backoff.
Exclusive resource waits do not block unrelated offline work.

## Limits

This is the A03 controller protocol, not an autonomous CAD decoder or worker launcher.
It adds no model calls, application runtime, production research import, neutral schema change or native conversion support.
A02 capture qualification remains blocked separately.
Local single-host filesystem operation is required; the initial remote process target is Linux and Python 3.14.
Receipts bind execution records and bytes, not the truth of a worker's claim.

## Verification evidence

Python syntax and applicable pinned formatting/static type checks are inspected without executing tests locally.
New real-process coverage is added for restart, invalidation, retries, concurrent claims, exclusive resources, lease fencing, cycle rollback and corrupted artifacts.
The scaling case exercises a 10,000-job dependency chain through batch submission and subsequent commands.
The existing registered workflow-quality job runs these checks remotely; results and exact revisions are recorded in PR #94 comments.
Current-head CI and configured review must pass before publication readiness is claimed.
Merge-group product acceptance remains separate and deferred.

The [artifact rollback gotcha](../../Gotchas/Research/ArtifactPublicationOutlivesRollback.md) records the cross-boundary behavior.
Rendered documentation usability and full language conformance remain unverified.

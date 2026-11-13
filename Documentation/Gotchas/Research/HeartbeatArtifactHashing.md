# Heartbeat artifact hashing holds the write lock

## Expectation

Renewing a worker lease should require only bounded control metadata checks.
Large inputs should not add repeated payload reads to each renewal.

## Actual behavior

At `7f8a742511bbf07e40c3fde3b1b12f27c0d90e50`, `leased` called `verify_job` while holding `BEGIN IMMEDIATE`.
That path rehashed each distinct bound artifact, up to 256 MiB per input.
Its verification set lasted only for that command.
Other workers could wait for the write transaction during repeated payload reads.

The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4566107279) identifies the affected call chain.

## Workaround

Use metadata-only heartbeat renewal and retain payload verification at claims, result submission, status and explicit artifact access.
Heartbeat success is not an artifact-integrity claim.
Keep result submission mandatory before accepting a worker's result.
The [controller guide](../../Reference/Research/ResearchController.md) records this boundary.

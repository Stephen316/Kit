# Audit the merged rationale revision

## Purpose

PR #127 merged as `4b730a8ff92f2a63dfdf3c16566d835b79c04835` without a merge-group acceptance run.
Its PR workflow deferred the complete test suite and heavy security jobs.
The initial audit runs those same jobs against the exact merged revision in GitHub Actions.
Any necessary repair receives a new immutable input SHA and a fresh audit; original failures remain recorded.

## Execution

The audit uses the existing [queue workflow](../../../.github/workflows/MergeQueue.yml).
A push to `codex/rationale-merged-audit` starts the additional audit phase.
Every source checkout selects the full source SHA from `AuditSha`.
The planner verifies its checkout before collecting tests.
Scorecard also selects that SHA for its candidate scan.

All test modules execute afresh in the normal shard planner, shard runners, and completeness report.
The audit does not import accepted test results or publish a reusable test-result cache.
Recorded durations can still balance the shards.
The acceptance gate requires every test and security job to succeed.

The native PR and merge-group phases retain their existing gates, scanner commands, query suites, pins, and limits.
The audit branch does not run tests locally or change repository protections.
The audit harness belongs to its own PR for review.
It does not establish that a native queue accepted PR #127.

## Verification

The merged revision's ordinary push checks passed for rationale, steering, paths, imports, formatting, typing, and workflow policy.
The initial inventory confirmed that all acceptance and heavy security jobs were deferred on PR #127.
Remote audit results are recorded in the audit PR and its workflow run.
The first run found two blocking security findings, described in [the repair entry](PostMergeAuditRepairs.md).
The follow-up audit selects the triggering push's immutable `github.sha`.
That input includes the input-boundary repairs and the complete audit harness.
No tests ran locally.
Any failed job leaves the audit incomplete until its cause is repaired and verified.

See [queue operations](../../../MergeQueue.md) and [deferred reruns](../../Gotchas/Ci/Audits/DeferredQueueReruns.md).

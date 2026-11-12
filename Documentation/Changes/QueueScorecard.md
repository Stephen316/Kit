<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Merge queue enforcement and Scorecard repair

## Behavior

The queue's `Scorecard` job installs OpenSSF Scorecard 5.4.0 from its official Linux AMD64 release.
It verifies the archive's SHA-256 before extraction.
The CLI replaces `ossf/scorecard-action`, which rejects `merge_group` before analysis even with publication disabled.

The job runs all default repository checks.
It then scans the exact `merge_group.head_sha` with commit-compatible checks.
Both scans are required because commit mode omits repository-only checks.
The outputs are `Scorecard.sarif` and `ScorecardCandidate.sarif`.
Each output must contain a SARIF run.
The job prints the findings and fails on execution errors.
Findings retain the existing advisory treatment without a new score threshold.
The job does not publish results to the Scorecard API.

## Aggregate behavior

`CI Agg` includes queue workflow checks and their overall result.
It requires a reported `Merge queue acceptance` result.
Acceptance waits for its heavy jobs.
The aggregate waits for acceptance and static validation.
This dependency direction avoids a cycle.
Failures, unexpected skips, cancellations, timeouts, and missing or pending acceptance block the aggregate.

This repair originally required native reviewer reports on PR heads and during PR evidence reuse.
[The CI allowlist](CiReviewerExclusions.md) supersedes that behavior.

The immediate artifact-verification client also permits four retries for transient 404 responses.
The [publication record](ArtifactPublication.md) documents failures at metadata and ZIP download boundaries.
Permanent errors still fail verification.
Digest and provenance checks remain enabled.

## Configuration

No new secret is required.
The CLI reads the existing job token from `GITHUB_AUTH_TOKEN`.
`ENABLE_SARIF` enables its SARIF formatter.
The install step stores the version and archive digest together.
Update both for an authorized upgrade.

## Historical live settings

On 2026-11-10, the separate `Protect` ruleset update removed the direct native-review required status.
It required `Merge queue acceptance` and `CI Agg` from GitHub Actions app `15368`.
The update retained review rules, queue settings, bypass actors, and other rules.

Required statuses also apply to queue candidates.
A directly required app status can block a synthetic commit when that app never reports there.
The settings change was independent of the workflow PR merge.
The reporter's revised behavior required merge because it executes trusted base code.
These historical observations do not prove the current live settings.

## Recorded verification and limits

- The [original queue job](https://github.com/TryUniCAD/Kit/actions/runs/42899921136/job/130122848089) confirmed the Scorecard action failure.
- The investigation checked the [5.4.0 release and digest](https://github.com/ossf/scorecard/releases/tag/v5.4.0).
- It also checked [CLI commit filtering](https://github.com/ossf/scorecard/blob/v5.4.0/cmd/root.go).
- The investigator read back [ruleset 25490615](https://github.com/TryUniCAD/Kit/rules/25490615) after the update.
- [PR #42's queue run](https://github.com/TryUniCAD/Kit/actions/runs/42899921136) reported 26 blocking Python CodeQL findings.
- That run also reported an insecure XML import through dlint and acceptance failures for unsupported ZIP Zstandard compression.
- Those were failed queue results, not successful acceptance evidence.
- This enforcement repair did not remediate the separate source and runtime defects.
- Process-boundary coverage checks heavy failures, non-success conclusions, pending checks, reviewer identity, head matching, and the synthetic-commit exception.
- No local tests ran.
- PR CI checks workflow syntax, pins, and policies.
- Heavy scans require a merge-group candidate on the relevant revision.
- The original record left the new CLI path awaiting a successful live queue run.

See [queue operations](../../MergeQueue.md), [supported action events](https://github.com/ossf/scorecard-action#readme), and [CLI usage](https://github.com/ossf/scorecard/tree/v5.4.0#scorecard-command-line-interface).

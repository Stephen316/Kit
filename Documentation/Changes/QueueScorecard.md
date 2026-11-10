<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Merge queue enforcement and Scorecard repair

## Behavior

The merge queue's `Scorecard` job installs OpenSSF Scorecard 5.4.0 from its
official Linux AMD64 release, verifying the archive's SHA-256 before extraction.
The CLI replaces `ossf/scorecard-action`, whose event validation rejects
`merge_group` even when publication is disabled.

The job first runs every default repository check, then scans the exact
`merge_group.head_sha` with all commit-compatible checks. Commit mode alone
filters out repository-only checks, so both scans are required. It produces
`Scorecard.sarif` and `ScorecardCandidate.sarif`, validates that both contain a
SARIF run, and prints their findings. Execution failures fail the job. Findings
retain the existing advisory summary behavior without a new score threshold.
Results are not published to the Scorecard API. The stable `Scorecard` job and
its dependency in `Merge queue acceptance` remain in place.

`CI Agg` now includes the queue workflow's checks and overall result instead of
excluding them. It also requires a reported `Merge queue acceptance` result.
Acceptance waits only for its heavy jobs; the aggregate waits for acceptance
and static validation, avoiding a dependency cycle. Failures, unexpected skips,
cancellations, and timeouts block the aggregate; missing or pending acceptance
cannot pass.

For PRs, `CI Agg` additionally requires a successful native `Greptile Review`
check from app ID `867647` on the current head SHA. A matching name from another
app, an older head, or a test-merge SHA cannot satisfy it. Other review providers
remain excluded. Queue candidates do not need Greptile checks; reuse of PR
evidence checks the native result on each contributing PR's own head. This does
not change the configured reviewer or request another automated review.

The immediate artifact verification client also retries transient 404 responses
up to four times. [Repeated publication races](ArtifactPublication.md) occurred
at both metadata and ZIP download boundaries in this PR. Permanent errors still
fail verification, and every digest and provenance check remains enabled.

## Configuration

No new secret is needed. The CLI reads the existing job token from
`GITHUB_AUTH_TOKEN`; `ENABLE_SARIF` enables its SARIF formatter. The version and
archive digest live together in the install step. Update both when upgrading.

The live `Protect` ruleset was separately updated on November 10, 2026 to remove
the direct `Greptile Review` required status and require `Merge queue acceptance`
alongside `CI Agg`, both from GitHub Actions (`15368`). It retains review rules,
queue settings, bypass actors, and every other rule. GitHub applies required
status checks to queue candidates as well as PRs, so requiring a review app that
does not report on queue commits leaves them waiting indefinitely. This live
settings change is independent of merging the workflow PR.

The direct acceptance requirement is active now. The revised aggregate behavior
requires merging this PR because the reporter intentionally executes trusted
base code, not the PR's implementation.

## Verification and limits

- Confirmed the original action failure on [the queue candidate's Scorecard job](https://github.com/TryUniCAD/Kit/actions/runs/42899921136/job/130122848089).
- Verified the official [5.4.0 release and archive digest](https://github.com/ossf/scorecard/releases/tag/v5.4.0) and [CLI commit filtering](https://github.com/ossf/scorecard/blob/v5.4.0/cmd/root.go).
- Read back [live ruleset 25490615](https://github.com/TryUniCAD/Kit/rules/25490615) after the update: `CI Agg` and `Merge queue acceptance` are required; Greptile is not directly required on synthetic queue commits.
- Inspected [PR 42's completed queue run](https://github.com/TryUniCAD/Kit/actions/runs/42899921136): Python CodeQL reported 26 blocking findings, dlint reported an insecure XML import, and acceptance tests failed on unsupported ZIP Zstandard compression. These are genuine failed queue results, not evidence of successful acceptance. This enforcement repair does not remediate those separate source/runtime defects.
- Added process-boundary aggregation coverage for heavy-job and queue-workflow failures, non-success conclusions, pending checks, native Greptile identity and head matching, and the queue's Greptile exemption. These execute in PR CI, not locally.
- No local tests were run. PR CI verifies workflow syntax, pinning, and policies; heavy scans remain deferred until a merge-group candidate executes this revision.
- PR success does not prove queue acceptance. The new CLI path still needs a successful live queue run after this workflow is merged.

See [merge queue operations](../../MergeQueue.md), the [Scorecard Action's supported events](https://github.com/ossf/scorecard-action#readme), and [Scorecard CLI usage](https://github.com/ossf/scorecard/tree/v5.4.0#scorecard-command-line-interface).

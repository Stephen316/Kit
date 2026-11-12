<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Configurable PR reviewers

## Behavior

[ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json) is the
single source for requested reviewer identities, wake words, native report names,
and existing report-exclusion metadata. The `Reviewers` array includes both
requested integrations. Instructions, CI aggregation, and process-boundary
fixtures read that array without embedding provider identifiers.

A PR is ready only when every listed reviewer has successful native reports and
an actual `APPROVED` review on the current head, with every finding fixed or
answered with evidence. Missing, pending, failed, stale, or dismissed evidence
blocks readiness. A green check or comment does not replace approval. All other
applicable CI and independently enforced repository requirements must also pass.

The agent workflow requests each entry's exact `Comment` as a separate top-level
comment once per accepted head unless that reviewer already has a request or
review for that revision. Native queued runs count as existing requests on later
heads. It verifies the responding account/app and reviewed SHA separately for
every reviewer. Unconfigured fallbacks are not allowed.

## Configuration

To add a reviewer, append one object to `Reviewers` in the JSON:

- `Comment`: the exact, nonempty, single-line trigger accepted by the integration
- `AppId` and `UserId`: verified positive immutable GitHub identity IDs
- `AppSlug` and `UserLogin`: observed identity names for human verification
- `Checks`: exact native check names produced by that app on PR heads
- `Statuses`: exact native commit-status contexts produced by that user
- `Documentation`: optional official trigger documentation URL

Supply both report arrays, with at least one required report overall. Every
listed report must succeed; multiple contexts are an all-of requirement. Duplicate
reviewer accounts, duplicate triggers, invalid IDs, and invalid report names fail
configuration loading. Checks match app ID and head SHA; statuses match creator
ID and the commit queried from GitHub. The newest matching report determines its
state. Identity names, brands, numeric IDs, and triggers belong only in the JSON.

`ExcludedReports` preserves identities of other installed review-report providers;
those entries are not requested reviewers. Their existing integration-owned
settings remain in place. Adding metadata does not install or enable an app,
link a triggering account, or alter live GitHub protections. Historical generator
metadata uses the stable `DocumentationSources.InitialWiki` key so reordering
reviewer or exclusion arrays cannot change the recorded provenance.

The previously approved README badge and integration-owned settings remain preserved.
CODEOWNERS is removed as requested. Repository rules are managed independently;
removing the file does not edit live branch-protection settings.

## Verification and limitations

Process-boundary coverage runs the full aggregate in a Node subprocess for each
configured reviewer, exercising success, failure, non-success conclusions,
missing reports, pending reports, stale revisions, spoofed identities, and partial
multi-report results. Existing unrelated-CI and queue-acceptance cases remain.
All test execution belongs to remote PR CI; no tests were run locally.

The PR reporter executes trusted default-branch code through
`pull_request_target`. The new all-reviewer report requirement activates after
merge; this PR's own readiness is checked against every configured reviewer
separately. Approval remains a native review gate in the agent instructions,
not a duplicate approval workflow. Synthetic queue commits do not require PR
review reports, but PR evidence reuse rechecks every configured report on each
contributing PR head. Heavy acceptance remains deferred until authorized queue
enrollment.

## Earlier rollout verification

On [PR #72 at 04ec7acc6](https://github.com/TryUniCAD/Kit/pull/72/checks?sha=04ec7acc69efafb183be48e457b32c5a837cb882),
the configured check-based reviewer passed its native check and
[approved that head](https://github.com/TryUniCAD/Kit/pull/72#pullrequestreview-5869463309).
Both native reports from the configured status-based reviewer passed on the
same head. Its GitHub approval was absent for that revision when checked, so the
PR still awaited that approval. The integration had
[approved an earlier revision](https://github.com/TryUniCAD/Kit/pull/72#pullrequestreview-5869152905).
The earlier approval cannot satisfy the current-head requirement.

The native check app and status creator IDs matched the two configured
entries, and the check and commit statuses were attached to 04ec7acc6. Review
and report evidence must be refreshed after each push.

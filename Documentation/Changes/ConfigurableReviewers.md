# Configurable PR reviewers

## Behavior

[ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json) defines requested reviewer identities, exact request text, native report names, and report exclusions.
The `Reviewers` array includes requested integrations.
This change originally used that array in instructions, CI aggregation, and process-boundary fixtures.
[The CI allowlist](CiReviewerExclusions.md) supersedes the original aggregation behavior.

A ready PR requires successful native reports and an actual `APPROVED` review from every configured reviewer on the current head.
Fix every finding or answer it with evidence.
Missing, pending, failed, stale, or dismissed evidence blocks readiness.
A green check or comment does not replace approval.
All other applicable CI and independently enforced repository requirements must also pass.

The agent workflow submits each entry's exact `Comment` as a separate top-level comment.
Submit once per accepted head unless that reviewer already has a request or review for the revision.
Native queued runs count as existing requests on later heads.
Verify the responding account or app and reviewed SHA separately for every reviewer.
Unconfigured fallbacks are not allowed.

## Configuration

To add a reviewer, append one object to `Reviewers` in the JSON:

- `Comment`: the exact, nonempty, single-line trigger accepted by the integration
- `AppId` and `UserId`: verified positive immutable GitHub identity IDs
- `AppSlug` and `UserLogin`: observed identity names for human verification
- `Checks`: exact native check names produced by that app on PR heads
- `Statuses`: exact native commit-status contexts produced by that user
- `Documentation`: optional official trigger documentation URL

Supply both report arrays, with at least one required report overall.
Every listed report must succeed.
Duplicate reviewer accounts, duplicate triggers, invalid IDs, and invalid report names fail configuration loading.
Checks match app ID and head SHA.
Statuses match creator ID and the commit queried from GitHub.
The newest matching report determines its state.
Identity names, brands, numeric IDs, and triggers belong only in the JSON.

The configuration reader requires `ExcludedReports` to be an array. It is now empty.
The CI allowlist keeps automated review reports out of CI aggregation.
Adding metadata does not install or enable an app, link a triggering account, or alter live GitHub protections.
The [provenance record](../Reference/Provenance.json) references generator metadata at a fixed repository revision.

The previously approved README badge and integration-owned settings remain preserved.
The change removes CODEOWNERS as requested.
Repository rules are managed independently.
Removing the file does not edit live branch-protection settings.

## Verification and limitations

Process-boundary coverage runs the full aggregate in a Node subprocess for each configured reviewer.
It covers successful, failed, missing, pending, stale, spoofed, and partial reports.
Existing unrelated-CI and queue-acceptance cases remain.
All test execution belongs to remote PR CI.
No tests ran locally.

The PR reporter executes trusted base code through `pull_request_target`.
The report requirement applies when the configuration and reporter exist on that base.
The introducing PR's readiness is checked against every configured reviewer separately.
Approval remains a native review gate in the agent instructions.
The change does not add a duplicate approval workflow.
Synthetic queue commits do not require PR review reports.
PR evidence reuse rechecks every configured report on each contributing PR head.
Heavy acceptance remains deferred until authorized queue enrollment.

## Historical verification from PR 72

[PR #72 at 04ec7acc6](https://github.com/TryUniCAD/Kit/pull/72/checks?sha=04ec7acc69efafb183be48e457b32c5a837cb882) recorded successful reports from both configured reviewers.
The reviewer with a native check also [approved that head](https://github.com/TryUniCAD/Kit/pull/72#pullrequestreview-5869463309).
The reviewer with native commit statuses had no approval for that revision when checked.
Its [earlier approval](https://github.com/TryUniCAD/Kit/pull/72#pullrequestreview-5869152905) could not satisfy the current-head requirement.

The native app and status creator IDs matched the configured entries.
The check and commit statuses referred to `04ec7acc6`.
This historical record does not establish the current PR state.
Refresh report and review evidence after each push.

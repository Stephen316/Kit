<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Configurable PR reviewers

The Reviewers array in
[ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json)
defines every required reviewer. Each entry declares the app and account
identities, the exact top-level request, and the expected native checks and
commit statuses. Both entries from the configuration proposed in
[PR #74](https://github.com/TryUniCAD/Kit/pull/74) are enabled.

After opening a PR or publishing a revision, request each configured reviewer
once per head unless that reviewer already has a request or a review on that
revision. A PR is ready when every configured reviewer passes its listed
reports, submits a GitHub approval for the current head, and has no outstanding
findings. The GitHub ruleset and the merge queue evaluate their own required
checks separately.

To configure a reviewer, supply Comment, AppId, AppSlug, UserId, UserLogin,
Checks, and Statuses in a Reviewers entry. Include both report arrays and at
least one report. Keep other installed review integrations in ExcludedReports
if their reports should be excluded from the CI aggregate. Config changes
require the matching integration to be enabled and able to report on the repo.

For verification, match the native check app IDs, commit status creator IDs,
and GitHub review author IDs to the configured entries, then compare every
report and approval with the current head SHA.

## Observed verification

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

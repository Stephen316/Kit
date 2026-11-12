<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review provider exclusions

`Pull Request / CI Agg` separates general automated review reports from ordinary
CI. Provider identities now come only from `Reviewers` and `ExcludedReports` in
[ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json).
The shared reporter excludes general reports from those identities during PR,
merge-group, and evidence-reuse aggregation. PRs and PR evidence reuse explicitly
require every native check and status listed under `Reviewers` on the current PR
head. Synthetic queue candidates remain exempt from PR-only reviewer reports.

`ReviewProviders.cjs` matches verified immutable GitHub app IDs and bot user IDs.
Register provider identities only in the JSON. Names, logins, and URLs cannot
exempt a report. Unrecognized providers remain CI; all lint, type, policy,
security, acceptance, and external CI stays enforced.

Only `Reviewers` contains requested reviewers. `ExcludedReports` preserves
existing unrelated report exclusions without requesting those integrations.
Every requested reviewer must pass its native reports, submit an actual current-
head approval, and have all findings addressed before the agent calls a PR ready.
This does not install integrations or change repository protections.

PR aggregation uses trusted base code through `pull_request_target`, so reporter
changes take effect only after merging. Integration coverage runs the complete
reporter in a Node subprocess and verifies its summary and filesystem evidence
against API-shaped fixtures, including failing unrelated CI and every configured
reviewer's reports. Tests run only in remote CI.

See [merge queue operations](../../MergeQueue.md),
[configurable reviewers](ConfigurableReviewers.md), and the
[trusted-base gotcha](../Gotchas/README.md).

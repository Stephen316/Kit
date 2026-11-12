<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review provider exclusions

[The CI allowlist](CiReviewerExclusions.md) supersedes this provider-based implementation.

## Original behavior

`Pull Request / CI Agg` separates automated review reports from ordinary CI.
Provider identities come from `Reviewers` and `ExcludedReports` in [ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json).
The shared reporter excludes their general reports during PR, merge-group, and evidence-reuse aggregation.

The later [reviewer configuration](ConfigurableReviewers.md) defines explicit report requirements.
PR aggregation and PR evidence reuse require every native check and status listed in `Reviewers` on the current head.
Synthetic queue candidates do not need those PR-only results.

## Identity and limits

`ReviewProviders.cjs` uses verified immutable app and bot user identifiers.
Register provider identities only in the JSON.
Names, logins, and URLs cannot exempt a report.
Unrecognized providers remain CI.
Lint, type, policy, security, acceptance, and external checks remain enforced.

Only `Reviewers` defines requested reviewers.
`ExcludedReports` retains other report exclusions without requesting those integrations.
Review approval and findings remain separate readiness gates.
Each requested reviewer must pass its native reports and submit an actual approval on the current head.
All findings must be fixed or answered with evidence.
This change does not install or disable integrations or change repository protections.

## Recorded verification

PR aggregation uses trusted base code through `pull_request_target`.
Reporter changes take effect after merge.
The original integration coverage executes the reporter in a Node subprocess against API-shaped fixtures.
It checks summary and filesystem evidence, including unrelated CI failures and every configured reviewer's reports.
No local tests ran.
The original record left current-head CI and review pending until GitHub reported them.
See [merge queue operations](../../MergeQueue.md) and [the trusted-base gotcha](../Gotchas/Ci/TrustedBaseAggregation.md).

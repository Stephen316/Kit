<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review provider exclusions

`Pull Request / CI Agg` aggregates CI independently from automated review. Cubic,
Greptile, CodeRabbit, and the reviewer named in `ReviewBot.json` are excluded from
check runs and legacy commit statuses, regardless of their report state. The
shared reporter applies these general exclusions to PRs, merge groups, and evidence reuse.
The later [queue enforcement repair](QueueScorecard.md) adds one explicit exception:
PR aggregation and PR evidence reuse require the native `Greptile Review` check
from app ID `867647` on the current PR head. Queue candidates remain exempt from
that PR-only requirement. No other automated review report becomes CI.

`ReviewProviders.cjs` identifies the installed providers by verified GitHub app IDs
and bot user IDs, with exact app slugs and normalized bot logins as identity
fallbacks. Register additional review integrations in that file when introduced.
Unrecognized providers remain CI; check names and URLs cannot exempt a report.
Actual lint, type, policy, security, acceptance, and external CI remain enforced.

Read the exact review request from `ReviewBot.json`. Review approval and findings
remain separate readiness gates. This change does not install an integration,
disable existing integrations, or change repository protection requirements.

PR aggregation uses trusted base code through `pull_request_target`, so feature
branch reporter changes take effect only after merging. The integration coverage
executes the full reporter in a Node subprocess and verifies its summary and
filesystem evidence against API-shaped fixtures, including failing unrelated CI.
Tests run only in remote CI; no local tests were executed during implementation.
Remote CI and current-head review evidence remain pending until reported by GitHub.

See [merge queue operations](../../MergeQueue.md) and the
[trusted-base gotcha](../Gotchas/README.md).

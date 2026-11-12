<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review bot configuration and required skill activation

Review request instructions previously duplicated a provider-specific mention and
comment across agent guidance, skill metadata, and follow-up examples. Changing
reviewers required editing multiple files, and the skill exempted its own edits
from activation.

The original request pointed at a regular GitHub user rather than the installed app.
The sole review configuration is now `Reviewers` in
[ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json).
Each entry contains the exact `Comment`, verified identity, and required native
reports. Agents reload the array before requesting review and submit each comment
verbatim once per head unless that reviewer already has a request or review.
Every listed reviewer must pass and approve the current head. Other guidance
links to the JSON instead of duplicating names or triggers. See
[configurable reviewers](ConfigurableReviewers.md) for the current schema.

Both [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md) require activating
[standard-pr-practice](../../.agents/skills/standard-pr-practice/SKILL.md) before
every repository task, including investigation, documentation, and skill edits.
Activation applies relevant instructions without granting additional publication
or merge authority.

Reviewer identity, reviewed SHA, findings, approval, CI, and enforced repository
requirements remain independently verified. The configuration does not install apps, alter provider settings, or update live
branch protections. The reviewer-list update removes CODEOWNERS and makes report
requirements and exclusions consume the JSON. Existing provider configuration is documented separately in
[the queue guide](../../MergeQueue.md).

Verification: inspected the complete instruction diff and searched maintained
workflow guidance for duplicated trigger literals. No tests ran locally; remote
PR CI provides repository policy and skill verification. Merge-group acceptance
remains deferred until authorized queue enrollment.

<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Contribute a documented change

## Purpose

Submit a scoped change with its documentation, CI evidence, and configured review.
The canonical workflow is [standard-pr-practice](../../../.agents/skills/standard-pr-practice/SKILL.md).
The repository has one discoverable skill.

## Before you start

Read [AGENTS.md](../../../AGENTS.md), the skill, and its complete standards index.
Current user instructions override conflicting repository defaults.
Read the [gotchas](../../Gotchas/README.md) for the affected area.
Identify the repository, base branch, and task-owned worktree.
Preserve unrelated changes.

## Procedure

1. Create an isolated worktree and task branch.
2. Inspect the affected source and its public behavior.
3. Implement the complete scoped change.
4. Update the relevant task and reference pages.
5. Add a new [change entry](../../Changes/Index.md) for each repository addition.
6. Update navigation for new or moved guides. Update terminology when it changes.
7. Record each new [gotcha](../../Gotchas/README.md) in a separate file.
8. Format only the changed files with the required tools.
9. Inspect the outgoing diff and commit range.
10. Commit the task-owned files.
11. Push the branch with `--no-verify`.
12. Open a normal PR against the intended base.

Expected result: the PR contains a complete, reviewable change and its documentation.
PR creation does not authorize merge or queue enrollment.

## Review follow-up

Read each entry in `Reviewers` from [ReviewBot.json](../../../.agents/skills/standard-pr-practice/ReviewBot.json).
The array is the only source of reviewer identities, report names, and request text.
For each entry, post `Comment` verbatim as a separate top-level request.
Post once per accepted head unless that reviewer already has a request or review for the head.
Verify each responding account or app and reviewed SHA.
Address actionable findings, including top-level and advisory reports.
Answer false positives with specific evidence.

Missing or invalid configuration blocks readiness.
Do not guess a trigger or use an unconfigured fallback.
Report unavailable review evidence separately from independently enforced GitHub requirements.
Every configured reviewer must pass all its native reports and submit an actual `APPROVED` review on the current head.
Missing, pending, failed, stale, or dismissed evidence blocks readiness.

## Validation

Do not run tests locally.
This restriction includes collection, reproductions, and hooks that execute tests.
Unit tests are prohibited.
Use integration and acceptance coverage at real component boundaries.

Verify every applicable CI result on the current revision.
Keep PR checks distinct from deferred merge-group acceptance.
Follow [merge queue operations](../../../MergeQueue.md) after an authorized merge request.

## Documentation quality

Use the [writing rules](../../Standards/WritingRules.md).
Include prerequisites, steps, expected results, and failure recovery in task pages.
Use exact public API names in examples.
Do not add explanatory code comments or comment-oriented docstrings.
Preserve the exact license notice in new comment-capable files.

Use Python and `uv` for backend dependencies outside exempt workspaces.
Use React for frontend work.
Use project-owned PascalCase paths.
The `re/` exemption does not waive product acceptance.

## Completion evidence

Record the accepted head SHA, full CI inventory, each reviewer identity, reviewed SHAs, and mergeability.
Leave the PR open unless a verified administrator explicitly requested a merge.
Report any remaining external blocker with its evidence.

## Related information

- [Documentation review](../../Maintenance/Review.md)
- [Information plan](../../Maintenance/InformationPlan.md)
- [Publishing](../../Publishing.md)

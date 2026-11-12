<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Repository policy

## Purpose

This page summarizes contributor boundaries.
The authoritative workflow is [standard-pr-practice](../../../.agents/skills/standard-pr-practice/SKILL.md).
Read its complete standards index and applicable rules before changing the repository.

## Work isolation

Use an isolated worktree and a separate PR for each task.
Preserve user-owned changes.
Do not commit or push directly to the code repository's `main` branch.
Push task branches with `--no-verify`.
Run tests only in remote CI.
Unit tests are prohibited by repository policy.

## Documentation

Each repository addition requires a new [change entry](../../Changes/Index.md).
Update the related guide and navigation in the same PR.
Record new gotchas before completion.
Use the [writing rules](../../Standards/WritingRules.md) for maintained documentation.
Record standards gaps without claiming unsupported conformance.

Generated pages receive the same technical and language review as manual pages.
Do not overwrite maintained text with an unchecked export.
Preserve the provenance record and license notices.

## Review and CI

Read each entry in `Reviewers` from [ReviewBot.json](../../../.agents/skills/standard-pr-practice/ReviewBot.json).
Use its configured identity, report names, and exact `Comment` request.
Request each review once per accepted head unless that reviewer already has a request or review for the head.
Verify each responding account or app and reviewed SHA.
Address findings from top-level, inline, and advisory reports.
Missing or invalid configuration blocks readiness.
Do not guess a trigger or use an unconfigured fallback.

All applicable CI must pass on the current revision.
Reviewer approval and CI health are separate facts.
Every configured reviewer must pass all its native reports and submit an actual `APPROVED` review on the current head.
Missing, pending, failed, stale, or dismissed evidence blocks readiness.
Independently enforced repository requirements can add other blockers.
Report those requirements separately from unavailable review evidence.

## Merge queue

PR checks do not establish merge-group acceptance.
Heavy acceptance and security checks run on the queue candidate.
The checked-in queue configuration does not prove that live GitHub protections match it.
Inspect the live requirements before authorized enrollment.

Only an explicit merge request from a verified repository administrator authorizes queue enrollment or merge.
Keep every applicable check enabled.
Do not bypass failed or pending acceptance.

## Product acceptance

Production conversion must remain independent of CAD applications.
Output must not use unrelated donor bytes.
Lossless acceptance requires geometry, history, editability, and target-application evidence.
The research exemption under `re/` does not waive those product requirements.

## Related information

- [Contribution workflow](../Overview/Contributing.md)
- [Merge queue operations](../../../MergeQueue.md)
- [Security policy](../../../.github/SECURITY.md)
- [Documentation review](../../Maintenance/Review.md)

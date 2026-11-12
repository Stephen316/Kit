<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Review configuration and skill activation

## Problem

Review instructions duplicated the provider mention and trigger across several files.
A reviewer change required multiple edits.
The skill also exempted edits to itself from activation.
The original request named a regular GitHub user and did not invoke the installed app.
See [configurable reviewers](ConfigurableReviewers.md) for the corrected configuration.

## Change

The original change stored a single `Comment` in [ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json).
Other guidance links to that file.
Agents load the value before requesting review.
They submit it once per accepted head unless that head already has a request or review.

The current contribution policy requires a `Reviewers` array in that file.
Each entry defines its reviewer identity, native reports, and exact request.
An absent or invalid array blocks readiness.
See [review follow-up](../Reference/Overview/Contributing.md#review-follow-up) for the current evidence requirements.
See [configurable reviewers](ConfigurableReviewers.md) for the schema.

[AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md) require skill activation for every repository task.
This includes investigation, documentation, and skill edits.
Activation applies relevant instructions but does not grant additional publication or merge authority.

## Evidence boundary

Verify reviewer identity, reviewed SHA, findings, approval, CI, and enforced requirements separately.
Changing the request does not install an app or change provider settings.
The later reviewer-list update removes CODEOWNERS and reads report requirements and exclusions from the JSON.
It does not change live branch protections.
See [the queue guide](../../MergeQueue.md) for those separate controls.

## Recorded verification

The original change inspected the instruction diff and searched for duplicated trigger literals.
No local tests ran.
Remote PR CI verifies policy and skill structure.
Merge-group acceptance remains separate from PR evidence.

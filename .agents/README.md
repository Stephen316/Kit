<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Repository skill

[standard-pr-practice](skills/standard-pr-practice/SKILL.md) is the only
repository skill. Edit it directly; it is no longer generated from Kiro steering.
All previous coding, formatting, quality, security, architecture, CAD, frontend,
and design rules and resources are incorporated without abridgment in its
[complete standards index](skills/standard-pr-practice/references/Standards/Index.md).
A pinned manifest and byte-exact provenance archive cover all 102 original files;
remote CI verifies that no original bytes or resources disappear.
Codex and Claude Code must activate this skill before every repository task,
including investigation, documentation, and edits to the skill itself.

Read every entry in `Reviewers` from
[ReviewBot.json](skills/standard-pr-practice/ReviewBot.json), the only source of
reviewer identities, native report names, and exact request comments. Submit each
entry's `Comment` verbatim once per head unless that reviewer already has a
request or review for that head. Every configured reviewer must pass its native
reports and submit an actual current-head `APPROVED` review before the PR is
ready. Only an explicit
request from a verified repository administrator authorizes agent queue
enrollment, auto-merge, or merging.

See [merge queue operations](../MergeQueue.md) for CI phases and activation.

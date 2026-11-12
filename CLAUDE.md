<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Agent guidance

Follow [AGENTS.md](AGENTS.md). Agents MUST activate the repository's only skill,
[standard-pr-practice](.agents/skills/standard-pr-practice/SKILL.md), every time they
work on this repository, before any task, including investigation, documentation,
skill edits, implementation, and PR follow-up. Read every reviewer and its exact request comment
from the `Reviewers` array in the sole source of truth,
[ReviewBot.json](.agents/skills/standard-pr-practice/ReviewBot.json).

Every repository addition MUST include a new entry in `Documentation/Changes/` in the
same PR, update its index and the relevant guide, and link the entry in the PR.
Follow the full documentation rule in [AGENTS.md](AGENTS.md).

Read [Documentation/Gotchas/README.md](Documentation/Gotchas/README.md). If you discover a new
gotcha, unexpected API behavior, wrong assumption, or undocumented quirk while
working on this codebase, you MUST add it to that bullet list before finishing
your task. This is mandatory, not optional. Format: a short description of the
gotcha, what you expected vs what actually happened, and the fix or workaround.

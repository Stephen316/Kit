<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Contribution workflow

[AGENTS.md](../../../AGENTS.md) and [CLAUDE.md](../../../CLAUDE.md) route agents to the single canonical [standard-pr-practice skill](../../../.agents/skills/standard-pr-practice/SKILL.md). Read its standards index and the rules relevant to the change. Edit the canonical skill directly; the old Kiro steering generator and separate skill registrations were removed.

1. Use an isolated worktree and a scoped PR. Preserve user-owned changes and never write directly to `main`.
2. Implement the complete change and add a new [documentation entry](../../Changes/Index.md) in the same PR. Update the relevant guide and index.
3. Record every newly discovered gotcha in [the mandatory log](../../Gotchas/README.md), including expected behavior, actual behavior, and the fix or workaround.
4. Run permitted static formatting locally. Do not run tests locally, including collection, reproductions, or hooks that execute tests. Unit tests are prohibited; integration and acceptance checks run in CI.
5. Push with `--no-verify`, request the currently authorized automated reviewer once per head, and address all actionable findings. Current user instructions override conflicting repository reviewer defaults; unavailable review evidence must be reported separately from enforced GitHub requirements.
6. Verify all applicable current-revision CI and conflict-free state. PR checks do not prove merge-group acceptance. A verified administrator's explicit merge request is required before queue enrollment or merging; preserve every applicable acceptance gate and live protection.

Use Python and `uv` for backend dependencies outside the exempt workspaces, React for frontend work, the exact `HEADER_NOTICE` for new comment-capable files, and PascalCase project-owned paths. Do not add explanatory code comments or comment-oriented docstrings.

The `re/` tree is exempt from code standards but not from product acceptance. Production conversions must be self-contained, emit from first-principles format knowledge without unrelated donor bytes, and satisfy lossless parametric target-application verification.

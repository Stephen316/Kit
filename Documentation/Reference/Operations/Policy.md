<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Policy and governance

The authoritative workflow is [standard-pr-practice](../../../.agents/skills/standard-pr-practice/SKILL.md), reached through [AGENTS.md](../../../AGENTS.md) and [CLAUDE.md](../../../CLAUDE.md). Its [complete standards index](../../../.agents/skills/standard-pr-practice/references/Standards/Index.md) contains the preserved rules and conflict precedence. Agents must activate the skill before every repository task, including work on the skill itself. [ReviewBot.json](../../../.agents/skills/standard-pr-practice/ReviewBot.json) is the only source of truth for the review request comment and reviewer mention. The removed Kiro generator is not part of the current workflow.

## Repository gates

- Path policy checks PascalCase file stems, ASCII spelling, and directory density.
- Python checks cover formatting, lint, typing, explicit imports, and steering.
- SPDX, workflow pinning, workflow security, and preserved-standards checks protect repository metadata.
- `CI Agg` inventories applicable CI; reviewer status is separate.
- `Merge queue acceptance` defers heavy work on PRs and runs acceptance and heavy security analysis on merge-group candidates.

The checked-in [queue guide](../../../MergeQueue.md) describes intended operation. Live GitHub rulesets must be inspected before enrollment; this documentation does not prove that those settings are active or that every required gate is enforced. Never infer queue acceptance from green PR checks or alter protections to obtain a merge.

## Documentation and gotchas

Every repository addition requires a new [change entry](../../Changes/Index.md), relevant guide updates, and links in the PR. Discoveries must be recorded in [Gotchas](../../Gotchas/README.md) before finishing. Generated documentation receives the same review, source verification, naming, and licensing checks as manually authored content.

## Security and acceptance

Follow [SECURITY.md](../../../SECURITY.md) for reporting and [archive validation](../../../src/convert/adapters/freecad/Archive.py) for concrete input limits. Security scanners and structural policy checks establish different facts; neither proves that a target CAD application can load, edit, and rebuild a converted model.

Research exemptions are scoped to `re/`. Production output still requires [no CAD runtime](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoCadRuntime.md), [no donor blocks](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md), and [lossless parametric acceptance](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/LosslessTranslation.md).

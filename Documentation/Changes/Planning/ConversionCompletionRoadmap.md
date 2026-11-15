# Conversion completion roadmap and owned backlog

## Behavior

The [roadmap](../../../Roadmap.md) now orders the work from current production subsets to a complete conversion SDK.
It replaces the stale 22/100 score with a revision-bound format snapshot and observable milestones.
The [conversion backlog](../../Maintenance/ConversionBacklog.md) records stable task IDs, ownership boundaries, dependencies and exit conditions.
It separates active implementation, blocked evidence, future programme scope and available independent work.
Its dated inventory links all twelve inspected open PRs to their observed heads.

[AGENTS.md](../../../AGENTS.md) requires contributors to read and maintain those records.
The README, documentation index and information plan link the planning entry points.
The format-selection guide now includes the qualified public Fusion reader/writer and its limitations.
The [capability documentation gotcha](../../Gotchas/Authoring/CapabilityDocsCanLag.md) records the conflicting earlier statements.

## Usage

Read the roadmap for ordered milestones and the immediate critical-path action.
Read the backlog before claiming work or creating another implementation PR.
Refresh live PR state and the owning register before changing a task's status.
Record the owner, precise scope, dependency, delivery PR and exit evidence.
Keep PR #94's detailed programme status in its own register.

## Limitations

This is planning and documentation work.
It adds no decoder, writer, CAD acceptance, automatic tracker or user evaluation.
The inventory is a dated snapshot, not a live readiness dashboard.
The supported version and route matrix remains task B01.
The next conversion prerequisite remains B02's independent native Fusion readback on PR #94.
No merge, queue enrollment or wiki publication is requested.

## Verification

The author inspected production adapter sources and the maintained Fusion/SOLIDWORKS contracts at main `e04e7b78`.
The author read current GitHub metadata for twelve open PRs and pinned their observed heads in the backlog.
PR #94's source register at `25d9104c` supplies the programme boundary and next evidence dependency.
Prettier 3.6.2 passed for all nine changed Markdown files.
Static link inspection found all 134 relative Markdown targets present.
The full-tree path policy passed for 11,211 tracked paths, including the three new pages.
The staged diff passed `git diff --cached --check`.
No local tests, decoder experiments, CAD application runs or research worker executions were performed.
Remote CI and configured review remain separate evidence on this PR's accepted head.
Rendered documentation, accessibility, representative-user evaluation and full standards conformance were not assessed.

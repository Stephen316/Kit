# Research automation contributor instructions

These instructions apply to research automation work associated with PR #94.
Follow the root [agent guidance](../AGENTS.md) and the canonical [repository skill](../.agents/skills/standard-pr-practice/SKILL.md).
These repository instructions do not replace higher-priority system or user instructions.

Read the maintained [plan](../Documentation/Reference/Research/AutomationPlan.md) and [step register](../Documentation/Reference/Research/AutomationSteps.md) before work.
Use the existing `CadDocument` contract for both native readers and all destination writers.
Cross-format editable native acceptance governs conversion completion.
Same-format fixed points and model confidence do not substitute for that evidence.

The current authorization is documentation only.
Do not implement the controller, adapters, model extensions or application experiments until explicitly requested.
After implementation is authorized, claim a stable step ID and check existing ownership before editing shared files.
Use isolated task worktrees and separate normal implementation PRs, unless the user explicitly directs an existing target PR.

Post progress comments on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
Use the template in the step register.
Comment when claiming work, after meaningful progress or accepted pushes, and whenever verification fails or a blocker appears.
Post a handoff when work pauses or changes owner.
During sustained work, post a consolidated update at least once per working day.
Include the step ID, owner, exact revision, completed work, evidence, remaining work, blockers and next action.
Keep document status and PR evidence consistent.
Do not claim another contributor's work is complete without its required verification.

Default to deterministic research with models disabled.
Models may propose bounded hypotheses only when configured and authorized.
Keep raw evidence, known semantics, unknown fields and native acceptance distinguishable.
Never relax checks, mask unexplained spans or execute model-supplied shell commands to force progress.
Keep tests in remote CI under current repository rules.
Application workers remain isolated research oracles and never enter production conversion.

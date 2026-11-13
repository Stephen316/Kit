# Research automation contributor instructions

These instructions apply to research automation work associated with PR #94.
Follow the root [agent guidance](../AGENTS.md) and the canonical [repository skill](../.agents/skills/standard-pr-practice/SKILL.md).
These repository instructions do not replace higher-priority system or user instructions.

Read the maintained [plan](../Documentation/Reference/Research/AutomationPlan.md) and [step register](../Documentation/Reference/Research/AutomationSteps.md) before work.
Use the existing `CadDocument` contract for both native readers and all destination writers.
Cross-format editable native acceptance governs conversion completion.
Same-format fixed points and model confidence do not substitute for that evidence.

Use the step register as the only maintained record of implementation status and ownership.
The current user request authorizes reconciliation with the latest docs and remaining deterministic implementation on PR #94.
Claim the next runnable child step before editing and respect its evidence dependencies.
Missing capture qualification blocks dependent semantic claims, not independent saved-file integration.
Optional external model execution, model-run shell exceptions and proposed local tests require their explicit authorizations.
After implementation is authorized, claim a stable step ID and check existing ownership before editing shared files.
By explicit user instruction, keep all code, documentation and progress for A01–A16 on PR #94.
Do not open separate implementation PRs for this programme.
Use isolated task worktrees, fetch and verify the current PR head, preserve concurrent contributions and push normally to its existing `docs/automation-plan` branch in `Stephen316/Kit`.

Post progress comments on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
Use the template in the step register.
Comment whenever a change or stage starts, progresses meaningfully, completes, becomes blocked or is handed off.
Comment after every accepted push and failed verification.
A chat update or PR-body edit does not replace the top-level PR comment.
Post a handoff when work pauses or changes owner.
During sustained work, post a consolidated update at least once per working day.
Include the step ID, owner, exact revision, completed work, evidence, remaining work, blockers and next action.
Start each progress comment with the current step and its status so a reader can identify the active work immediately.
Keep document status and PR evidence consistent.
Do not claim another contributor's work is complete without its required verification.

Default to deterministic research with models disabled.
Models may propose bounded hypotheses only when configured and authorized.
Keep raw evidence, known semantics, unknown fields and native acceptance distinguishable.
Never relax checks, mask unexplained spans or execute model-supplied shell commands to force progress.
Keep tests in remote CI under current repository rules.
Application workers remain isolated research oracles and never enter production conversion.

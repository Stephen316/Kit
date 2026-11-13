# A01 neutral contract audit

## Decision

The [A01 audit](../Reference/Research/NeutralContractAudit.md) selects existing `CadDocument` interchange JSON as the neutral format.
It retains schema `1.0`, registered wire records, source provenance and explicit unresolved information.
A future separate research receipt records exact-source and capability evidence without replacing the neutral model.

## Scope and usage

The audit inventories current fields, adapter boundaries, demonstrated gaps G01–G09 and initial comparison profiles P01–P05.
It separates main capabilities from the pinned unmerged Fusion work.
Use it to prepare paired examples and later reader/writer mappings.
It defines independent acceptance requirements for both cross-format routes.
The [capability-presence gotcha](../Gotchas/Conversion/CapabilityPresenceIsNotSemanticCoverage.md) records a specific source-inspection finding.

This change introduces no schema field, codec, comparator, controller, runtime dependency or native conversion capability.
The audit completes the design deliverable only; its listed implementation gaps remain open.

## Verification evidence

Source inspection and AST field enumeration used main `52dbbe55ea1410b6bcf0ac153975b8c35fe37a3d` without importing SDK modules.
The Fusion branch comparison is pinned to `be3220e3fb2e07ef33ee264f300a20f2c7a4a137` in PR #92.
The author inspected neutral serialization, model validation, capability inference and native adapter boundaries.
Formatting, source-link and Git whitespace checks are recorded in PR #94 after execution.
No local tests, test collection or application experiments ran.
Remote CI, configured review and native acceptance remain distinct evidence.

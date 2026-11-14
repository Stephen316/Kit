# Fusion gives uploaded Kit designs new revision GUIDs

## Expectation

A native insert of an uploaded Kit design copies the revision GUIDs from the uploaded file.
A Kit root that copies the same GUIDs then matches a native insert exactly.

## Actual behavior

The native inserts of the three Kit files wrote revision GUIDs that are not in the uploaded files.

| Field in the inserting design | Native insert | `EmitAssembly` |
| --- | --- | --- |
| `ComponentInstance.lastSavedTargetRevisionGuid` | New GUID in all 3 inserts | Target `FusionComponent.revisionGuid` |
| `ACTRefdTable.CachedRevGuid` | New GUID in all 3 inserts | Target `ACTTable.RevisionGuid` |
| `ACTRefdTable.RevisionGuidForChangeType` | New GUIDs for 4 of 6 change types in each part, 1 of 6 in the subassembly | Target `revisionGuidForChangeType` |

The other change types kept the GUIDs of the uploaded file.

Fusion still accepted the Kit root with the copied GUIDs.
On the first open, both references resolved and neither was out of date.
Part A became out of date only after a real edit and a new version.

## Workaround

Copy the revision GUIDs from the uploaded target file, as `EmitAssembly` does.
Do not compare these GUIDs when you check a Kit root against a native insert.

## Evidence

- [Assembly authoring acceptance](../../../../../re/Fusion/LocalOracle/LinksConfigs/AsmAcceptance.json), key `acceptance`
- [Probe insert script](../../../../../re/Fusion/LocalOracle/LinksConfigs/ProbeAsmTargets.py)
- [Assembly authoring change](../../../../Changes/Fusion/Assembly/FusionAssemblyAuthoring.md)

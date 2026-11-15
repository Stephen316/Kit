# Fusion sketch binding capture

A02d fresh-process capture now records sketch constraint participants and dimension targets.
Preparation pins `FusionBindings.py` with the tool, shared helper, specification and control.
Each before-recompute and after-recompute observation contains its own point and curve roster.
Curve endpoints and constraint targets refer to that observation's roster.

The initial supported constraints are horizontal, vertical, coincident and midpoint constraints.
Linear and diameter dimensions record their native targets and parameter names.
Unsupported types, missing targets and ambiguous matches remain explicit unresolved evidence.
Shared curve endpoints retain their point references without inventing an additional constraint.

Use the [fresh-process capture procedure](FusionFreshProcessEvidence.md) to prepare a new run.
Previously committed measurements remain unchanged.
The new records do not establish supporting-face identity or qualify a captured pair.
Qualification still requires native observations, readback diagnostics and independent semantic adjudication.

Entity identities apply to one observation only.
The capture compares native objects rather than entity-token strings.
Autodesk documents the [constraint targets](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_CoincidentConstraint.htm),
[dimension targets](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchLinearDimension.htm)
and [token identity limitation](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_SketchEntity_entityToken.htm).

## Verification

Static syntax inspection and source review cover the new capture path.
Remote process coverage prepares a pinned P01 run and rejects P05 without launching Fusion.
Its current-revision result is pending.
No local tests were run.
The implementation host's Fusion bridge refused connections, and native UI initialization failed.
No native binding observation, fresh-process run or qualification result is claimed.

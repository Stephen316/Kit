# Fusion keeps the stored Form body until the form changes

## Expectation

A Form document stores the control cage in the `TSplines.BlobParts` TSM member. The converted body looks like a cache that Fusion rebuilds from the cage when it opens or recomputes the document. A writer could then omit the converted body, or write an approximate one.

## Actual behavior

Fusion 2706.1.17 does not rebuild the converted body on open or on `computeAll`. It refuses a Form document without the converted body. It accepts a stale converted body without a warning.

The probe changed the Z coordinate of grip 0 by 0.25 cm in the native plane and box controls. It changed the TSM member, the TSM text inside the converted BRep, or both. The `NoBrep` variants removed the `.smb` and `.smbh` members and kept all other members.

| Variant | Opens | Cage digest | Converted body | Form health |
| --- | --- | --- | --- | --- |
| Control | Yes | Control | Control | 0 |
| TSM member changed | Yes | Changed | Equal to control | 0 |
| Embedded TSM changed | Yes | Equal to control | Equal to control | 0 |
| Both changed | Yes | Changed | Equal to control | 0 |
| BRep members removed | No | None | None | None |

The body observation includes face, edge and vertex counts, area, volume and bounds. It stayed equal after `computeAll` and after an empty `startEdit` and `finishEdit`. The import of a `NoBrep` variant raised `RuntimeError: 2 : InternalValidationError : isSuccessfullyOpened && status.isOk()`.

The TSM member is the source of the editable cage. The stored BRep is the source of the body in all four variants. A change to the TSM text inside the BRep had no observed effect.

A real cage edit converts the form again. In the Form document acceptance, one vertex move changed the plane control area from 3.831410566653259 cm² to 3.75882224444742 cm².

## Workaround

Write the converted body for every Form feature. Make it the exact conversion of the cage in the TSM member. Do not use an approximate body, because Fusion shows it as healthy and keeps it. Kit's `CheckFormBreps` rejects a converted BRep whose embedded TSM program differs from the TSM member. `EmitParsed` runs this check, so Kit never writes such a body. `ReadDocument` does not run it, because Fusion opens these documents. The four files in `re/Fusion/LocalOracle/FormDocuments/Stale` therefore read, and their re-emission raises `ValueError`.

`ConvertGrid` gives the exact conversion of qualified open grid cages. `SwapGridCage` replaces the cage and the converted body of a document with the same grid layout. Kit refuses every other cage, because it has no exact conversion for it. The [converted surface gotcha](ConvertedSurfaceIsExact.md) shows that the stored surface is the face geometry.

## Evidence

- [Probe inputs](../../../../../re/Fusion/LocalOracle/FormDocuments/Stale/Preparation.json)
- [Native probe](../../../../../re/Fusion/LocalOracle/FormDocuments/Stale/Probe.json)
- [Probe script](../../../../../re/Fusion/LocalOracle/FormDocuments/ProbeStale.py)
- [Variant preparation](../../../../../re/Fusion/Reconstruction/FormDocuments/PrepareStale.py)
- [Form document acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/Acceptance/NativeAcceptance.json)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)

# Edited Form documents store a T-spline graphics world

## Expectation

A Form document saved after a control-point edit has the same graphics layout as the Form document before the edit. The graphics codec knew world kinds 0, 1 and 3.

## Actual behavior

Three edited Form archives store a group with world kind 2 in `OGS.BlobFolder/OGS/DefaultScene/world`. Kit raised `ValueError("Unsupported custom graphics world")` for them.

Kind 2 has the same level-of-detail layout as a BRep world but has no `ValidBody` flag.

| World kind | Leading flag | Layout |
| --- | --- | --- |
| 1 | `ValidBody` | Edge group, `EdgesCount`, edge levels, face group, `FacesCount`, face levels, `HasModelBox`, optional `ModelBox` |
| 2 | None | Edge group, `EdgesCount`, edge levels, face group, `FacesCount`, face levels, `HasModelBox`, optional `ModelBox` |

The same archives also store an `OpacityAttribute`. Its fields are `Absolute` as a bool and `Opacity` as a 32-bit float, after the base attribute fields.

## Workaround

Read kind 2 with `XferTSplineMut` into a `BrepWorld`. Write it back without a `ValidBody` flag. Require both the edge group and the face group.

All three edited archives now read and re-emit with an equal model. Their OGS members are byte-equal. Only the `.protein` material packages differ, because the material writer emits them in canonical form.

| Archive | Kind 2 groups | Result |
| --- | --- | --- |
| `re/Fusion/LocalOracle/TSpline/BoxEdited.f3d` | 1 | Model equal |
| `re/Fusion/LocalOracle/TSpline/PlaneEdited.f3d` | 1 | Model equal |
| `re/Fusion/LocalOracle/TSpline/SymmetricBoxEdited.f3d` | 1 | Model equal |

## Evidence

- [Slack census with the edited archives](../../../../../re/Fusion/Reconstruction/ActSlack/SlackCensus.json)
- [Edited world isolation](../../../../../re/Fusion/Reconstruction/FormDocuments/EditedWorlds.json)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)

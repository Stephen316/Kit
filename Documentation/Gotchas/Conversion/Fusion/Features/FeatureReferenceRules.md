# Feature references need fresh tags and a component scope

## Expectation

A replaced face can keep the entity tag of the face that it replaces.
A pick on the only body can use the body identifier as its reference scope.
Both forms keep the Design graph equal to the native graph apart from identifiers.

## Actual behavior

Fusion 2706.1.17 rejects both forms.
The first form prevents the document from opening.
The second form opens correctly but fails at the first recompute.

| Variant            | Changed rule                                  | Open result                                                       | `computeAll` result               |
| ------------------ | --------------------------------------------- | ----------------------------------------------------------------- | --------------------------------- |
| `FilletAccepted`   | None                                          | 23.961372 cm³, 7 faces                                            | 23.961372 cm³, healthy            |
| `FilletReusedTags` | A replacement face takes the deleted face tag | `InternalValidationError : isSuccessfullyOpened && status.isOk()` | Not reached                       |
| `ShellAccepted`    | None                                          | 7.152 cm³, 11 faces                                               | 7.152 cm³, healthy                |
| `ShellBodyScope`   | Pick scopes carry the body identifier         | 7.152 cm³, 11 faces                                               | 24 cm³, 6 faces, `Face 1 missing` |

Each opened variant showed the 24 cm³ box at the extrusion marker and the feature solid at the final marker.
The `ShellBodyScope` shell reports health state 1 with `1 Reference Failures` after `computeAll`.

A fillet trims two walls and both caps.
The writer stores a trimmed face as a deletion and an insertion when its draft key changes.
Native journals give an inserted face a new tag and keep a tag only through an `(old, new)` modification.

Native controls store the component `persistentId` in every reference scope.
A body identifier in that field does not change the stored geometry.
After `computeAll`, the shell cannot find its roof face and the body reverts to the extruded box.

## Workaround

Claim face tags by draft key in `TagLedger`.
A key that was absent from the previous state receives a fresh tag.
Store `Author.ComponentId` in every reference scope through `PartScope`.

`TestTagChains` and `TestRefScope` check both rules for every authored case.
The [regression generator](../../../../../re/Fusion/Reconstruction/FeatureAuthoring/RegressionVariants.py) restores each earlier rule in its own process.
The [native observation](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Regressions/Observation.json) preserves the evidence.

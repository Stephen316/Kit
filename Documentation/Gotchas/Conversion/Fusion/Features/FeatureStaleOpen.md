# Fusion shows the saved journal without a recompute

## Expectation

A writer could store only the parametric feature records and the base body.
Fusion appears able to rebuild later features from their saved inputs when it opens the document.

## Actual behavior

Fusion 2706.1.17 shows the stored BRep journal as the current model.
It does not compute a missing or stale feature state when the document opens.
Each timeline feature still reports a healthy state.

| Native control with a truncated journal | Opened volume (cm³) | Opened faces | Volume after `computeAll` (cm³) | Faces after `computeAll` |
| --------------------------------------- | ------------------: | -----------: | ------------------------------: | -----------------------: |
| `FilletWithoutFilletState`              |              24.000 |            6 |                       23.961372 |                        7 |
| `ChamferWithoutChamferState`            |              24.000 |            6 |                       23.910000 |                        7 |
| `ShellWithoutShellState`                |              24.000 |            6 |                        7.152000 |                       11 |
| `ExtrudeCutWithoutCutState`             |              24.000 |            6 |                       22.429204 |                        7 |
| `RectPatternWithoutPatternState`        |           23.434513 |            7 |                       20.607080 |                       12 |

Persisted dirty and update flags on the unsolved fillet did not change this result.
Five flag variants opened as the 24 cm³ box and became correct only after `computeAll`.

## Workaround

Emit the solved geometry for every timeline state.
Kit computes each fillet, chamfer and shell state with its own exact modeler before it writes the journal.
Do not depend on Fusion to repair a stale journal when the document opens.

The [truncated-journal observation](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Recompute/Observation.json) and the [dirty-flag observation](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Recompute/DirtyObservation.json) preserve the evidence.

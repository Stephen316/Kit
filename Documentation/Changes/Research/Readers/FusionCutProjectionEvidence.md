# Fusion P04 saved projected cap edges

The P04 archive command follows each of the four projected `CutSketch` lines to its source edge in the clock-qualified boss-cap view. It reads only the eleven discovery archives and historical measurements pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Run it with Python 3.14 or later. [Evidence command](../../../../re/automation/FusionCutProjectionEvidence.py), [Saved cap and journal evidence](FusionCutJournalEvidence.md)

```powershell
python -B re/automation/FusionCutProjectionEvidence.py > FusionCutProjectionEvidence.json
```

The sketch-owned automatic boundary controller `346` names output entry `354` and the sketch's verified face-selection proxy. Each entry binds one cached line to an output naming leaf. The leaf's complete stored edge recipe has unique byte equality with a named source-context edge recipe. The source descriptor, historical BODY anchor and feature owner agree with the independently mapped cap and `BlindBoss` clock. [Saved cut support cap](FusionCutFaceEvidence.md), [P04 projection markers](../../../Gotchas/Research/Readers/FusionCutProjectionMarkers.md)

Each edge recipe names two adjacent faces and two three-face endpoint operands. Exact complete name matches and reciprocal incidence on the selected cap identify one edge and both vertices. The four recipes cover all four cap edges exactly once. The resulting edge IDs below are original inspection-record indices of each archive's explicitly mapped `.smbh` member. The JSON retains dense chart indices, original record offsets and digests.

| Projected sketch line | Baseline A/B source edge | YZ source edge | Through-all source edge |
| --- | ---: | ---: | ---: |
| `381` | 112 | 113 | 167 |
| `384` | 130 | 131 | 180 |
| `387` | 155 | 156 | 173 |
| `388` | 132 | 133 | 158 |

Python 3.14.6 verified all 44 saved projection associations and all 88 directed endpoint pairs. The saved cap vertices and projected sketch points agree in world millimeters with the historical API's independently measured reference-line endpoints. Source selection uses exact recipe names and typed incidence before the geometry comparison.

The result identifies original serialized source edges within the earlier boss chart. The historical API measured reference geometry and did not capture the live `isLinked` or persistent source-edge identity getters. Fresh native link and identity roundtrips, general topology regeneration and editable acceptance remain open.

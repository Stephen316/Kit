# Fusion P04 saved boss and cut profiles

The P04 archive command uses the original eleven discovery captures pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54`. It verifies the original paired receipt and historical measurements, then joins the saved boss and cut profile owners to the two clock-qualified journal endpoints. Run it with Python 3.14 or later. [Evidence command](../../../../re/automation/FusionCutProfileEvidence.py), [Journal endpoint evidence](FusionCutJournalEvidence.md)

```powershell
python -B re/automation/FusionCutProfileEvidence.py > FusionCutProfileEvidence.json
```

The earlier endpoint's native feature selects `RectangleSketch` and its entire four-line outer loop. The later endpoint identifies `BlindCut` or `ThroughAllCut`. Its owned proxy and repeated descriptor independently name `CutSketch`. A reciprocal typed loop record and unique curve tags select lines `393`, `396`, `399` and `400`. The identity join comes from the feature records and clock-bound actor references. The reported record numbers are archive-local. [Saved body and sketch selection routes](FusionCutSelectionEvidence.md), [Historical sketch bindings](FusionCutSketchEvidence.md)

All four selected lines match the historical API's authored perimeter. Lines `381`, `384`, `387` and `388` match its projected reference boundary, and line `405` matches its construction diagonal. Those five lines stay outside the saved cut loop. The bounded geometry check gives the inner rectangle's area and the projected rectangle's area with the inner rectangle removed. Both values agree with the original API profile area inventory, including the independent size edits. [Fusion cut regions](../../../Gotchas/Research/Readers/FusionCutSketchRegions.md)

| Control | Selected cut area in mm² | Other measured region in mm² | Stored cut member order |
| --- | ---: | ---: | --- |
| Baselines | 80 | 720 | `400,396,393,399` |
| Boss-width edit | 80 | 800 | `400,396,393,399` |
| Boss-height edit | 80 | 880 | `400,396,393,399` |
| Cut-width edit | 96 | 704 | `400,396,393,399` |
| Cut-height edit | 100 | 700 | `400,396,393,399` |
| YZ | 80 | 720 | `400,399,393,396` |
| Through-all | 80 | 720 | `400,399,396,393` |

Python 3.14.6 verified the two profile joins in all eleven archives. The archive recipe selects the authored inner cut rectangle in both blind and through-all cases. The historical API measured sketch regions and line flags without a live selected-profile getter. The saved owner and loop records supply that selection evidence. The stored membership order, same-process measurement limits, projected line sources, fresh Fusion readback and editable acceptance retain their separate scope.

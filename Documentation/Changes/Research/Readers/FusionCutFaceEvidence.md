# Fusion P04 saved cut sketch support cap

The archived support study follows the owned P04 face recipe into its mapped ASM history blob. It uses the eleven discovery exports pinned at `89c25945f5833ad9c3a1c6c683df510b5702dd54` and cross-checks the placement against the original Fusion measurements. Run it with Python 3.14 or later. [Evidence command](../../../../re/automation/FusionCutFaceEvidence.py), [Saved selection provenance](FusionCutSelectionEvidence.md)

```powershell
python -B re/automation/FusionCutFaceEvidence.py > FusionCutFaceEvidence.json
```

In every archive, `CutSketch` owns bounded-face recipe `353`, which references the historical Body `309` through its face descriptor and anchor. Native collection `7` and mapping `8` name the same asset's `.smbh` member and bind Body `309` to stored handle `5`, initial ASM body record `1`. The explicit slot `0`, pointer-side `0` journal alias reaches one paired body with handle `5`, an identity body transform and six reciprocal faces and loops. The report retains the original serialized record indices and offsets alongside the dense indices used by the literal view.

The 476-byte recipe selects complete name group `0` before geometry is compared. Its five distinct face groups resolve within this body. Four two-face operands resolve four edges, and eight three-face endpoint operands resolve their vertices. The edge set exhausts the selected face’s single reciprocal loop. The other faces comprise four orthogonal side planes and one parallel cap on the boss profile plane. The selected analytic plane normal and reference axis agree with the saved sketch frame and the archived Fusion axes. The selected plane is offset from the boss profile by exactly the bound boss depth. [Bounded face incidence reader](../../../../re/Fusion/Study/decode_shell_reconstruction.py)

| Archived variant | Serialized `.smbh` face record | Dense literal face index | Plane point in cm | Plane normal | Boss depth in mm |
| --- | ---: | ---: | --- | --- | ---: |
| Baselines A and B | 199 | 98 | `[2, 1, 1]` | `[0, 0, 1]` | 10 |
| Boss-depth edit | 199 | 98 | `[2, 1, 1.2]` | `[0, 0, 1]` | 12 |
| YZ | 200 | 99 | `[1, 2, 1]` | `[1, 0, 0]` | 10 |
| Through-all | 196 | 96 | `[2, 1, 1]` | `[0, 0, 1]` | 10 |

Python 3.14.6 processed all eleven exact archives. In each, all five names also match the mapped initial geometry, where the four recipe edges fail to exhaust the cap’s loops. The separate `.smb` member has multiple owners for the selected name group in every archive. These controls require the typed body alias and reciprocal loop proof before accepting the name. [Fusion face names across history charts](../../../Gotchas/Research/Readers/FusionFaceNameAcrossHistoryCharts.md)

The result identifies the saved cap occurrence in this literal chart. The document-root study extends this evidence to world coordinates with the typed root occurrence and historical API sketch placement. Slot-to-feature chronology, a reopened Fusion API reference to this face, native participant-body meaning and editable acceptance remain open. [P04 document-world frame evidence](FusionCutWorldFrame.md)

# Fusion P04 document-world frame evidence

The P04 cut face report now resolves the document root and compares the saved cap and both sketch frames with the historical Fusion measurements. It reads the same eleven immutable discovery exports and original receipt as the cap study. Run it with Python 3.14 or later. [P04 saved cap evidence](FusionCutFaceEvidence.md)

```powershell
python -B re/automation/FusionCutFaceEvidence.py > FusionCutFaceEvidence.json
```

All eleven exports contain typed root occurrence `57`, a zero instance number, no parent and an identity transform. The root's repeated component references lead to Component `3`, which owns both sketch placements and native body collection `7`. The cap study binds that collection and Body `309` to the same-asset ASM body with its independently verified identity transform. The report retains the original indexed root and placement records, including byte ranges and digests.

The bounded occurrence reader has an opt-in used by this pinned report. Baseline A, YZ and through-all carry an explicitly empty attribute table. Baseline B, the six scalar edits and inch display carry the three previously typed gate attributes. Both forms store a literal `01` immediately before the first UUID. The report requires the two observed table shapes, validates the canonical root suffix and preserves the additional byte and its original offset in its evidence. [Root occurrence marker](../../../Gotchas/Research/Readers/FusionRootOccurrenceMarker.md)

The frame composition uses row-major matrices acting on column vectors. Position translations are stored in centimeters and compared with the historical API's measured world millimeters. Axes are unit vectors. Python 3.14.6 processed all eleven archives. All 22 sketch world frames match the independently recorded origins and directed X and Y axes. The saved cap normal and reference axis agree with the cut sketch Z and X axes, and the cut sketch origin lies on the selected cap plane in all archives.

| Archived variant | Cut sketch origin in world mm | Cap normal | Signed plane offset in mm |
| --- | --- | --- | ---: |
| Baselines A and B | `[0, 0, 10]` | `[0, 0, 1]` | 10 |
| Boss-depth edit | `[0, 0, 12]` | `[0, 0, 1]` | 12 |
| YZ | `[10, 0, 0]` | `[1, 0, 0]` | 10 |
| Through-all | `[0, 0, 10]` | `[0, 0, 1]` | 10 |

The evidence qualifies the saved document-world frame of the cap in the selected literal chart. The comparison uses the original same-process observations, with Baseline B measured before its repeat export. A journal-slot-to-feature chronology, fresh API face identity, participant-body behavior and native editable acceptance remain open.

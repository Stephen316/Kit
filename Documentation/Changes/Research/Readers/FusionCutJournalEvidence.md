# Fusion P04 saved journal endpoint actors

The P04 archive command compares the native Design timeline and its owned feature bookkeeping with the typed kernel journal. It uses the same eleven pinned P04 discovery exports, immutable measurement receipt and qualified same-asset body map as the support-cap report. [Evidence command](../../../../re/automation/FusionCutJournalEvidence.py), [Saved source cap](FusionCutFaceEvidence.md)

```powershell
python -B re/automation/FusionCutJournalEvidence.py > FusionCutJournalEvidence.json
```

Design history record `35` stores the feature sequence `207` (`RectangleSketch`), `277` (`BlindBoss`), `334` (`CutSketch`) and `446` (`BlindCut` or `ThroughAllCut`). All four names, feature types and positions agree with the original Fusion feature inventory. Each feature's typed `6CCF41D5` bookkeeping record has a reciprocal owner reference and a unique self entry whose `uint64` equals the owner-footer clock. The four stored clocks increase in Design timeline order. Shared-footer fields for suppression and rollback still report their original reader diagnostics.

In the mapped `.smbh` slot `0`, an explicit two-sided BODY pair connects the six-face literal source view and the mapped initial result geometry. The two `Timestamp_attrib_def` attributes have separate single-sided journal entries. Reciprocal BODY attribute chains place the side-0 timestamp on the literal source body and the side-1 timestamp on the initial geometry body. The exact integer-valued `float64` equals feature `277`’s clock on side `0` and feature `446`’s clock on side `1` in all eleven files. Thus the selected support cap belongs to the earlier boss endpoint of this saved pair, while the initial result endpoint carries the cut actor’s clock. The kernel’s traversal direction, a unique command event for the slot and persistent topology identity remain unassigned.

| Archive | Slot `0` left endpoint clock | Slot `0` right endpoint clock | Clock difference in inferred microseconds |
| --- | ---: | ---: | ---: |
| Baseline A | 1794686599326774 | 1794686599330576 | 3802 |
| Baseline B | 1794686599505983 | 1794686599510638 | 4655 |
| Boss-depth edit | 1794686599989444 | 1794686599993636 | 4192 |
| YZ | 1794686601174664 | 1794686601178657 | 3993 |
| Through-all | 1794686601520153 | 1794686601526282 | 6129 |

Python 3.14.6 processed all eleven exact archives. The root and active manifests agree on the asset GUID. Interpreting the integer scale as epoch microseconds reproduces the kernel creation string to the second, and the ZIP clocks of both manifests and the mapped blob fall within one two-second DOS interval of the cut clock. These saved wall strings have no timezone field. The historical receipt corroborates the feature roster and order.

Slot `1` is empty across all eleven. Slot `2` has only side-1 entries, including the initial BODY record and the trailing boss timestamp attribute. Resolving its raw entity ordinals through the already verified kind-preserving slot-0 aliases yields every row of the clock-bound `BlindBoss` source chart except its ASM header. The inventory covers 101 entities in ten archives and 102 in YZ, with no duplicates, extra rows or missing non-header rows. The report retains the original ordinals and the exact alias substitutions. The one-sided inventory identifies the boss chart. A distinct creation or removal event, a slot-2 command actor and slot-1 behavior still require independent evidence. Raw headers and the neighbor order `0 → 2 → 1` stay visible. [Fusion journal slots and clocks](../../../Gotchas/Research/Readers/FusionJournalSlotClocks.md)

Fresh Fusion supporting-face and participant getters, exact licensed process readback, and editable acceptance remain open.

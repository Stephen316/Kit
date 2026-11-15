# Fusion drawing acceptance record

## Problem

The Fusion drawing work had evidence spread across change entries, gotchas and research reports.
No single page said which of the [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md)
pass, which fail, and why, so a reader could not tell a measured result from a claim.

## Change

[`Documentation/Reference/Operations/FusionDrawingAcceptance.md`](../../../Reference/Operations/FusionDrawingAcceptance.md)
records the verdict per criterion with the measured numbers.

| Criterion                  | Verdict                                              |
| -------------------------- | ---------------------------------------------------- |
| C1 no donor data           | pass, scanner clean, no CAD files under `src/`, and the one captured default is now the schema zero |
| C2 no CAD runtime          | pass, Fusion is the oracle only                      |
| C3 lossless                | **not met** for drawings: 60 of 60 and 248 of 248 are byte replay, not conversion |
| C4 fully parametric        | pass for designs, **not met** for drawings           |
| C5 to C7 loadable and usable | **fail** for a drawing authored from nothing       |
| C8 honest attestation      | the failure is stated as a failure                   |
| C9 complete implementation | incomplete, blocked by policy                        |
| C10 generalization         | held-out design case and one-input drawing controls  |
| C11 traceable knowledge    | five gotchas linked                                  |

## Sheet name control

A third control changed only the drawing member's `ActiveSheet` to `Kit Sheet Renamed` and left the
DWG byte-identical. Fusion reported the old name, `KitDrw Source 20261112114717`, with the same
420 by 297 mm sheet and views `[5, 4, 4]`. The member is a mirror, not the value Fusion reads.

## Behavior

One data change: `ACDBASSOCINVENTORPERSSUBENTIDMANAGER.ManagerFlag` in the authored drawing defaults
was `1` because every Fusion save carries `1`, although Fusion also opens the drawing with `0`.
It is now the schema zero, so the table holds no value that only a save can justify.

The rest is a record, and it links the gotchas that carry each finding.

## Verification

Every number on the page comes from a run recorded in this repository or in the research workspace:

| Number                          | Source                                        |
| ------------------------------- | --------------------------------------------- |
| 60 of 60 DWG, 248 of 248 F2D    | corpus round-trip run on this branch          |
| 60 of 60 headers typed          | same run                                      |
| 3078 files scanned              | `tools.Donors.CheckReplays src`               |
| design volumes                  | `OpenDesign.py` reports in the research tree  |
| sheet, scale and position       | `BisectRound.py` reports for the three cases  |

## Limits

The page states a failure. It does not make the drawing writer loadable, and it does not claim the
objective is met.

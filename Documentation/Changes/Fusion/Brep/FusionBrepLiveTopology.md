# BRep live topology is resolved by the existing state walk

## Problem

A BRep journal is a history, not a snapshot. Counting every entity in it overcounts, because the
journal keeps the topology from before a feature as well as after it.

`shell_both.f3d` carries 3 `DeltaState` records and 266 entities for an `ActiveCount` of 195. A count
over every entity reports 17 faces, 36 edges and 24 vertices, while Fusion reports 11, 24 and 16.

## Change

No new resolver. `WalkStates` already walks the delta-state chain from the active node, undoes each
state, and validates that the journal resolves to its initial header. Its first `LiveState` is the
live topology at the active node.

An earlier draft of this change added a second resolver that applied the bulletin boards in physical
order. That was wrong twice: the physical order is not chronological, because the latest state sits at
node zero, and the set started empty, which dropped the ASM header at entity zero. The draft is
removed and the existing validated walk is the only resolver.

## Behavior

| File | `WalkStates(...)[0]` | Fusion | Match |
| ---- | -------------------- | ------ | ----- |
| `mirror_xy.f3d` | 12 face, 24 edge, 16 vertex, 2 body | 2 bodies of 6, 12, 8 | yes |
| `analytic.f3d` | 4 face, 2 edge, 2 vertex, 3 body | sphere 1/0/0, torus 1/0/0, cone 2/2/2 | yes |
| `shell_both.f3d` | 11 face, 24 edge, 16 vertex, 1 body | 1 body of 11, 24, 16 | yes |

## Verification

The three files were opened in local Fusion 2706.1.17 with `ProbeBrep.py`, which imports the F3D and
reports each body's face, edge and vertex counts. The walked counts match all three.

Across the corpus, `WalkStates` resolves 500 journals with no failures, and the live count equals the
journal's `ActiveCount` in all 500. That equality is the check that the walk is not over- or
under-counting: `shell_both` resolves to 195 live entities for an `ActiveCount` of 195, where a count
over every entity gives 266.

## Limits

`WalkStates` returns live entity indices and their versions. It does not rebuild the topology graph,
so a caller still has to read the entity records to know what each index is.

The 39 corpus designs whose body history is a `PrismHistory` wrapping a `HistoryState` are not
journals and are not covered.

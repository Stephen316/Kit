# A combine keeps its consumed tool body in the journal

## Expectation

A combine that does not keep its tools removes the tool body.
The journal state after the combine would then hold only the target body.

## Actual behavior

The native `Combine` control joins a post into a block.
Its journal makes the block as body tag 7 in state 6 and the post as body tag 8 in state 7.
State 8 modifies body 7 only, and no later state deletes body 8.

The Design keeps the consumed body as well.
Its `Body` has `isVisible` false and is missing from the `children` and `groupChildren` of `Bodies`.
Its `DcBody` has `isEliminated` true, and the combine lists it in `removedBodies`.
`BRepHistorySerializer.mapBodyId` still maps the tool body tag.

## Workaround

`SolvePart` keeps every body it has made, and `PartStage.Bodies` lists them all.
`PartStage.Shown` lists the visible bodies only.
`EmitPartHist` writes every body into each later state, so a consumed tool stays in the journal.
`LinkBodiesMut` hides the consumed bodies and maps every body tag.
The four combine cases passed native acceptance, including the recompute, edit and reopen checks.

The [native combine control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/Combine.f3d) records the journal.

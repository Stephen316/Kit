# A body paste writes a hidden base feature

## Expectation

`copyPasteBodies.add` adds one timeline item. Its Design record would own the pasted body and the journal state, like a body pattern.

## Actual behavior

The four native paste controls each write two features for one paste.
`DcPasteBodies` is the timeline item. It names the source body through a `ModelDataRef` and a `DRBody`, and both of its model history indexes are -1.
`DcPasteBodies.rBaseFeature` names a `DcBaseFeature` that is missing from `DcCreationOrderFeatures`.
The base feature owns the journal state and the first of the two paste operations. The paste owns the second.
Both features name the paste as `rGroupRepresentative`, and the paste lists both in `groupMembers`.

The base feature holds two bodies.
A hidden body sits in the cache bodies, which also hold the base feature snapshot part.
The visible body sits in the part bodies, and its `DcBody` names the base feature as its owner.
The two bodies name each other through `BASEFEAT_PM_BODY_REF` and `BASEFEAT_DM_BODY_REF`.

In the journal the pasted body is a new body. Its body tag is the first paste operation with secondary id 1.
Every face tag of the source appends the first operation. Edge tags stay as in the source.

## Workaround

`AddPasteMut` writes both features, both bodies and the base feature progenitor table.
`LinkTimeline` gives the first operation to the base feature and leaves it out of the creation order.
`PasteSolid` copies the source solid with the shifted face tags.
Fusion saves a body snapshot for the hidden PM body. Kit writes no snapshot for it and leaves its `mapBodyId` entry empty.
Fusion accepted all six paste cases without the snapshot, both at open and after `computeAll`.

The native controls are `PastePlain`, `PasteFillet`, `PasteTwice` and `PasteSecond` in [the paste capture report](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/CapturePastes.json).

# Native Metadata Header Semantics

The two 32-bit fields previously retained as `MetaHeader.HeaderWords` are one 64-bit saved software version.
For the controlled build, `(17, 709361728)` is `0x2a48004000000011`.
The formula `(major << 50) | (minor << 38) | build` decodes it to 2706.1.17, the version of the Fusion build that saved the controls.

[NativeHeader.json](NativeHeader.json) records this interpretation.
An earlier version also cited static inspection of installed Fusion libraries.
That material was removed.
It was the only source for these points, which are not confirmed by a black-box experiment:

- The bit widths: 14 bits for major, 12 for minor, and unused bits 32 to 37.
- The wide UUID previously called `Namespace` is the segment's current version UUID.
- The order of the save fields after the literal magic 1234: metadata version, packed software version, segment type identifier, add-in identifier, and segment type enum.
- The next word counts ancestry UUIDs, and a nonzero count is followed by that many wide UUID strings.

The qualified controls have no ancestry entries.
The current production header codec admits this zero-count profile.
It should not be described as supporting arbitrary ancestry.

## Manifest identity and allocation

An earlier version named the root manifest UUIDs, the localized strings before them, the per-module version maps and the asset manifest UUIDs from the same removed static evidence.
It also read the value 5 before the segment count as a next-segment-ID allocation watermark.
These readings are not confirmed by a black-box experiment.
Until a black-box experiment settles it, a source rewrite should retain the value it finds.

## Entity offset ordering

[OrderingCorpus.json](OrderingCorpus.json) observes 2,136 segments across all 712 inventory archives.
Their 259,464 primary records and 34,228 continuation records have no descending physical entity IDs.
Both metadata index lists also have no descending IDs.
There were no unsupported headers or read errors.
This is a fresh read-only observation rather than a test run.

A black-box run supports the constraint.
An independently authored ACT graph initially violated this ordering.
Sorting physical primary records by entity identity advanced native loading to the next semantic requirement.
An earlier explanation of the loader came from removed static evidence and is not repeated here.

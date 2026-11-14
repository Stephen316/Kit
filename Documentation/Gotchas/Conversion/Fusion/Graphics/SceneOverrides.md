# Assembly scenes hold override attributes

## Expectation

The attribute classes of a scene are display attributes with fixed fields. Every entity in the scene names a record of the document.

## Actual behavior

Member 3 of `re/Fusion/examples/.f3z/example1.f3z` is an assembly. Its instance nodes carry attribute sets of kind 3 with override attributes. No other corpus world holds them, apart from the copy in `re/Fusion/LocalOracle/Bundles`.

| Class | Count | Fields |
| --- | --- | --- |
| `OverrideTransformAttribute` | 159 | `Transform`, `Absolute`, `NodePath`, `Target`, `Overrides` |
| `OverrideVisibilityAttribute` | 4 | `Visibility`, `NodePath`, `Target`, `Overrides` |
| `OverrideInActivatedVisibilityAttribute` | 8 | `Visibility`, `NodePath` |

- `Transform` is 16 `f32`. `Absolute` and `Visibility` are flags.
- `NodePath` links a `PersistentPassiveNodePath` object, like other linked objects: a flag, the class name, an id text and, on first use, the body. The body is a `u32` count of entries. Each entry is a `u32` segment id and a big-endian `u64` object id.
- `Target` is a flag. Flag 1 is followed by a big-endian `u64` object id and a `u32` segment id. Flag 0 is followed by a node id text.
- `Overrides` is a `u32` count of override sets. An override set is a child set, a target and an `i32` count of child sets. Those child sets can hold further override attributes.

The 171 paths have 2, 3, 4 or 6 entries. 36 last entries name no record of this document. They point into referenced documents.

Kit raised `ValueError("Unsupported graphics attribute class: OverrideTransformAttribute")`.

## Workaround

Read the three classes with these fields. Keep path entries as `PathEntity` values, not as `EntityRef` values, so `CheckDocScene` does not check them. Add node id targets to the node links that `FinishScene` checks.

## Evidence

- [Cache and package notes](../../../../../re/Fusion/Reconstruction/ReadGaps/CachePackageNotes.md#override-attributes-member-3)
- [Override spy](../../../../../re/Fusion/Reconstruction/ReadGaps/OverrideSpy.py) and [path spy](../../../../../re/Fusion/Reconstruction/ReadGaps/PathSpy.py)
- [Cache gap tests](../../../../../tests/convert/formats/FusionCodec/SavedCorpus/CacheGapTests.py), case `TestCacheMember`

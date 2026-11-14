# Sketch attribute ASCII semantics

The version-three kernel `sketch_attrib_def` string stores six fields:

```text
primaryId secondaryId direction topologyRoleFlags splitSequenceId splitTotalNumber
```

For `102 0 0 0 1 1`, the final ones mean fragment one of one.
They are not independent enumerations.

## Evidence

[SketchAsciiSemantics.json](SketchAsciiSemantics.json) holds the corpus observations.
[SketchAsciiSemantics.py](SketchAsciiSemantics.py) reproduces the read-only corpus inspection without executing product code or calling Fusion.

An earlier version also cited static inspection of installed Fusion libraries.
That material was removed.
It was the only source for these claims, which are not confirmed by a black-box experiment:

- The fourth ASCII field is the stored topology-role mask, not a reserved constant.
- The ASCII fields use unsigned overloads, with the widths of the saved Design record.
- Older kernel tag versions read signed values and place the flags differently.
- Reversal should exchange zero and one and keep the wildcard.

The saved Design sketch tag record writes `version, primary, secondary, direction, sequence, total, flags`.
The ASCII kernel form keeps six values and puts its fourth value before sequence and total.
Keep the two orders distinct.

## Semantic domains

Primary and secondary IDs form a source-curve key in Kit's model.
The secondary component is zero for ordinary authored sketch curves in the qualified writer.
Corpus kernel attributes also contain nonzero secondary IDs, including generated text-outline identifiers.

Direction has the values zero, one and `4294967295` in the corpus.
The value `4294967295` shows that the ASCII form prints direction as an unsigned 32-bit value.
The [split evidence](SketchSplitSemantics.md) supports the joint invariant `1 <= sequence <= total <= UINT32_MAX` and the unsplit pair `(1,1)`.
A fragment ordinal is distinct from the total fragment count.

`topologyRoleFlags` is a behavior-based name; see [SketchTagSemantics.md](SketchTagSemantics.md).
Its complete bit dictionary and exact source field name remain unresolved.
A qualified ordinary-profile writer can require zero.
It should treat this as a restricted value, not pretend the field is absent or padding.

## Corpus corroboration

The read-only inspection covered all 1,083 distinct `.smb`/`.smbh` blob digests in the frozen corpus inventory, including archived record revisions.
Repeated blob members were counted once.
It found 20,636 sketch attributes, all using version three:

| Observation | Count |
| --- | ---: |
| Direction zero / one / wildcard | 15,573 / 4,964 / 99 |
| Fourth field zero | 20,636 |
| Unsplit `(1,1)` | 20,180 |
| Split pair other than `(1,1)` | 456 |
| Values outside the stated unsigned domains or split invariant | 0 |

Examples and exact split-pair counts are retained in the JSON.
These source observations support the field reading.
They do not establish native acceptance of expanded product writer qualifications.

## Scoped product and documentation corrections

Rename provisional fields such as `EnumA/EnumB` to `SplitSequenceId/SplitTotalNumber`.
Model the fourth member as `RoleFlags` or `TopologyRoleFlags`, with explicit zero qualification.
Validate the ordinal and count jointly.
Keep ASCII and binary callback member orders distinct.

The previously frozen cuboid research text called the fourth ASCII member `reservedZero`.
Its observed zero value remains correct.
Existing accepted cylinder and cuboid-control bytes do not change when the semantic names change.

No production files, frozen cuboid artifacts or native application state were modified by this investigation.
No local tests were run.

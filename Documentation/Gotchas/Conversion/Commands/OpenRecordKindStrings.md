# Structurally valid kind strings can still describe unsupported semantics

Several SDK record kinds accept an enum or an open string for research and
interchange preservation. Valid component links, mate entity paths, and sketch
references do not prove that a native or unknown kind has portable semantics.
These records can pass `CadDocument.AssertValid()` without using `NativeFeature`
or `NativeGeometry` payload classes.

The CLI now checks known nonnative kinds for component definitions, mates, mate
entities, sketch entities, and sketch constraints throughout the document graph.
Both enum `native` values and canonical `"native"` strings are refused; unknown
strings are refused too. A typed geometry object does not override an unsupported
entity-kind tag.

Use `kit decode` or the research commands to inspect and recover unsupported
semantics. Known enum values and their canonical strings remain eligible, and SDK
inspection still preserves the original records. See
[the process cases](../../../../tests/Convert/Commands/Kind/CliKindTests.py) and
[the change entry](../../../Changes/Commands/NativeRecordKinds.md).

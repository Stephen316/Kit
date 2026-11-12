<!--
This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Archive and native records

[Fusion feature index](../README.md)

See [the archive source proof](../../../src/convert/formats/Fusion/SourceProof/InspectSource.py) for the receipt and [the wire codecs](../../../src/convert/formats/Fusion/SegmentCodec) for stream framing.

## SDK coverage

The SDK's `convert.formats.Fusion.BulkSpans.ReadBulkSpans` indexes native
version-8 design streams. It accepts decompressed BulkStream and MetaStream
bytes and returns immutable record spans with class and object identities.
It checks each bulk header against its metadata entry and verifies that
continuations belong to ancestors of their primary class. The SDK index
agreed with the study on all 261,141 record boundaries and identities
across the 712 tracked archives.

`convert.formats.Fusion.DesignZip.ReadDesignZip` loads the active design
stream pair directly from `.f3d` bytes and returns the BulkStream with its
verified record spans. It checks archive size and entry limits, rejects
duplicate or encrypted members, and verifies both selected payloads.
Runtimes with standard ZIP Zstandard support can read the archive directly.
Older runtimes can supply a Zstandard decoder that accepts compressed bytes
and an expected output size. The callback must bound decompression to that
size. The archive reader checks the returned size and CRC.

The document reader uses one validated ZIP index for the active design and
every referenced body history stream. It reads referenced streams on demand.
Explicit-format reads share this session across all feature projections.
Automatic format detection still performs a separate, non-inflating probe.

`convert.formats.Fusion.SourceProof.InspectSource.ReadFusionSourceProof`
reports coverage for the exact archive SHA-256 and selected native history.
It reports each unresolved ZIP member and design record, including primary
records and continuations. Framed streams and source spans attached to
neutral entities count as structural or observed evidence. Complete proof
currently covers the selected version-zero history and group records and
exact empty configuration table and rule members. It verifies numeric
parameters against the standalone collection order, scoped names, and
saved expression values. Bound values also need reciprocal binding records
and matching feature controls. It verifies the two known numeric metadata
layouts, including the eleven-byte form used by newer Revolve captures.
Browser and ACT stream framing provides structural evidence from their
version-8 index and record boundaries. The optional
`ActiveRoutes` receipt links the root manifest's active asset ID to the
active manifest and its snapshot ID to ACTTable. A `0_` route must repeat
the exact counted key in its typed Design primary record. A `1_` route
must resolve to its typed ACT component or instance in the ACT stream.
The report keeps unsupported `3_` routes and unexplained field tails
visible and records the manifest and ACT links as observed evidence.
ACT role UUIDs are change tokens. The route links can survive a Design
stream swap between revisions of the same asset and do not authenticate
the saved Design snapshot. Ordinary reads leave these streams unopened.
ACT payloads and unverified parameter data remain unresolved. The two-body
Scale capture has 30 members, 388 primary records, and 62 continuations. Its report leaves
28 members and 438 design records unresolved. Strict Fusion import and
conversion still require complete source coverage.

The internal segment writer builds version-8 Design, ACT, and Browser
streams from typed metadata and record payloads. It checks primary class
ownership and continuation ancestry, then derives both index tables from
the emitted record positions. The Browser root codec writes the ordered
routes and named folders, including the alternate route flag observed in
one older capture. Across 713 native archives, these codecs reproduced
2,139 stream pairs and 713 Browser root payloads byte for byte. Full
Fusion export still requires semantic writers for the remaining native
records and validation in Fusion.

The internal asset builder emits both manifests, all three core stream
pairs, and empty root properties in a ZIP32 archive. It uses method 93
with standard raw Zstandard blocks, including on Python versions without
a Zstandard encoder. ACT field ownership and Browser route and folder
references must agree with Design before the archive is emitted. Empty
configuration sidecars require explicit selection and the exact member
names declared by the typed Design triggers. This archive profile covers
the core graph. Graphics caches, other auxiliary members, and a complete
CAD document writer require separate work and verification in Fusion.

## Saved study coverage

Saved evidence includes [`fusion-class-catalog.json`](../Study/fusion-class-catalog.json).

| Area                 | Observed support                                                                                                                           | Open work                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| Archive and metadata | ZIP/Zstandard members, CRCs, version-8 class registries and indexed primary/inherited records for observed design, browser and ACT headers | Other header variants/versions; browser/ACT field schemas |
| Unknown features     | Observed feature-class ancestry exposes unsupported feature records explicitly                                                             | Unknown ancestry and unimplemented native fields          |

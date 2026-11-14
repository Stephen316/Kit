# Fusion corpus entity coverage

## Behavior

The research Design reader now consumes every indexed Design record in the supplied corpus: 712 archives, 261,141 records, and 25,458,293 payload bytes. There are no archive failures or unexplained suffixes. This closes the previous 4,619 unresolved records through typed named metadata, line/ellipse/NURBS callbacks, ASM persistent-selection recipes, and the lazily initialized progenitor auxiliary value.

[The complete callback model](../../../re/Fusion/Reconstruction/EntityGraph/ExtendedCallbacks.md) describes exact field order, version qualifications, array capacity descriptors, recursive recipe payloads, tag tables, and UV order fields. [The summary](../../../re/Fusion/Reconstruction/CorpusSemantics/Summary.json) and [compressed per-record evidence](../../../re/Fusion/Reconstruction/CorpusSemantics/Inventory.json.xz) bind those counts to source digests and offsets. The initial inventory is preserved beside them.

## Usage and qualification

`python re/Fusion/Reconstruction/CorpusSemantics/InspectGraphs.py` performs read-only corpus analysis and writes the inventory. It requires the research corpus and captured reflection vocabulary. It is not a production entry point.

The recipe profile admits tagging version 3, which accounts for all 1,763 corpus recipes. The geometry profile includes the observed NURBS interval layout. Older-version branches are not confirmed by a black-box experiment and are not treated as compatible. The full inventory establishes typed field boundaries, not every feature algorithm or independent regeneration of every corpus model.

The [geometry array gotcha](../../Gotchas/Conversion/Fusion/FusionGeometryArrayLayout.md) and [lazy schema gotcha](../../Gotchas/Conversion/Fusion/FusionLazyValueSchemas.md) record the assumptions that previously prevented complete parsing.

## Production compatibility profiles

Schema-only descriptors now select 412 class/version declarations across all 712 archives. They include inherited fields, explicit reference targets, named metadata, custom geometry callbacks, recursive selection recipes, matrix identity discrimination, and lazy progenitor values. The fixture contains schema vocabulary, not retained entity values or donor geometry.

The [split-tag correction](../../Gotchas/Conversion/Fusion/FusionSketchSplitTags.md) qualifies one-based fragment ordinals and the native wildcard direction while preserving the narrower secondary-ID and topology-role guards.

The remote compatibility suite decodes each archive through production `EntityCodec`, re-encodes its typed values, and requires exact physical-record, bulk-stream, and metadata-stream equality. No local execution of these compatibility cases is permitted. [The descriptor summary](../../../re/Fusion/Reconstruction/EntityGraph/CorpusProfileSummary.json) records qualifications and unresolved empty-only branches.

The [sketch-tag notes](../../../re/Fusion/Reconstruction/EntityGraph/SketchTagSemantics.md) name the two profile sets as start and end adjacent primary tag IDs, and one sketch-tag word as topology role flags. A black-box experiment does not confirm these names. The bit allocation is unresolved. All 5,077 observed sketch-tag values across the 712 archives have zero in that word, so the production zero-only guard remains justified.

## Verification

Remote run `43221337105` passed 783 of 804 archive cases. Its 21 corpus failures exposed the split and wildcard assumptions described above; revision `4eb1571f6c9a6f870aaa8ae7a67c22873384b190` corrected them. Remote [run 43222880126](https://github.com/TryUniCAD/Kit/actions/runs/43222880126) then passed all 807 cases in 35.59 seconds, including all 712 complete corpus Design reconstructions and three malformed split-tag rejection cases. [The evidence manifest](../../../re/Fusion/Reconstruction/CorpusSemantics/ProductionCompatibility.json) records the exact revision and schema digest. All pre-existing document, container, material, BRep, entity, and bundle cases passed.

Evidence comes from read-only corpus decoding and the remote compatibility runs. No local automated tests ran. Independent document generation and native acceptance remain separately reported in [FusionIndependentAuthoring.md](FusionIndependentAuthoring.md) and the production document change entry.

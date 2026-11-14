# Typed linear Fusion BRep journals

`ReadJournal` and `EmitJournal` read and write complete qualified ASM history streams, including archived entity versions and insertion, deletion and replacement bulletins. The model stores named fields for every supported record. It contains no original payload, opaque record, token-list or trailing-byte field.

## API

The API lives in `convert.formats.Fusion.BrepCodec.Journal`:

| Function         | Input                                                                 | Result                                                                       |
| ---------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `ReadJournal`    | A complete `.smbh` member as bytes                                    | Immutable `JournalModel`                                                     |
| `EmitJournal`    | `JournalModel`                                                        | Complete derived binary history bytes                                        |
| `Materialize`    | `JournalModel`                                                        | Ordered live revision maps from current to initial state                     |
| `PermuteJournal` | Model and a complete tuple of entity ordinals in desired output order | Equivalent model with all entity references and bulletin references remapped |

`JournalModel` holds the semantic header and provenance stamp, active entity count, complete typed entity table, stream state and delta states. Geometry values explicitly use centimetres; direction vectors and carrier parameters retain their distinct field roles. The writer does not infer units from numerical values.

The entity union includes bodies, lumps, shells, faces, loops, coedges, edges, vertices, points, planes, cones, ellipses and straight carriers. Attribute models cover timestamps, generic feature tags, ASCII sketch links and tracked entity tags. Generic-tag and sketch-link fields reuse the existing validated identity models. `FPM_tracked_attrib_def` contributes one signed 32-bit tracking identity under schema version one.

`StreamState` separates current ID, maximum allocated ID, retained-state limit and next entity tag. `DeltaState` separates state IDs from physical node references, flags, optional names and bulletin boards. `BulletinChange` represents old/new entity references directly; insertion, deletion and replacement are derived from which reference is null. `LiveState.Versions` maps each logical slot to its selected physical revision.

## Validation and qualified scope

The reader and writer both validate the complete state chain and every materialized entity table. They require reciprocal previous/next references, unique state IDs, a matching current-state root, and all archived revisions referenced by bulletins. The reader and writer also require no alias cycles, class-compatible live entity references and eventual rollback to the initial ASM header. Non-null entity tags must remain below the declared allocator. Required solid topology references cannot be null.

The profile is bounded to 2 MiB, 1,024 total entity records, 256 states and 256 boards per state. The profile is also bounded to 1,000 changes per board and 4,096 wire fields per record. Kit bounds integers to signed 32-bit domains, even when they are stored in tagged 64-bit wire slots. Numeric payloads must be finite. Text is qualified ASCII. The header is ASM BinaryFile8 save version 23200, two roots, flags three, unit metadata 50 and the established tolerances.

Supported histories are linear, with backward and visible states, self-linked partner nodes and null merge references. Supported histories also have succeeded boards, zero retained-state limit and an empty final state list. Working-node and owner-entity references must be null. Names, branching/merged histories, other save options, unsupported entity/attribute kinds, non-null reserved fields and trailing bytes fail explicitly. The final state-list role and non-null history owner-entity semantics remain unresolved and are not retained opaquely.

`PermuteJournal` keeps the ASM header at ordinal zero and preserves the active/archive partition. It remaps entity references and bulletin old/new references only. State-node ordinals, state IDs, entity tags, Design identities and custom attribute values remain unchanged. Allocation order is therefore independent of these external identities.

This API operates on a complete BRep history member. It does not automatically add arbitrary multi-state dispatch to `ReadDocument`, produce a new Design feature graph, validate arbitrary CAD geometry or qualify unsupported carriers. Existing analytic authoring APIs remain separate.

## Evidence and verification

The [detailed data model](../../../../re/Fusion/Reconstruction/JournalStates/JournalModel.md) and [Design identity joins](../../../../re/Fusion/Reconstruction/JournalStates/DesignStatesSummary.json) explain the field meanings and remaining boundaries. Some field names, such as the hidden-state flag, the merged-state reference, the retained-state limit and the tracked-attribute width, first came from binary inspection. That evidence was removed at the tip and is not a black-box confirmation. Source digests accompany the compressed record evidence.

Research serializers reconstructed both controlled three-state histories exactly: Draft has 35 active and 22 archived records; OffsetFaces has 35 active and 25 archived records. Both materialize states `14 → 9 → 2` with `35 → 36 → 1` live entities. The earlier cylinder includes the tracked face attribute that the current body no longer needs.

[Native reconstruction acceptance](../../../../re/Fusion/LocalOracle/JournalStates/NativeAcceptance.json) passed both sources through rollback to prior states, restoration, rebuild, driving-height and final-feature edits, save and reopen. [Native allocation permutation acceptance](../../../../re/Fusion/LocalOracle/JournalStates/NativePermutationAcceptance.json) passed the same sequence after independent active/archive reordering and reference remapping. Each acceptance archive retained its own source's non-history members; these results establish complete semantic history replacement, not independent full-document authoring.

[Production native acceptance](../../../../re/Fusion/LocalOracle/JournalStates/NativeProductionAcceptance.json), SHA-256 `fdee08a175167a2d579905ac7084ecdf6f58cdcd26b4d0a3672c41bd7ef8dd66`, passed both controls and all four public-codec candidates. [ProductionPreparation.json](../../../../re/Fusion/LocalOracle/JournalStates/ProductionPreparation.json) binds each input, output and complete history digest. `ReadJournal` → `EmitJournal` produced byte-exact original histories; `PermuteJournal` changed the allocation bytes while preserving all native observations. Both source-specific pairs passed prior-state rollback, sketch-only rollback, restoration/rebuild, height 23 mm, final-feature edits to 7° or 3.5 mm, and save/reopen. The native application had zero documents open afterward. The reproducible preparation and native driver are `PrepareProduction.py` and `AcceptProductionJournal.py`; neither is a production dependency.

Twelve remote archive integration cases cover both three-state sources, independently permuted allocations, rolled-back metadata and a 102-record ordinary cuboid. The cases also cover rejection of trailing bytes, unknown attributes, wrong reference classes, unsupported board status, nonempty initial-state boards and cyclic state links. Black, Ruff, mypy, strict Pyright and repository steering checks passed the 130 new production/integration modules. No local tests ran.

See [the journal namespace gotcha](../../../Gotchas/Conversion/Fusion/Geometry/FusionJournalRevisions.md).

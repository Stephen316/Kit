# Packaged native Fusion schema catalog

## Behavior

`EntityCodec.Vocabulary.BuildProfile` derives a qualified decoding/encoding profile from the archive's real `MetaClass` declarations and explicit external targets. Callers no longer need corpus-specific class lists or research fixtures.

The packaged `NativeClasses.xz` contains 412 class/version declarations and six named metadata types. It stores format vocabulary: class GUIDs, inheritance, member names, saved-state flags, wire shapes, reference target classes, and validated discriminator domains. It contains no source archive paths, source digests, root entity identities, entity values, geometry payloads, or donor blocks. The generic root class GUID is a format identity, not a source object's ID.

## API

```python
from convert.formats.Fusion.EntityCodec.DecodeEntities import DecodeEntities
from convert.formats.Fusion.EntityCodec.EncodeEntities import EncodeEntities
from convert.formats.Fusion.EntityCodec.Vocabulary.BuildProfile import BuildProfile

Profile = BuildProfile(Metadata.Classes, ExternalTargets)
Values = DecodeEntities(Records, Metadata.Classes, Profile)
ReconstructedRecords = EncodeEntities(Values, Metadata.Classes, Profile)
```

`Metadata.Classes` is the tuple parsed from the segment metadata. `ExternalTargets` is an explicit tuple of `ExternalTarget` values describing referenced entities in other segments; it defaults to empty. The caller remains responsible for supplying the real external target inventory. The return value is an immutable `EntityProfile` accepted by the existing entity codecs.

## Version and dependency selection

Every metadata declaration must match one catalog class GUID, exact schema version, and base GUID. GUID matching is case-insensitive. Duplicate declarations, unknown classes, unknown versions, and incompatible bases are rejected.

The factory recursively includes required base classes, nested value-object dependencies, and known external target ancestry. Unsaved declarations participate in schema validation even though they emit no saved bytes. A dependency not explicitly versioned by the segment is admitted only when the catalog has exactly one qualified version; missing or ambiguous versions are rejected. The factory does not choose a latest version by convention.

The assembled profile passes `BindProfile` validation before it is returned. Per-record class ownership, inheritance continuations, references, payload bounds, discriminator domains, and complete byte consumption remain enforced by the entity codecs.

## Limits

This catalog qualifies the observed Design schemas and their dependencies. It does not independently synthesize every feature or decode every BRep/history representation. Optional conflict values and the empty-only PMI map retain their existing rejection guards for unsupported nonempty content. Sketch tags retain the qualified version, secondary-ID and topology-role restrictions.

The independently accepted document authoring catalog remains unchanged. The new factory is a broader reader/writer profile facility, not an implicit expansion of the document author's feature support.

## Reproducible catalog promotion

`re/Fusion/Reconstruction/EntityGraph/PromoteCatalog.py` derives the production catalog and the separate test provenance fixture from the research schema inventory using explicit declaration-key whitelists. `--check` compares both artifacts byte-for-byte without writing them. The compatibility workflow runs this provenance check before exercising archive reconstruction. Neither the promotion tool nor the research inventory is a production runtime dependency.

## Verification

The previous explicit-schema path passed all 712 corpus archive reconstructions within the 807-case remote run on `4eb1571f6c9a6f870aaa8ae7a67c22873384b190`. The corpus suite now obtains every profile through this production factory and retains only archive paths and metadata digests in a separate test provenance fixture. No production module imports the test fixture or research workspace.

Three additional archive-boundary cases rewrite complete ZIP metadata to carry an unqualified class, schema version, or base, and require explicit rejection. Remote run `43225207242` passed all 712 factory-driven reconstructions and 814 of 815 total cases. The base-mismatch rejection fixture initially violated continuation lineage while constructing its malformed archive, before reaching the intended catalog guard. The corrected fixture mutates an unused leaf class and awaits its new remote run. No cases ran locally. Black, Ruff, Mypy, Pyright, steering compliance, and diff checks passed for the new production and integration files.

See [full corpus coverage](FusionCorpusEntityCoverage.md), [the detailed data model](../../Reference/Research/FusionDataModel.md), and [complete document authoring](FusionNativeDocumentCodec.md).

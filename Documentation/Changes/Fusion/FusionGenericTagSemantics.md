# Fusion generic-tag identities and byte lengths

## Corrected behavior

The BRep codec now models generic-tag fields using the meanings the saved corpus supports.
It derives each primary identifier's byte count and validates that count when reading.
Body tags with operation identities longer than three decimal characters now have the correct count.

`FeatureTag` exposes `PrimaryId`, `OperationIds`, `SecondaryId`, and `ApproachId`.
The removed `Selector` field was a byte count, not a topology selector.
`BodyIdentity.SecondaryId` replaces the misleading `GenerationRef` name.
The secondary identity is independent of the history stream state IDs and entity-tag counter. [Native history semantics](FusionHistoryStates.md) replaces the earlier generation-number terminology.

The canonical document author uses its existing `BodyProgenitorTag` as the body's secondary identity.
Its redundant `AuthorPolicy.GenerationRef` setting has been removed.
The accepted default identities and their serialized bytes remain unchanged.

## Field contract

Each saved tag group holds these fields:

| Order | Field                        | Wire representation | Production handling                        |
| ----- | ---------------------------- | ------------------- | ------------------------------------------ |
| 1     | Primary byte-array length    | Tagged integer      | Derived from primary text; checked on read |
| 2     | Primary identifier bytes     | Counted text        | `FeatureTag.PrimaryId`                     |
| 3     | Secondary identity           | Tagged integer      | `SecondaryId`                              |
| 4     | Operation-array length       | Tagged integer      | Derived from `OperationIds`                |
| 5     | Ordered operation identities | Tagged integers     | `OperationIds`                             |
| 6     | Approach identity            | Tagged integer      | `ApproachId`                               |

BinaryFile8 stores secondary, operation, and approach identities in tagged 64-bit integer fields.
Kit limits them to signed 32 bits.
That limit and the field names for the secondary and approach identities came from binary inspection.
They are not confirmed by a black-box experiment.

The qualified writer admits printable ASCII primary identifiers from one through 255 bytes.
Unicode and embedded NUL behavior remain outside this profile.
It accepts at most 256 ordered operation identities, including an empty sequence.

## API migration

Old explicit count inputs are removed:

```python
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag

FaceTag = FeatureTag("3", (1701,))
EdgeTag = FeatureTag("-102", (1701,), SecondaryId=0, ApproachId=0)
Identity = BodyIdentity(0, 1701, 4, 1794477991119457)
```

The body identity's third argument is now `SecondaryId`.
The body primary text remains the canonical decimal spelling of `OperationId` in the qualified cylinder profile.
That body profile requires a nonnegative signed-32-bit operation identity, an empty operation list, and approach zero.
General body tag groups and arbitrary primary body strings are not introduced by this correction.

Current production callers and preparation bridges use the new API.
Historical reports retain their original field spellings so their evidence remains auditable.
The historical research-only `body_generation_reference` and `selector` names are superseded by this interpretation.
Legacy research specification keys remain accepted by their existing preparation bridge and map to the corrected production fields.

## Evidence

The [tag evidence](../../../re/Fusion/Reconstruction/CuboidHistory/GenericTagEvidence.json)
records the controlled tag examples and the decoded candidate histories.

All 441 decoded generic-tag groups across sixty candidate box histories have matching declared primary byte lengths.
Observed secondary identities include zero, one, seven, eight, and thirteen.
All observed approach identities are zero.

The controlled cuboid body group is `[3, "301", 7, 0, 0]`.
Its secondary identity seven matches its Design-side body progenitor tag.
The controlled cylinder bottom-edge group is `[4, "-102", 0, 1, 301, 0]`.
The four counts the bytes of `-102`; it does not identify an edge type.

This evidence defines field order and byte lengths.
It does not establish arbitrary tag identity assignments as valid native feature-history links.

## Verification

Archive integration coverage now checks four-digit body primary lengths and longer face identifiers.
It carries signed identity boundaries through emitted history, ZIP storage, and the complete history reader.
It corrupts body and face declared lengths independently and requires rejection after archive loading.
An exact `ReadDocument` → `EmitParsed` case protects the previously accepted `ProductionExtrusion.f3d` artifact.

No integration tests or production codecs were executed locally during this correction.
Remote CI and any further native acceptance remain separate observations.
Black formatting passed for the changed codec and integration scope.
Steering compliance, Mypy, Ruff, and Pyright passed across the 74 files in that static-analysis scope.
Pyright reported only three pre-existing unrecognized configuration settings, with no code errors or warnings.

The older `Topology/AsmEdge/AsmNames` projection remains a separate qualified naming profile.
It already interprets its first field as text length and requires approach zero.
This change does not silently expand that projection's supported naming domains.

See [the generic-tag count gotcha](../../Gotchas/Conversion/Fusion/FusionGenericTagLengths.md)
and [embedded geometry authoring](FusionEmbeddedGeometry.md).

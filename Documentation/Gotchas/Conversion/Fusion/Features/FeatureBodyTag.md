# Part journal body tag must equal the body map key

## Expectation

A multi-state part journal can allocate entity tags in any order.
The Design body serializer appears to find the body through its own entity reference.

## Actual behavior

`BRepHistorySerializer.mapBodyId` maps an ASM body entity tag to the Design `Body`.
Fusion resolves the body through that key.
A journal whose `BodyNode` carries a different tag opens with a body that has no geometry.

| Variant               | Journal body tag | `mapBodyId` key | Fusion 2706.1.17 result                      |
| --------------------- | ---------------: | --------------: | -------------------------------------------- |
| `BoxProduction`       |                0 |               0 | One 24 cm³ body                              |
| `BoxKitJournal`       |                6 |               0 | `RuntimeError: 3 : The body has no geometry` |
| `BoxKitNoTags`        |                0 |               0 | One 24 cm³ body                              |
| `FilletNativeJournal` |               15 |               0 | `RuntimeError: 3 : The body has no geometry` |

The timeline stays healthy in each failed variant.
The error appeared when the observation script read the body volume.

## Workaround

Claim the body tag before any face tag in the part journal ledger.
`BuildPartBody` rejects a policy whose `BodyKey` is not zero.
A native journal cannot be placed under a Kit Design without a matching body key.

The [variant generator](../../../../../re/Fusion/Reconstruction/FeatureAuthoring/JournalVariants.py) and the [native observation](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Variants/Observation.json) preserve the evidence.

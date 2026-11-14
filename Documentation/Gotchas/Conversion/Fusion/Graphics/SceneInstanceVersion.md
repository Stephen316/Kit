# Older scene headers omit blob features and the instance id

## Expectation

Every saved scene header names nine serializer classes, among them `GraphicsBlobFeatures`. It declares `F360InstanceNode` version 1. An instance node payload holds `IsXref`, then a `u32` instance id.

## Actual behavior

`GraphicsCensus.py` reads the `world` member of all 1,725 corpus documents. 1,480 have one. Two headers name eight classes. They lack `GraphicsBlobFeatures` and declare `F360InstanceNode` version 0. Both are member 0 of `re/Fusion/examples/.f3z/example1.f3z` and of its copy in `re/Fusion/LocalOracle/Bundles`. Member numbers follow `ReadBundle` order.

The world holds one instance node payload. After `IsXref` the next bytes are the `WorldSerializerEndMark` class name. So a version 0 payload has no instance id.

Kit raised `ValueError("Unsupported graphics serializer versions or environment")` for this header.

## Workaround

Accept a header without `GraphicsBlobFeatures`. No Kit layout reads its version. Accept `F360InstanceNode` versions 0 and 1. Read and write the instance id only for version 1.

Each class must still appear once. Every other class must be present at a known version.

## Evidence

- [Cache and package notes](../../../../../re/Fusion/Reconstruction/ReadGaps/CachePackageNotes.md#serializer-header-without-graphicsblobfeatures-member-0)
- [Graphics census](../../../../../re/Fusion/Reconstruction/ReadGaps/GraphicsCensus.json)
- [Cache gap tests](../../../../../tests/convert/formats/FusionCodec/SavedCorpus/CacheGapTests.py), cases `TestCacheMember` and `TestOldInstance`

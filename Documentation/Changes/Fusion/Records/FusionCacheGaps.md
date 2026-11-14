# Fusion cache and package gaps

## Purpose

This change closes the last read and round-trip gaps of the [read gap change](FusionReadGaps.md) in `re/Fusion/examples/.f3z/example1.f3z`. The same documents are in `re/Fusion/LocalOracle/Bundles/kit_production_example1.f3z`. Member numbers follow `ReadBundle` order, as in the sweep.

- The package writer writes material packages with a `Resources` folder tree. Member 7 now round-trips.
- The graphics reader and writer read the caches of members 0, 3, 5, 6 and 8.

Each fix is a general format rule from the corpus. No rule names a file, and no saved byte ships in `src/`. `CachePackageNotes.md` in `re/Fusion/Reconstruction/ReadGaps` records the evidence.

## Results

The sweep in `re/Fusion/Reconstruction/ReadGaps` reads the 1,709 tracked files and their 1,725 design documents. The first sweep ran on the read gap change, the second after the package writer and the third after the graphics rules.

| Measure | Before | Package writer | After |
| --- | --- | --- | --- |
| Files that read | 1,698 of 1,709 | 1,698 of 1,709 | 1,698 of 1,709 |
| Documents that `ReadDocument` reads | 1,704 of 1,725 | 1,704 of 1,725 | 1,714 of 1,725 |
| Read documents that round-trip | 1,698 of 1,704 | 1,700 of 1,704 | 1,710 of 1,714 |
| `NativeMaterial` passes | 1,656 | 1,656 | 1,666 |
| `NativeMaterial` failures | 13 | 13 | 13 |

`Compare.py` shows the package writer changed only the round trips of member 7 in both copies. The graphics rules fixed members 0, 3, 5, 6 and 8 in both copies. No other document changed its read result, model, round trip or material projection. All 18 bundle documents now read and round-trip. The written `world` and stream members of the 10 fixed documents equal the saved bytes.

## Rules

| Rule | Members | Gotcha |
| --- | --- | --- |
| An asset folder with resources links `AssetData`, `Resources` and `Schemas`. Each `Resources` folder holds a `core.xml` asset node and a `cnx.xml`, which links child folders by name or lists resource files next to it. | 7 | [Package resources](../../../Gotchas/Conversion/Fusion/Materials/FusionPackageResources.md) |
| A scene header can omit `GraphicsBlobFeatures` and declare `F360InstanceNode` version 0. A version 0 instance payload has no instance id. | 0 | [Instance version](../../../Gotchas/Conversion/Fusion/Graphics/SceneInstanceVersion.md) |
| `FProteinEffectAttribute` holds one `AssetReference` text. | 5 | [Protein effect](../../../Gotchas/Conversion/Fusion/Graphics/SceneProteinEffect.md) |
| Three override attribute classes hold a linked `PersistentPassiveNodePath`, a target and nested override sets. | 3 | [Overrides](../../../Gotchas/Conversion/Fusion/Graphics/SceneOverrides.md) |
| A version context can name an older version of its link's lineage. | 3 | [Older contexts](../../../Gotchas/Conversion/Fusion/Assembly/FusionOlderContexts.md) |
| A mesh stream can end with bytes that no world item references. Kit keeps them as scene slack and writes them back. | 6, 8 | [Stale tails](../../../Gotchas/Conversion/Fusion/Records/SceneStaleTails.md) |

## Model

- `PackageFolder` trees in `MaterialPackage.Resources` are written by `FolderEntries`.
- `GraphicScene.MeshSlack` and `GraphicScene.FusionSlack` hold the unreferenced tail of each mesh stream.
- `NodePath` holds the `PathEntity` entries of a `PersistentPassiveNodePath`. A `PathEntity` is a segment id and an object id. `CheckDocScene` does not check it, because paths can end in a referenced document.
- `NodeTarget` holds an external `PathEntity` or a node id.
- `OverrideSet` holds a child set, a target and its child sets.

## Evidence

- [Cache and package notes](../../../../re/Fusion/Reconstruction/ReadGaps/CachePackageNotes.md)
- [Package census](../../../../re/Fusion/Reconstruction/ReadGaps/PackageCensus.json) and [graphics census](../../../../re/Fusion/Reconstruction/ReadGaps/GraphicsCensus.json)
- [Sweep before](../../../../re/Fusion/Reconstruction/ReadGaps/Sweep-base.json) and [sweep after](../../../../re/Fusion/Reconstruction/ReadGaps/Sweep-cache.json)
- [Package folder tests](../../../../tests/convert/formats/FusionCodec/Materials/Package/PackageFolderTests.py) and [cache gap tests](../../../../tests/convert/formats/FusionCodec/SavedCorpus/CacheGapTests.py)

## Remaining failures

| Documents | Error | Reason |
| --- | --- | --- |
| `re/Fusion/Reconstruction/ContainerAuthoring/{Generated,StoredOnly,StoredFolders,StoredDirectories,OrderedAct}/AuthoredParameter.f3d` | Primary offsets out of order, or missing directories | Kit research files that Fusion rejected |
| `re/Fusion/LocalOracle/FormDocuments/Cache/{Box,Plane}SurfNone.f3d` | `Unsupported Fusion journal qualified field` | Rewritten caches that Fusion failed to import |
| `re/Fusion/LocalOracle/FormDocuments/Intervals/{Plane4x4/Half,Plane4x4/ColumnRow,Plane4x4/Single,Box/Single}.f3d` | `invalid literal for int()` | Patch program words are doubles. The fix belongs in `BrepCodec/Journal/Spline`. |

The four stale Form files of the read gap change read, and `EmitParsed` still refuses them. Member 7 gives three physical assets to its bodies, so `NativeMaterial` still raises for it. Eleven documents have an undefined body material. None of these is a cache or package gap. The graph material projection raises `Unknown native Fusion entity class` for the 10 fixed documents, as for 1,395 other documents.

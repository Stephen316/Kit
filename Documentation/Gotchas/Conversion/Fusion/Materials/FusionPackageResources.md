# Material packages can hold resource folders

## Expectation

A Fusion material package links two folders under its asset folder, `AssetData` and `Schemas`. Assets that share a definition id share one definition.

## Actual behavior

One member of `re/Fusion/examples/.f3z/example1.f3z` holds a package whose asset folder links `AssetData`, `Resources` and `Schemas`. The reader raised `Unsupported material asset folders`. The copy in `re/Fusion/LocalOracle/Bundles` is the same.

`Resources` is a tree of folders:

- Each folder holds a `core.xml` asset node whose name is the folder name.
- Each folder holds a `cnx.xml`. It either links child folders by name, or lists resources.
- A resource list has the same metadata as the `AssetData` and `Schemas` lists.
- A resource file lies next to the `cnx.xml` that lists it.

Here the tree is `Resources/<asset>/thumbnail/0/<resource>`, six times. Each resource is a PNG thumbnail.

Several appearance assets of this package share one definition id. Each asset has its own definition root in `DefinitionIteratorProperties.bin`. Their definitions differ in `UIName` and `thumbnail`, and a `thumbnail` names a file in `Resources`. The reader raised `Conflicting Fusion material definition identity`.

`DefinitionCensus.py` reads all 1,679 corpus packages. 1,372 definition ids are shared by more than one asset. Only the 4 in this document and its copy have different definitions. Every shared id keeps one schema.

## Workaround

Accept an asset folder that links `AssetData` and `Schemas`, or `AssetData`, `Resources` and `Schemas`. Read the `Resources` tree into `MaterialPackage.Resources`. A folder holds either child folders or resources. Folder and file names are single path segments.

Assets that share a definition id must share its schema. Their definition values are their own. The encoder writes one definition per asset, so this loses nothing.

The package writer links `AssetData`, `Resources` and `Schemas` when `MaterialPackage.Resources` is set. `FolderEntries` writes each folder's `core.xml` and `cnx.xml`, then either the resource files or the child folders, in model order. Every byte comes from the package model. The package of this member round-trips model-exact, like every other package.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#material-resource-folders)
- [Definition census](../../../../../re/Fusion/Reconstruction/ReadGaps/DefinitionCensus.json)
- [Package spy](../../../../../re/Fusion/Reconstruction/ReadGaps/PackageSpy.py)
- [Package writer notes](../../../../../re/Fusion/Reconstruction/ReadGaps/CachePackageNotes.md#material-resource-folders)
- [Package census](../../../../../re/Fusion/Reconstruction/ReadGaps/PackageCensus.json) and [package check](../../../../../re/Fusion/Reconstruction/ReadGaps/TryPackage.py)
- [Package folder tests](../../../../../tests/convert/formats/FusionCodec/Materials/Package/PackageFolderTests.py)

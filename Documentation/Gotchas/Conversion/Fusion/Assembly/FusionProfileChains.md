# A Design class needs its full base chain in JSON

## Expectation

A new Design class needs only its own schema in `DesignClasses.json`.
The native catalog supplies its base classes.

## Actual behavior

The Design profile merges the native catalog first.
The ACT and Browser profiles use `ReadDocSchemas` instead.
That function reads only the three JSON vocabularies and `KAuxiliarySchemas`.

| Profile | Schema sources |
| --- | --- |
| Design | Native catalog, then JSON vocabularies |
| ACT | `DesignClasses.json`, `ActClasses.json`, `BrowserClasses.json`, `KAuxiliarySchemas` |
| Browser | `DesignClasses.json`, `ActClasses.json`, `BrowserClasses.json`, `KAuxiliarySchemas` |

`ClassGroups` checks every JSON class in each profile.
The ACT profile raised `Fusion entity profile is missing an inherited class` after Kit added `DcXRefPCIFeature` alone.
Its bases `DcPlaceComponentInstance` and `DcAssemblyFeature` were only in the native catalog.

## Workaround

Add each missing base class to `DesignClasses.json` with the new class.
`BaseChain.py` prints the chain of a class and writes the missing native schemas as JSON.
Do not edit `NativeClasses.xz`.

## Evidence

- [Schema source list](../../../../../src/convert/formats/Fusion/DocumentCodec/Records/ReadDocSchemas.py)
- [Inherited class check](../../../../../src/convert/formats/Fusion/EntityCodec/Schema/ClassGroups.py)
- [Base chain script](../../../../../re/Fusion/Reconstruction/LinksConfigs/BaseChain.py)

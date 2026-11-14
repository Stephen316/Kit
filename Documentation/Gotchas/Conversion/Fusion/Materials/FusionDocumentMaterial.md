# The document material is not always on a body

## Expectation

Every Fusion document with a material package has one body. The body names one physical asset of the package.

## Actual behavior

`MaterialCensus.py` reads every corpus document and lists each material reference by the class that holds it.

| Holder | Field | Documents |
| --- | --- | --- |
| `Body` | `physicalMaterial` | 1,427 with an asset, 11 empty |
| Mesh body `EA90DA22` | `physicalMaterial` | 84 |
| Form body `FA1F0081` | `physicalMaterial` | 247 |
| `ComponentBase` | `defaultPhysicalMaterial` | 1,266 with an asset, 429 empty |

Many documents have no BRep body. There are 163 documents with only a component default, 59 with only mesh bodies and 29 with `Body` records without a BRep part. In 22 packages, the body asset differs from the component default, so each package holds two physical assets. The old projection raised for all 284 shapes.

## Workaround

Take the physical asset that the body records name. Brep, mesh and Form bodies all count. Without one, take the asset of `ComponentBase.defaultPhysicalMaterial`. Without either, the document states no material, and the projection returns the default `MaterialSpec`.

A body with an empty `physicalMaterial` reference has an undefined material. Fusion reports zero density for it, as [Undefined body materials](UndefinedBodyMaterial.md) shows. The projection raises for it.

Two different physical assets at the same level also raise. Only `example1.f3z` has them. One of its members gives three physical assets to its bodies. The single-body `DocumentSpec` cannot hold them.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#document-material)
- [Material census](../../../../../re/Fusion/Reconstruction/ReadGaps/MaterialCensus.json)

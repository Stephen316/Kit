# Vector named metadata adds an element type name

## Expectation

Each named metadata entry of an entity frame stores a field name, a metatype name and one value. Earlier Kit readers looked up the metatype name in the catalog and rejected names that were not in it.

## Actual behavior

The `SubDSurfaceNode` record of a Form document has the entry `BASEFEAT_PM_BODIES_REF` with the metatype name `Vector`. A third text follows the metatype name. It gives the element metatype, here `PassiveRefMetaType`. The value is a counted sequence of elements of that metatype.

| Owner class | Field | Metatype | Element metatype | Items | Records |
| --- | --- | --- | --- | --- | --- |
| `SubDSurfaceNode` | `BASEFEAT_PM_BODIES_REF` | `Vector` | `PassiveRefMetaType` | 1 | 29 |
| `Body` | `FORMFEAT_DM_SUBD_REF` | `PassiveRefMetaType` | None | None | 29 |

The two entries join the converted body and the T-spline surface node in both directions. The sequence item refers to the `Body`. The `Body` entry refers back to the `SubDSurfaceNode`.

## Workaround

Read the element metatype text only when the metatype name is `Vector`. Store it in `NamedMetadata.ElementName` and keep it empty for scalar entries. Reject a `Vector` of `Vector` and an element metatype that is not in the catalog.

## Evidence

- [Named metadata census](../../../../../re/Fusion/Reconstruction/FormDocuments/NamedVectors.json)
- [Form round trip](../../../../../re/Fusion/Reconstruction/FormDocuments/RoundTrip.json)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)

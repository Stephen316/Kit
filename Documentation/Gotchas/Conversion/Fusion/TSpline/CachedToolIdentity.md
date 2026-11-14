# Form tool cache needs a top-entity identity

## Expectation

The snapshot `BRepSerializer.topEntityPIDGenerator` is runtime bookkeeping. An empty generator is safe in a new document.

## Actual behavior

Fusion deletes the converted Form body on `computeAll` when that generator gives the cached tool entity no identity. Timeline health and Form health stay 0. The body count drops to 0.

Every local Form archive gives the cached entity an identity in that generator.

| Record | Field | Value in all 42 archives |
| --- | --- | --- |
| `ETCachedTopology` | `cachedEntityId` | 0, 1 or 2 |
| `topEntityPIDGenerator` | `scanOrderIndex` | (`cachedEntityId`) |
| `topEntityPIDGenerator` | `nextId` | `cachedEntityId` + 1 |
| `topEntityPIDGenerator` | `addressOfTopEntities` | One entry |

A one-field probe on the box isolates the cause in Fusion 2706.1.17. Every Kit variant below also has `bodyType` 2.

| Variant | Change | Bodies after `computeAll` |
| --- | --- | --- |
| `KitSolid` | Kit box with an empty top-entity generator | 0 |
| `KitSolidCache` | Adds the native mass `cache` and `facetVersion` | 0 |
| `KitSolidIds` | Adds the native body `PassiveIdGenerator` | 0 |
| `KitSolidCacheIds` | Adds both | 0 |
| `KitSolidTop` | Top-entity generator with `nextId` 1, `scanOrderIndex` (0) and the native address | 1 solid |
| `KitSolidTopZero` | Same generator with address 0 | 1 solid |
| `NativeBlankCache` | Native box with the Kit `cache` and `facetVersion` 0 | 1 solid |
| `NativeBlankIds` | Native box with an empty body `PassiveIdGenerator` | 1 solid |
| `NativeBlankTop` | Native box with an empty top-entity generator | 0 |

The mass cache and the body `PassiveIdGenerator` do not affect the result. The stored address value does not affect it either.

## Workaround

Give the cached tool entity identity 0. Write `scanOrderIndex` (0), `nextId` 1 and `addressOfTopEntities` (0). `LinkFormMut` writes these values.

## Evidence

- [Variant probe](../../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/Variants/ProbeVariants.json)
- [Variant documents](../../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/Variants/Variants.json)
- [Variant builder](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/MakeVariants.py)
- [Cache identity census](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/SolidityCensus.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/NativeAcceptance.json)
- [Form body type](FormBodyType.md)

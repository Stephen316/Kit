# Form body type follows shell closure

## Expectation

A source-free Form document can store any body type. Fusion derives solidity from the converted BRep shell.

## Actual behavior

Fusion reads `Body.bodyType` when it opens the document. A closed converted body with type 4 opens as a sheet without volume.

Every local Form archive follows one rule.

| Converted body | `bodyType` | Archives |
| --- | --- | --- |
| Closed, every coedge has a partner | 2 | 18 |
| Open, at least one coedge has no partner | 4 | 24 |

A one-field probe on the box shows the effect in Fusion 2706.1.17.

| Variant | Change | Solid when loaded | Bodies after `computeAll` |
| --- | --- | --- | --- |
| `KitBase` | Kit box before the fix, with `bodyType` 4 | No | 0 |
| `KitSolid` | Kit box with `bodyType` 2 | Yes | 0 |
| `NativeBase` | Native box | Yes | 1 solid |
| `NativeSheet` | Native box with `bodyType` 4 | No | 1 solid |

`computeAll` rebuilds the native body as a solid. It does not keep the Kit body. [Cached tool identity](CachedToolIdentity.md) explains that loss.

## Workaround

Write `bodyType` 2 when every converted edge has two coedges. Write 4 otherwise. `LinkFormBodyMut` applies this rule.

## Evidence

- [Body type census](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/SolidityCensus.json)
- [Variant probe](../../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/Variants/ProbeVariants.json)
- [Variant documents](../../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/Variants/Variants.json)
- [Native acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/Sourceless/NativeAcceptance.json)

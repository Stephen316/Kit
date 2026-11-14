# The converted Form surface is exact, not a cache

## Expectation

Each converted Form face is a `t_spl_sur` spline surface. It embeds the complete T-spline program and a region index. Its B-spline data looks like an approximation cache that the kernel could refit from the program on restore.

## Actual behavior

The stored B-spline surface is the exact face geometry. The record adds the T-spline program and the region index for editing.

Fusion 2706.1.17 confirmed this with three variants of the native plane and box documents.

| Variant | Opens | Body after open and `computeAll` |
| --- | --- | --- |
| Control | Yes | Plane 3.9099999999999993 cm², box 23.560443509000663 cm² |
| Approximation level none | No, `InternalValidationError` | None |
| Interior poles moved by 0.05 cm | Yes | Plane 3.9256276041882643 cm², box 23.64507885678318 cm² |

Fusion uses the moved poles as the face geometry and reports healthy Forms. A changed `TsSurface.bConversionFailed` flag does not start a conversion either. A stale body stayed stale with the flag set, after `computeAll` and after an empty edit.

## Workaround

Write the exact conversion of the cage in every converted face. Do not omit the B-spline data, and do not write an approximation. Use `ConvertGrid` for the qualified grid cages and `ConvertCage` with the general cage rules for every other cage. Refuse a cage that the rules cannot convert exactly.

## Evidence

- [Cache variant preparation](../../../../../re/Fusion/Reconstruction/FormDocuments/PrepareCache.py)
- [Cache probe with the level-none refusal](../../../../../re/Fusion/LocalOracle/FormDocuments/Cache/Probe.json)
- [Grid acceptance with the moved-pole variants](../../../../../re/Fusion/LocalOracle/FormDocuments/Grid/NativeAcceptance.json)
- [Conversion flag probe](../../../../../re/Fusion/LocalOracle/FormDocuments/Flag/Probe.json)
- [Stored body authority](StoredFormBrepAuthority.md)

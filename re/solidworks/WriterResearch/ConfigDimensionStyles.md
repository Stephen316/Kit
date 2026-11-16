# Config-0 saved dimension styles

`WriteSavedDimensionStyles` follows the [complete inline detail start](ConfigDetailOpening.md) and writes the ten generation-19000 styles in the order called by `moDimDefs_c::Serialize`. Their common base contains alignment, tolerances, text, length and angle formatters, and leader and extension appearance. Derived styles append their own fields. The shared part allocator retains the class originally registered by the [units table](ConfigUnits.md).

## Native ownership

Addresses are virtual addresses in the 34.4.1.1011 [pinned DLL](../records/P04ArchiveWalk.md#inputs).

| Owner | Native source |
| --- | --- |
| Inline order | `moDimDefs_c::Serialize` at `0x3c86be19`–`0x3c86bf47` calls the ten embedded styles in wire order. Its constructor at `0x3c7eec76`–`0x3c7eecf2` establishes the classes corresponding to those members. |
| Base dimensions | `moBaseDimDef_c::Serialize` at `0x3c8666a0` writes the base settings in member order 0x8–0x74, 0x80–0x98 and 0xe0. It skips the layer data on the -1 branch at `0x3c86683f`. Constructor `0x3c7ee780` sets default tolerances, automatic fit, and the two tolerance precision flags. The known style overrides follow the standard and subtype constructors at `0x3c7f0ac0`, `0x3c7eea30` and `0x3c7eef20`. Named setters at `0x3c7f69c0` and `0x3c7f5250` confirm bits 6 and 7 for primary and dual tolerance precision. |
| Formatter ownership | The base calls its +0xf0 length and +0xf8 angle formatters inline at `0x3c866a5d` and `0x3c866a6d`. The length serializer at `0x3c91cb30` writes its own +0xb0 selector and +0xb8 pointer. The ordinary angle style stores a null length child. The remaining nine styles allocate a length child under the existing class tag, with unit selector 3 and a null subordinate pointer. Both ordinary angle and angular ordinate have the primary selector 2. The other eight primary selectors follow the actual document length setting. The linear formatter's previous numeric value is supplied separately. |
| Appearance | The base calls the character format and two inline `uiLFConfig_c` objects at `0x3c866a7d`, `0x3c866a8d` and `0x3c866aae`. The native line-font constructor at `0x3c858380` initializes its inherited width via `utLineWidth_c`. The witnessed plain character settings use the same constructor as the detail heading, with their own explicit font input. The base returns extension style, inward tolerance setting and zero-removal fields at `0x3c866ae0`–`0x3c866b53`. |
| Derived returns | Linear `0x3c86e9a0`, angle `0x3c865960`, radial `0x3c86fb00`, hole callout `0x3c86e530`, ordinate `0x3c86f8a0`, chamfer `0x3c867020`, diameter `0x3c86b820` and angular ordinate `0x3c865860` file their own scalar returns after the common base. Arc length `0x3c865f50` and the general base file no suffix in this profile. |

## Pinned comparison

The 5,026 bytes occupy +993 through +6019 from the relation return in each of the six P01 and eight P03 saves at capture revision `466dcb172dfa3803463e07ccde963ba01671d200`. Both inch saves use the document length selector 3. The other twelve use selector 0. The saved linear formatter's previous value is either 0 or 20, and differs from the earlier unit-table previous value in twelve saves. The reported rows retain both distinct values.

The reused length class occupies slot 10 and the nine newly owned objects occupy slots 57–65 in P01 and 61–69 in P03. No other style record allocates. The independent annotations reader then reaches offset +7975. [Hosted exact comparison](VerifyDimensionStyles.py)

The replay SHA-256 is `5fe2c5a1d827b0eecd71310587752b208a99201a5f1891d4f62e5470ca83312e` over the source receipt hashes, style and annotation boundaries, newly allocated slots, both formatter values and style interval digests. The rest of the saved detail continues with annotations, tables, labels, finish, note and weld data, tolerance settings and the final detail options.

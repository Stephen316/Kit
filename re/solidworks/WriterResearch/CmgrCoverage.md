# Generation-19000 CMgr construction coverage

This census covers the six P01 sketch-only saves and eight P03 single-boss saves from capture revision `466dcb172dfa3803463e07ccde963ba01671d200`. It follows the [pinned receipts](CmgrVisual.md#inputs-and-reproduction) and the installed serializer evidence linked below. Ranges are half-open byte offsets in the decompressed `Contents/CMgr` stream. Construction status applies to the individual record and the measured shape.

| Record | P01 | P03 | Current construction boundary |
| --- | --- | --- | --- |
| [Manager, inherited feature and part opening](CmgrOpening.md) | 0–278 | 0–278 | Read-only. Opening node state and feature stamps still need emitter inputs. |
| [Visual properties before DSPBR](CmgrVisual.md#saved-spans) | 278–795 | 278–795 | Read-only. The material and RealView fields belong to the enclosing visual record. |
| [Default color DSPBR](CmgrVisual.md#research-encoder) | 795–1095 | 795–1095 | Constructed from the explicit packed visual color and measured appearance profile. |
| [Part inherited feature and base header](CmgrMiddle.md#inherited-feature) | 1095–1234 | 1095–1234 | Read-only. The header includes independent feature stamps and the variable base members at `+0x85c,+0x860,+0x670`. |
| [Mass record](CmgrMiddle.md#mass-property-record) | 1234–1488 | 1234–1488 | Constructed. P01 uses native empty defaults. P03 uses certified cuboid bounds and density, with numeric agreement for geometry and retained native residuals. |
| [Base configuration collections](CmgrMiddle.md#base-configuration-collections) | 1488–1654 | 1488–1662 | Read-only. The saved solid count and accuracy byte have independent owners. The remaining model state and collection inputs need construction. |
| [Linked atom map](CmgrAtoms.md#linked-atom-map) | 1654–1658 | 1662–1724 | Constructed. The empty map preserves next index 9. One P03 link advances from 9 to 11. |
| [Base return](CmgrAtoms.md#linked-atom-map) | 1658–1692 | 1724–1758 | Read-only. The signed values `(2,0,0)` at the closing words have source members `+0x4c8,+0x4cc,+0xa80`. Their generation inputs are still open. |
| [Inline part and part return](CmgrAtoms.md#inline-part-configuration-object) | 1692–1804 | 1758–1878 | Constructed for the empty optional members and ordered zero-valued atom map. |
| [Manager configuration aliases](CmgrAtoms.md#part-return-and-manager-aliases) | 1804–1818 | 1878–1892 | Read-only. Both references resolve to the already allocated part. A future emitter needs its actual allocation. |
| [External file and manager continuation](CmgrTail.md#external-file-and-referenced-configuration) | 1818–first list | 1892–first list | Constructed from typed file metadata in the standalone profile. The hosted byte and allocator comparison covers 25 archive spans and awaits execution. |
| [Manager lists and feature stamps](CmgrTail.md#root-and-feature-stamps) | First list–EOF | First list–EOF | Constructed with explicit feature stamps and the enclosing allocator. |

| Captures | External path | First list | EOF | Map from first list to EOF |
| --- | --- | ---: | ---: | --- |
| 2 P01 | Empty | 1963 | 2073 | 14 to 17 |
| 4 P01 | Prior save | 2193 | 2303 | 14 to 17 |
| 2 P03 | Empty | 2037 | 2159 | 16 to 19 |
| 1 P03 | Empty | 2039 | 2161 | 16 to 19 |
| 5 P03 | Prior save | 2267 | 2389 | 16 to 19 |

The 14-file read-only replay advances from the opening allocations to the visual return, then checks the mass header, typed collections, independent atom links and part return. The two active configuration aliases preserve the part identity. The external object's two CStrings determine the next boundary. The manager terminal reader then checks both lists through EOF. Every row covers exactly its saved stream length.

The replay SHA-256 is `e9bdd8e32e2c6cbea7d3f3013d094f0d975e5cd89528ae683575adc8b7d8f3eb`. For each file in receipt order, compact JSON records its SHA-256, the consecutive boundary offsets from zero through EOF, the next indices before and after the link map, at the first list and at EOF, and the linked-map slice SHA-256. Use the typed walkers and field layouts linked in the table. The offsets are evidence for the pinned files. Future construction takes model inputs and uses the allocator to derive positions.

The remaining record constructors and their composition into a generated native part are still open. Native acceptance requires the licensed open, rebuild, edit and save sequence with healthy controls.

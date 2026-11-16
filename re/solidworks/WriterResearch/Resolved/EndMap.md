# Resolved configuration end map

The generation-19000 P01 and P03 ordinary parts store an empty MBSM data-object map at the end of `Contents/Config-0-ResolvedFeatures`. The map follows the last complete feature return. Its zero entry count is one little-endian Windows signed long and allocates no archive slots. The research encoder derives the count from the supported empty map. Its reader requires exactly four bytes from the caller's final feature cursor to EOF. [Research codec](EndMap.py)

## Native ownership

The following preferred virtual addresses are from SOLIDWORKS 34.4.1.1011. The pinned modules have these SHA-256 values.

| Module | SHA-256 |
| --- | --- |
| `doccplu.dll` | `120e1d5c359f5895d9785325995ebfaafc790ef7d74fe4fb0e242303f933939b` |
| `slduiu.dll` | `88a8d1bff1e8d7b5cad7e456096c4e32c8d84d4046fc5c09ce26f2563ee8e2a6` |
| `sldmodu.dll` | `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99` |
| `sldmfcu.dll` | `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6` |
| `swccu.dll` | `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49` |

`SolidStorage_c::iSaveModelDefn` calls `uiModelDoc_c::saveResolvedFeatureList` at `0x1800258ad`. The save method appends the UTF-16 `-ResolvedFeatures` suffix at `0x49737e86`. It copies the pointers in model member `+0x60` into a temporary `suObList`, writes the archive's inherited map count from `+0x50` at `0x49738173`, then calls `suObList::Serialize` at `0x49738184`. That export at `0x3c8dd4d0` delegates to `su_CObList::Serialize` at `0x31a56530`. The binary route writes the compact list count at `0x31a56662` and serializes the counted object pointers before returning at `0x31a5672e`.

The parent save then reaches `moPartConfiguration_c::SerializeMBSMDataObjects` at `0x4973822d` on its guarded part route. The method at `0x4c22ec70` builds a separate filtered data-object map, calling its serializer at `0x4c22ee43`. The map serializer at `0x4c20e9a0` writes the entry count through `su_CArchive::operator<<(long)` at `0x4c20e9bb`. An empty map reaches the sentinel and returns without any key or pointer records. The save path also contains optional deferred database callbacks. This research scope is the ordinary binary streams in the pinned receipts.

The corresponding `moModel_c::loadResolvedFeatures` consumes the generic object list at `0x4b5889e9`. It later calls the MBSM reader at `0x4b588b6c` when its part/configuration guards hold. The modern generation reads the map at `0x4c22ef35`, beyond the historical additional scalar branch for generations earlier than `0x141e`. The separate `moNodeList_c` virtual serializer at `0x4c1775a0` also writes a zero after its list, but the separate resolved stream explicitly calls the generic `suObList` export. Its inherited map header, feature count, last feature return and terminal MBSM count are separate fields.

## Archive controls

Read-only replay verified every native archive size and SHA-256 against the pinned receipts and checked the measurement receipt digests. The packaged rectangle reader supplied the P01 profile return cursor and the P03 extrusion return cursor. Each exact end-map span has SHA-256 `df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`. [P01 receipt](../../../automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json) · [P03 receipt](../../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

| Discovery lane | Inherited map count | Feature entries | End map half-open spans in bytes | Next archive index |
| --- | ---: | ---: | --- | ---: |
| P01, six saves | 106 | 18 | Baseline A 11895–11899, YZ 11967–11971, other four 12125–12129 | 250 |
| P03, eight saves | 111 | 19 | Baseline A 15033–15037, YZ 15103–15107, negative 15031–15035, other five 15261–15265 | 306 |

The hosted P01 check replaces the footer after the captured profile and rereads the original profile with the packaged parser. The P03 check appends the constructed footer after the generated display and extrusion return, retaining the five unresolved end-specification properties for the readback comparison. Whole-stream authoring, nonempty MBSM data, other configurations and licensed native acceptance remain separate research boundaries. [P01 hosted check](../../../../tests/Research/Archives/SolidWorksListEndTests.py) · [P03 hosted check](../../../../tests/Research/Archives/SolidWorksEndVerify.py)

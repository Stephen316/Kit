# Ordinary Config-0 part return

The ordinary generation-19000 part closes the model after its absent bend-note format with a 17-byte lead into the mass caches. After the cache list, a four-byte part field introduces the 195-byte schema-1 `moPrtExplViewManager_c`. The part ends 36 bytes later. The manager allocates one class and one object. All six P01 saves end at archive index 106 and all eight P03 saves end at 111. `WriteMassLead` and `WriteConfigEnd` surround the existing [mass cache list](../ConfigMass/CacheList.py) on the same allocator.

The addresses below refer to `sldmodu.dll` `34.4.1.1011`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. The model emits its empty text-pair table at `0x4c2349e4`. The enclosing part path at `0x4c235040` calls the model serializer at `0x4c23508a` before saving its own four fields. These are `+0x14f8` at `0x4c2350b5`, byte `+0x1428` at `0x4c2350c5`, `+0x14d8` at `0x4c2350d4` and `+0x152c` at `0x4c235111`. The first three retain their initialized zeroes. The ordinary value for `+0x152c` is one, which has native assignments at `0x4c1c3c24` and `0x4c1c66d1`. `0x4c2354bf` starts the cache list. After its last occupied slot and conditional replacement index, `0x4c2355a8` writes the zero part field at `+0x1400`.

`createExplViewManager` at `0x4baab450` constructs the feature base and calls `moNode_c::onCreate` at `0x4baab502`. The latter claims a `moHeader_c::getNewID` result at `0x4c03cab5` and stores it in the node at `+0x08`. The lightweight node store at `0x4c178b47` writes this document tree identity. Its owner is separate from the archive object slot. The optional name and lightweight child routes are empty. The inherited feature uses its own FILETIME through the shared [configuration-feature codec](../CmgrInherited.py), including both dated and zero times in the pinned saves.

The manager serializer at `0x4b66d0b0` calls `moFeature_c::Serialize` first. It then writes nullable pointers `+0x358` and `+0x360`, the double at `+0x398`, and signed words at `+0x3a0` and `+0x3a4`. The default constructor at `0x4baa9a30` initializes those members to null, null, `0.0`, `-1`, `-1`, and creates an empty word map at `+0x368`. The serializer calls the inline map at `0x4b66d228`.

| Part return field | Store | Ordinary value |
| --- | --- | --- |
| Presentation identity `+0x1698` | `0x4c23561e` | Caller-owned tree ID. After creating the exploded manager, the native new-ID path obtains the next header ID at `0x4c2317e4`. |
| Configuration identity `+0x169c` | `0x4c235676` | Caller-owned configuration ID. `setConfiguration` copies it from its pointed configuration state at `0x4c1bc178`. |
| Supplemental linked data | `0x4c235798` | Absent. The populated branch requires two pointers. |
| Sheet-metal extension | `0x4c235910` | Empty count on the ordinary part. |
| Cached bounding boxes | `0x4b79780b` | Empty count. The loader's populated branch reads `moCachedBoundingBoxData_c`. |
| Part defeature state `+0x18c4` | `0x4c2359a4` | Zero. `setFaceMapOnDefeature` has the separate enabled assignment. |
| Unsigned word `+0x18c8` | `0x4c2359fc` | Constructor value `101` at `0x4c1bd134`. |
| Assembly defeature state `+0x18f0` | `0x4c235a54` | Zero. |
| Body list `+0x1bd0` | `0x4c235aac` | Zero. The populated branch writes additional body atom IDs. |

In each of the 14 pinned saves, the exploded view and subsequent presentation IDs are 19 and 20 and the separate configuration identity is 1. The constructor accepts those identities from the enclosing graph and requires the consecutive ordinary tree allocation. The source-to-range digest map across the generated fields on both sides of the cache list is `cd16fa11ca352bbc39545ff7c5d8c3afd78f4bdc61ef611cc1f92150c39c8e34`. The hosted verifier compares every generated field and passes the record through the packaged reader to exact stream end and the inherited resolved-feature allocation map. Native open, rebuild and edit remain open. [Hosted verifier](../VerifyCfgPartEnd.py)

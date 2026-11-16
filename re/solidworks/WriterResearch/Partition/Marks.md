# Configuration and blind-boss partition marks

The generation-19000 configuration and resolved boss save separate `moPMarkRecord_c` objects that each contain one signed kernel identifier. This identifier belongs to a Parasolid partition. The surrounding SOLIDWORKS archive map has its own class and object indexes. `ReadOrdinaryMap` identifies the configuration's typed marker definition and `ReadRectPart` exposes the boss marker payload as `partition_state` after following its inherited class reference. [Config model-list ownership](../ConfigScene/ModelLists.md) [Boss chooser boundary](../BossChoice.md)

The six pinned P01 controls and eight pinned P03 controls from capture revision `466dcb172dfa3803463e07ccde963ba01671d200` all store configuration marker ID 3 and following model word 1. Every P03 boss allocates archive object 293, while its kernel identifier changes with the saved edit history.

| P03 save | Boss kernel marker ID |
| --- | ---: |
| Baseline A | 7 |
| Baseline B | 9 |
| Width edit | 11 |
| Height edit | 15 |
| Depth edit | 19 |
| Inch units | 23 |
| YZ reauthor | 7 |
| Negative-direction reauthor | 7 |

## Native ownership

The installed SOLIDWORKS 34.4.1.1011 modules establish these paths.

| Module | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99` |
| `sldgcu.dll` | `797f81cba7080ea6edd37eca36abeaa9a2c0539f9319b980b92abc5a875edf24` |
| `sldgciParau.dll` | `af3bb6440b9b78445a084c1ae2ce6787f6db06aa70690c43cd9ac041e64db017` |
| `pskernel.dll` | `2a0b45e9778c42acaa9a955d4dd4826c8892ac3be08532b819778c7989c66969` |

The configuration path at `0x4c334a70` creates a temporary empty partition and calls `gcPartition_w::createPMark(0)` at `0x4c334ab2`. It gathers and validates the model partition's current marks. It substitutes the temporary mark into the first array entry at `0x4c334b4d` and merges the model and temporary partitions at `0x4c334b62`. On success, it installs the mark handle through the model's `+0xe38` setter at `0x4c334bb4`. The store at `0x4c233d3c` writes that object.

`moAtomFeature_c::saveBodyTagForRollback` obtains the actual model partition at `0x4b7152a0`. Its `0x4b71569e` call creates another mark when the partition is present. The setter at `0x4b717530` owns the corresponding record at feature `+0x3d0`. The rollback-data branch serializes it at `0x4bb0b0bb` when the save context and kernel setting allow rollback data.

Both records use `moPMarkRecord_c::Serialize` at `0x4bb19b30`. It calls `gcPMark_w::getId` for a live mark and otherwise preserves the detached stored ID from `+0x18`. The `sldgciParau.dll` bridge calls `PK_PMARK_ask_identifier` at `0x3306a31b`. The kernel writes the validated mark's identifier from its `+0x48` member at `0x1803cd1e4–0x1803cd1e7`.

## Native allocator

- Creating an empty partition through `PK_PARTITION_create_empty` reaches the initializer at `0x18093c9f0`. It seeds the partition's last allocated mark identifier at `+0x90` to one at `0x18093cb0e`. Its initial mark's identifier at `+0x48` is one at `0x18093cb96`.
- The ordinary allocation under `PK_PARTITION_make_pmark` enters `0x181422330`. The new-mark route at `0x181422690–0x18142269c` increments the partition's `+0x90` counter and writes that result into the new mark's `+0x48` member. An existing and previously initialized counter is sufficient to compute the next mark on this route.
- The partition merge enters `0x18093ece0`. It walks the transferred marks and checks their partition ownership at `0x18093fa70–0x18093fa7e`. A mark moving to the destination is assigned the next destination identifier at `0x18093fad1–0x18093fadd`. The temporary mark's old identifier therefore does not determine the final configuration marker. Other branches retain the already-owned mark.

The remaining fresh-generation dependency is the exact set and order of intermediate mark operations on the initial model partition, including the mark list selected for merge and the rebuild operations before the first boss save. The constructor seed and increment are source-backed. The measured final IDs 3 and 7 alone cannot identify the intermediate operations. The model's separate `+0x1010` value 1 also remains a caller input. The ordinary writers should receive interpreted marker identities from their enclosing generated lifecycle until that sequence is established.

The licensed P03 omission campaign preserved the configuration and resolved marker fields when omitting the physical partition streams. Its fresh reopen and edit evidence applies to those unchanged numeric references. A generated lifecycle or a changed marker payload needs separate licensed confirmation. [Licensed omission evidence](../../../../Documentation/Changes/Research/Writers/SolidWorks/SolidWorksArchiveOmissions.md)

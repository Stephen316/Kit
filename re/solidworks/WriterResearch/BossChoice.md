# Generation 19000 ordinary boss choosers

`WriteBossChoice` follows the [boss opening](BossOpening.md). It files two cap faces and their ordered sketch-edge occurrences, then files a second chooser that aliases those cap and edge objects. The two bounding-centre objects have identical scalar state and distinct archive allocations. The caller supplies the enclosing boss and trim file owners, the saved line IDs, and the cap order, timestamp and bounding cache.

## Native ownership

Preferred addresses refer to installed SOLIDWORKS `34.4.1.1011` `sldmodu.dll`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.

| Group | Native store evidence |
| --- | --- |
| Outer chooser entries | The `moAtomFeature_c` store around `0x4bb0acbf–0x4bb0af87` files the chooser selector state, first chooser pointer and later replay. The presence fields and the typed `moExtrusion_c` aliases follow the single-body branch in all eight saves. |
| Each chooser payload | `moPerBodyChooserData_c` archive slot 5 at `0x4c271900` writes three compact object arrays at `0x4c27192f`, `0x4c271952` and `0x4c2719ac`. The chosen cap pair is the first array. The second is empty and the third holds one bounding-centre record. The two signed members at `0x4c2719c2` and `0x4c2719ce` default to zero in constructor `0x4b75d890`. The `su_CDWordArray` at `0x4c2719df` and the final signed member at `0x4c2719e8` save `[0]` and `0` on this branch. |
| Face envelopes | `moFaceRef_c` archive slot 5 at `0x4bba88d0` calls the enclosing face serializer at `0x4bba88f9`. It writes the two doubles at `0x4bba2af6` and `0x4bba2b04`; the constructor at `0x4b747e00–0x4b747e0e` initializes both to `1e100`. The entity writer at `0x4bba2b11` files the ordered children, with a null first and final identity bracketing the cap and four sides. The optional face additions are absent in this lane. |
| Cap and side identity | `moEndFaceSurfIdRep_c` uses archive slot 5 at `0x4bba3480`. `moFromSktEntSurfIdRep_c` uses `0x4bba9930`. Both call the shared identity body at `0x4bba7a20`; the compact `moFR_c` links to the same boss feature and document file. The repeated envelopes retain the exact old surface object indices. |
| Bounding centre | `moBBoxCenterData_c` archive slot 5 at `0x4c270370` writes the type at `0x4c2703af`, the point via `mgPoint_c::save` at `0x4c2703d5`, and the enclosure diameter at `0x4c27040e`. |

## Receipt-pinned evidence

In all eight saves the 742-byte chooser interval advances the map from 260 to 293, adding five classes and 28 objects. It ends before the partition fields and the class-reference allocation of its marker at slot 293. The first chooser and repeated chooser occupy slots 261 and 289. Their centre allocations occupy slots 288 and 292. Each cap edge list maps to the same closed four lines independently measured by the native application. Front forward uses orders `(4,3,2,1)` and `(4,1,2,3)`. Right and Front reversed exchange those orders. These are measured examples. The constructor takes the ordered identities as inputs.

The saved bounding state equals the independently measured prism's centre and diagonal in five files. The width, height and depth edits retain the original 40 × 20 × 10 mm box cache. Thus the existing saved cache is independent caller state for reconstruction. Fresh generation can derive a candidate cache from the requested prism, with native rebuild still required.

Run `python -B re/solidworks/WriterResearch/VerifyBossChoice.py --read-only` in the Kit environment. The exact report SHA-256 is `bd4477321aea633bfb06579621443054a0bdefc134b081195d413b4fbef1f2a6`. Hosted `CheckBossChoice` compares both materializations, aliases and the complete map. The [partition and signed end](BossEndOpen.md) follow.

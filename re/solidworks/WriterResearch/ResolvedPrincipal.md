# Resolved principal datum planes

`WriteResolvedPlanes` resumes the [later resolved folders](ResolvedFolderTail.md) and writes the three standard Front, Top and Right datums for the ordinary generation-19000 part. Each plane retains its own feature FILETIME and update state, and allocates its name and nested default plane data. The three standard identities are tree IDs 2, 3 and 4. The first plane allocates both classes, while the later planes use the original class registrations. The writer ends before Origin.

## Native boundaries

Addresses below refer to the [pinned SOLIDWORKS 34.4.1.1011 sldmodu image](ConfigRoot.md#native-field-authority).

| Owner | Ordinary standalone branch |
| --- | --- |
| `moRefPlane_c` | Runtime descriptor `0x4daeea90` uses the factory `0x4c25e890` and constructor `0x4c2d02f0`. The primary `0x4d16c1f8` table's archive function at `0x4c2744e0` uses the inherited plane body at `0x4c274280`, whose first call is the shared atom-feature path `0x4bb0a3b0`. Its `0x4bb0a3d7` call enters `moModelFeature_c::Serialize` at `0x4bb18580`. The observed ordinary named node and inherited feature body use the same grammar as the resolved folder and CMgr bookkeeping. |
| Empty atom attachment | The model-feature tail writes its preceding member at `0x4bb185c0`. The shared atom-feature path owns the source collections and keeper, including `0x4bb0a412`, `0x4bb0a422`, `0x4bb0a435` and `0x4bb0a44e`. Its later transfer selectors, atom reference, body chooser, local partition and map fields are the typed [ordinary plane atom reader](../../../src/convert/adapters/solidworks/Resolved/PlaneAtom.py) sequence. All 42 datums take the empty attachment branch with a null atom, recorded body chooser flag 1 and a local partition record with a null payload. The research codec restricts the remaining scalar placeholders to that witnessed empty state. |
| Plane name location and data pointer | `0x4c2742ee` stores the plane name location through `mgPoint_c::save`. The rest of that body writes mode, one member at `+0x6e0`, the null feature reference at `+0x6e8` and the `+0x6f0` tail. `0x4c274528` files the typed data object owned by `+0x6f8`. |
| Default plane data | Runtime descriptor `0x4daef7b0`, factory `0x4c25fde0` and table `0x4d135f70` select `0x4c2745b0`. It calls virtual slot `+0x150` at `0x4c278930`. That routine files the world root and normal, `mgXform_c::save`, four border dimensions and a null edge. It stores three signed members from `+0x50` onward and an explicit zero byte at `0x4c278a2d`. After the display root, it files the `+0x5c`, `+0x60` and `+0x64` fields, then three optional pointers. The constructor `0x4c2d83c0` establishes the preserved defaults, including `(0, -4, -4)`, `(1, 0, 0)` and the null pointer members. |

The geometric origin of each datum is the document origin. Normals are +Z, +Y and +X respectively. Front's identity transform omits the basis. Top uses in-plane coordinates +X and −Z, and Right uses −Z and +Y. The saved direction and exact right-hand basis follow the same typed plane boundaries accepted by the packaged reader. The ordinary transform has unit scale, zero shift and no nested transform.

## Derived plane display

`moModel_c::iResizeDefRefPlanes` at `0x4c029710` calls `moRefPlane_c::UpdateBorders` at `0x4c02979e`. `moRefPlnData_c::UpdateBorders` selects the default-data border function at `0x4c2f3c20` through table slot `+0x188`. Its size helper `0x4c2ee310` transforms the model box to the plane frame, takes absolute in-plane spans and uses `iCheckBorders` at `0x4c2e8af0`. The latter dispatches to `0x4c2e8bb0`, which uses a length threshold of `1e-7 m` and extends a collapsed axis from a surviving in-plane span. Each side then expands by 0.05 of that span at `0x4c2f3d11` and `0x4c2f3d2b`. This is a 10% total enlargement. At `0x4c2f3dd3`, intersecting a line through the model box center along the datum normal sets the display root. `updateNameLocation` at `0x4c2f4940` resolves the correct border corner in the saved frame.

`BuildPlaneView` applies those rules to the measured ordinary axis-aligned model bounds. It admits a useful projected span and refuses a point-sized projection. The renderer quantities depend on the physical model or sketch extents. The geometry of the origin and the three plane equations remains fixed. The constructor takes the derived view separately from the feature bookkeeping, which does not come from geometry.

## Replay

```sh
python re/solidworks/WriterResearch/VerifyResolvedPlanes.py --read-only
```

The 14 pinned P01/P03 saves contain 42 native `RefPlane` features at spans `2944–3483`, `3483–4049` and `4049–4619`. The same three licensed tree names and ModelHeader tree IDs bind to each decoded datum. All display coordinates and borders agree with the independent world bounds within `1e-15 m`, including the planar box collapse, signed reverse boss, and YZ sketch and boss variants. The source map advances by 11 slots, from 147 to 158 for P01 and from 152 to 163 for P03. The packaged system reader agrees on the entire class and object map and the Origin boundary.

The receipt-order replay SHA-256 is `58ea10925023d080a670a3e10884043677ad584cca704864f52a47860bea86c2`. Hosted `CheckResPlanes` compares exact constructed bytes and complete object maps with the saved range, in addition to the separate geometry comparison. The current replay is read-only. Subsequent owners and native application acceptance remain open.

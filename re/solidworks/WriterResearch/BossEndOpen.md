# Generation 19000 boss partition and signed blind end

`WriteBossEndOpen` continues at the [chooser return](BossChoice.md). It constructs the local partition reference, the ordinary empty atom and body return fields, and the beginning of the signed single-sided blind end. The next byte belongs to [the active distance display](Display/Boundaries.md), which uses the same archive map.

The caller supplies the native partition mark ID and the direction relative to the selected sketch normal. The mark ID is distinct from the marker's archive object index and the configuration's transferred atom ID. The writer returns the two new archive objects for the marker and end specification. Assigning a mark ID for a fresh complete part still requires the owning partition geometry.

## Native ownership

Preferred addresses refer to installed SOLIDWORKS `34.4.1.1011` `sldmodu.dll`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.

| Relative range | Native owner |
| --- | --- |
| +0–14 | The inactive chooser-presence, signed member at `+0x578` and action-array selector precede the positive partition selector. Calls include `0x4bb0ae76`, `0x4bb0afc9`, `0x4bb0b013` and `0x4bb0b0ab`. |
| +14–20 | The atom feature's partition pointer at `+0x3d0` is stored at `0x4bb0b0bb` through `0x4bb07930`. `moPMarkRecord_c` factory `0x4bb01860` installs vtable `0x4d17b928` in its constructor. Slot 5 `0x4bb19b30` calls `gcPMark_w::getId` at `0x4bb19b75` for a linked kernel mark. Without a link it files the signed cached member `+0x18` at `0x4bb19b6e`. |
| +20–72 | The ordinary atom route files three clear scalars beginning at `0x4bb0b0ca`, the guarded empty maps and ancillary results. Native stores include `0x4bb0b175`, `0x4bb0b1e4`, `0x4bb0b32f`, `0x4bb0b461` and `0x4bb0b616`. The admitted single-body route has thirteen zero words after the marker. |
| +72–82 | `moBodyFeature_c` at `0x4bb0c750` files the absent optional objects at `0x4bb0c7ce` and `0x4bb0c7fe`, the empty inline array at `0x4bb0c810` and the final signed zero at `0x4bb0c81c`. |
| +82–123 | The outer extrusion stores the new `moEndSpec_c` at `0x4bb109ea`. The end serializer at `0x4bb0f540` writes the three signed state words at `0x4bb0f60e–0x4bb0f62c`; the final one encodes direction. The two blind termination words follow the absent start pointer at `0x4bb0f647` and `0x4bb0f653`. Its active display is filed next. [End and display source](Display/EndOwner.md) |

The 123-byte interval advances the map from 293 to 296 in all eight P03 saves. It creates marker object 293 using the earlier marker class and defines end class 294 and object 295. The six observed native mark IDs are 7, 9, 11, 15, 19 and 23. The reverse archive changes the direction word while retaining the blind codes and one-sided profile start. The [resolved boss composition](BossResolve.md) continues through the terminal list.

Run `python -B re/solidworks/WriterResearch/VerifyBossEndOpen.py --read-only` in the Kit environment. All eight exact source saves agree with the complete production boss reader and independently measured direction. The report SHA-256 is `209520b1305788589d2d235f784f66d8ff8642b327d027ef43df22b9964a3343`. Hosted `CheckBossEnd` compares construction against the source interval and compares the full resulting map. The distance display, end tail, final extrusion return and parent footer remain separately owned.

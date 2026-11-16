# Generation 19000 rectangle line collection

`WriteRectLines` continues the [Origin proxy](OriginProxy.md) with the line count, the retained deleted line, and four authored perimeter lines. It takes permanent marks separately from creation IDs and emits local endpoints in their measured direction. The four edges must close on the same four point slots. The line collection retains its archive map.

## Native field ownership

These preferred virtual addresses use the same `34.4.1.1011` `sldmodu.dll` [pin as the corner writer](RectangleCorners.md).

| Field | Source |
| --- | --- |
| Count and inline order | `sgSketch` names `TotalLines` at `0x4c58fb3c`, writes the count at `0x4c58fb78` and calls the member's virtual serializer at `0x4c58fc53` in physical array order. Each inline line has an ordinary mode short. |
| Identity and state | The `sg2DEnt` serializer writes `PermMark`, `CreationId` and `RefCount` through the keys at `0x4c5815b4`, `0x4c581603` and `0x4c581817`. `sgEntHandle::isDeleted` at `0x4c5cbe22` tests bit 0 of `+0x54`. The retained slot has flags 5, while active members have flags 4. The deleted member uses the constructor's color, constraint status and type `(5,1,1)` at `0x4c3df1cc` through `0x4c3df1da`. The active branch uses the previously proved solved color and the explicit normal line weight. |
| Directed endpoints and contour | The `sgCurve` serializer at `0x4c58e9c0` files `End1` and `End2` through the short stores at `0x4c58ea4d` and `0x4c58eb02`. It files `isContour` and `isFlipped` at `0x4c58ebab` and `0x4c58ebfe`. With no scaling object, it writes the native `-1.0` at `0x4c58ec66`. |
| Line return | `sgLine` at `0x4c588d30` calls `sgCurve`. It omits the absent direction vector and writes its trailing short at `0x4c588d82`. |

All 14 saves retain a deleted slot before the four lines. It carries mark 0, creation ID −1, point slots `0→1`, no relations and contour 0. The independently measured perimeter excludes it. The physical archive order remains creation IDs `(1,2,3,4)` across P01 and P03. P01 assigns permanent marks `(1,2,3,4)` and P03 assigns `(1,4,3,2)` in that same order. The two arrays encode separate identities. The 56 perimeter lines match every independently measured directed endpoint and one axis-relation incidence each.

## Boundary and replay

Run `python -B re/solidworks/WriterResearch/VerifyAuthoredProfile.py --read-only` in the Kit environment. In every pinned discovery capture the count starts at byte 6906, the first line at 6910, and the fifth line returns at 7370. `line_replay_sha256` is `8fc41b75f4c3b0bd5e0e35a3285cc835f47f8e99a0716aa53722c26258fe97cc`. The hosted `CheckProfile` also compares the complete generated interval and preserved map. Value dimensions and subsequent relations still require constructive coverage and the finished part needs native edit and reopen verification.

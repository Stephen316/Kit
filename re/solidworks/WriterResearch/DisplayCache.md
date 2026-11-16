# Ordinary blind boss distance cache

The 92-byte span begins at `ReadCache` after the generated distance display placement. It ends immediately before the compact `moFavoriteHandle_c` class reference. All fields belong to `moDisplayDim_c` or its inline `CacheValueArray`. The four null object references consume no object slots. The evidence covers generation 19000, ordinary part display mode 201, the clear conditions on this path and the binary archive branch. [Placement tail](DisplayTail.md), [packaged reader](../../../src/convert/adapters/solidworks/Sketch/DisplayFields.py)

The source matches installed SOLIDWORKS build 34.4.1.1011. The SHA-256 values are `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99` for `sldmodu.dll`, `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6` for `sldmfcu.dll` and `3b82cfcaa13f099fca4f9741acbb11479dab7a6f20656052d5a750e61c6fee1e` for `sldmgu.dll`. The addresses below are preferred virtual addresses.

| Offset | Native field | Source and interpretation |
| --- | --- | --- |
| +0, +2 | Two absent compact `moPointRef_w` object pointers | `moDisplayDistanceDim_c` virtual slot 335 returns 1. With condition two clear the base store calls `0x4c267b00` for members `+0x580` and `+0x588` at `0x4c82ad5d` and `0x4c82ad6c`. Both start null at `0x4c888053–0x4c88805a`. |
| +4, +12 | Two zero doubles | Members `+0x5a0` and `+0x5a8` start at zero at `0x4c888193–0x4c88819a`. Their stores are `0x4c82ad7c` and `0x4c82ad8d`. |
| +20, +24 | Two absent inline point payloads | Each parent pointer must exist together with the associated point pointer before the serializer writes the signed-long 1 and point payload. Both conditions fail on the initialized empty branch, which writes signed-long 0 at `0x4c82adcc` and `0x4c82ae0b`. |
| +28, +30 | `TolPrec` and `AltTolPrec` unsigned words | Defaults `2, 2` from `0x4c8881cd` and `0x4c8881d7` are stored at `0x4c82ae4b` and `0x4c82aea3`. |
| +32 | Unsigned `Mask` | Store at `0x4c82aefa`. The fresh constructor writes `0x427` at `0x4c887f79` and sets bit 31 at `0x4c86d8ea`. |
| +36, +40 | Two absent object arrays | With conditions two and four clear `0x4c82af4a` and `0x4c82af5a` call `suObArray::serializePtr` for cleared members `+0xa58` and `+0xa60`. The null branch of `0x3c8df910` writes a signed-long 0 and returns without an array payload. |
| +44 | Empty wide `GroupName` | Null group member `+0xa68` takes the `0x4c82af6c` branch, which uses the empty wide literal at `0x4cd89460` and reaches the CString store at `0x4c82b022`. |
| +48, +50 | Absent `DimLengthUnit` and `DimAngleUnit` object pointers | The constructor clears `+0xaf8` and `+0xb00` at `0x4c888323` and `0x4c88832a`. Stores at `0x4c82b07a` and `0x4c82b0d2` call the typed object write operators. The inch control also uses these absent overrides. |
| +52 | Signed-long `BrokenStatus` | Unset state `-1` from `0x4c8881af`. Stored at `0x4c82b129`. |
| +56 | Double `BreakValue` in metres | Store at `0x4c82b182`. The ordinary update resolves the current dimension handle, obtains its scalar at `0x4c89e3d0` and writes it to `+0xad0` at `0x4c89e3d5`. |
| +64, +68, +72, +76 | Four unsigned `CacheValueArray` header words | The initializer at `0x4c887fcf–0x4c887fe2` allocates eight-byte elements, growth step 16 and strategy 1. Virtual slot 354 returns zero, so the initializer appends one element. The binary writer at `0x4bd02a90` stores element width, growth step, strategy and live count in that order. `suDynamicGetStats` at `0x31dff650` reads those allocation fields. The reader reconstructs allocation via `suDynArrayAllocSpecial`. |
| +80 | Single `CacheValueArray` double in metres | `updateDimension` writes the current display value into the first element at `0x4c89e413`. The binary writer at `0x4bd02b72` writes live count times element width. |
| +88 | Empty wide `FavoriteName` | The constructor initializes the CString at `0x4c86d33b` and the base store writes it at `0x4c82b3c5`. The signed-long field before this name is skipped when conditions one and four are clear. |

The two saved numbers agree with the typed driving dimension and the independent measured positive depth in all eight archives. They change from 0.010 m to 0.012 m on the depth edit. Plane, signed direction and document measurement units leave both copies at the positive length.

The native distance load path calls the setter at `0x4c896ba0` from `0x4c82f2c8` when its version, owning document and archive conditions permit it. The setter changes bit 25 at `0x4c896bae`. Fresh baseline A, Right-plane and negative-direction controls save the constructor mask `0x80000427`. Baseline B opens baseline A in a fresh process and rebuilds before the second save. The three edits and inch control use that reopened document. All five save `0x82000427`. The research writer uses the fresh constructor mask. The research reader returns whether the latter bit was saved, independently of the neutral model length. [Capture procedure](../../automation/PairedCaptures/SolidWorksAuthoring/SolidWorksCapture.cs)

The pinned receipt SHA-256 `f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94` binds each archive and its independent measurement file. The typed archive replay reached the following boundaries in `Contents/Config-0-ResolvedFeatures`. At every end the compact class reference uses class index 221 and creates favorite object 303. Before that reference the archive index remains 303 throughout the cache. [Pinned native receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json), [research codec](DisplayCache.py)

| P03 controls | Cache interval | SHA-256 of saved cache |
| --- | --- | --- |
| Baseline A | 14370–14462 | `054bb38a94a86149b941b8e43cb2fc1d56ff8734efd724783eeddc667dcaf00f` |
| Baseline B, width edit, height edit and inch display | 14598–14690 | `1aa8a58577afa30de33490dc640f849c285bf14d9c3e6dcd7f5a4a70785a6364` |
| Depth edit | 14598–14690 | `ee773386b3be64463cb9140fde10ade98868b28137dd8e4afb427ec8fdf4b458` |
| Right plane | 14440–14532 | `054bb38a94a86149b941b8e43cb2fc1d56ff8734efd724783eeddc667dcaf00f` |
| Negative direction | 14368–14460 | `054bb38a94a86149b941b8e43cb2fc1d56ff8734efd724783eeddc667dcaf00f` |

The scoped writer covers empty optional fields and one ordinary positive cache value. Populated optional references, text, unit overrides, alternate cache arrays and other generation routes remain outside this evidence. The next separate boundary is the 438-byte favorite and distance-display return path. Hosted execution of the new archive comparison and licensed native reopen remain pending. [Hosted boundary](../../../tests/Research/Archives/SolidWorksCacheVerify.py)

# P04 root archive context and material records

The native Config-0 read for P04 baseline A and YZ reaches the root dynamic-array field with archive context mask 0. Both sessions read one zero dword and advance four bytes without allocating an archive object. The strict offline walk uses that observed branch with the [native P04 map seed](P04ArchiveWalk.md#native-root-map) and reaches the material and model-data records in all eleven discovery captures.

## Licensed context witness

The two fresh, licensed SOLIDWORKS `34.4.1.1011` processes opened hash-verified read-only scratch copies and exited normally. The copies' native digests stayed unchanged. Independently hash the full runtime Config-0 buffer before accepting a trace.

| Capture | Runtime buffer bytes and SHA-256 | Context mask | Dynamic flag span | Archive map count before and after |
| --- | --- | ---: | ---: | ---: |
| Baseline A | 42,879, `e40cdd1e562a9e501a0a29ac252745d5c5cac6a7265ef924ccef4f5d078b34ab` | 0 | 2,708–2,712 | 49 |
| YZ | 42,949, `72ceb3ef354feed23fd70e5de87f05a44090972941ff81abbb5a504609a0ad46` | 0 | 2,706–2,710 | 49 |

Use execution hardware breakpoints at `sldmodu+0x10ed208`, `0x10ed248` and `0x10ed263` in an owned blank process. At the first hook, `r15` is the archive and `r12` is the model. Match the schema-1 `moPart_c` root and MO 19000, the runtime stream size, and the cursor after the version-2 alias sentinels `0xaaaaaaaa` and `0xbbbbbbbb`. Observe the context helper at `[rsp+0x28]`, its mask at +0x10, the generation at +0x7c0 and the method return in `eax`. The matched implementation at `sldmfcu+0x8c020` returns `mask & 0x80`. Join the later observations by the same model, archive and buffer. Disable all three probes after the completion hook so the read-only session can close normally. [Existing debugger trace method](../archive/Segmentation.md#2-the-productive-trace-and-the-segmentation)

The flag read at `sldmodu+0x10ed242` is conditional on a clear `0x80` return and MO generation at least `0x2778`. A set bit skips the field. A nonzero flag leads to the dynamic-array loader at `0x906300`. That loader reads a dword stride and, for nonzero stride, three header dwords and `stride × count` bytes. It requires a stride divisible by 24. Both P04 witnesses read a zero flag at the guarded cursor and take the short path. The subsequent XML serializer at `0x10f6330` consumes no bytes in load mode.

## Strict typed continuation

The eleven input blobs and the matching PE identities are pinned in the [archive walk evidence](P04ArchiveWalk.md#inputs). Seed indices 0–3 from the licensed root witness and resolve each reference only against an allocated entry of the matching kind. The loader structure derives the cursor for each capture. The two licensed traces establish the context branch, and the other nine files cross-check its guarded data layout offline.

1. After the unit owner reference, consume the zero optional external-owner byte from `sldmodu+0x10e9ce6`, two empty face-visualization counts from `sldmodu+0x10fdd20` and the curvature-display byte at `0x10ecb2e`. The curvature object reads five doubles and two dwords at `sldmfcu+0xa8e44`. The transformed-plane object reads six dwords at `sldmodu+0x15b1a1f`.
2. Follow the present bounding box through its ten double reads at `sldmgu+0x32820`. The matched `sldmgu.dll` SHA-256 is `3b82cfcaa13f099fca4f9741acbb11479dab7a6f20656052d5a750e61c6fee1e`. Consume the subsequent fixed fields and guard the two optional root lists as empty. Inline selector 2 enters the alias manager, whose `moAliasMap_c` invokes `swccu+0x1ad80`. Its empty count is a u16. The enclosing loader checks the two dword sentinels at `sldmodu+0x388540`.
3. Read the witnessed zero dynamic-array flag. Follow the fixed scalars and guarded empty fields, including shrink-wrap, defeature, the inline `suObList` and display-note dictionary. The animation-key sequence at `sldmodu+0x10edf6f` reads a dword count and two dwords per key. The next archive action reads a typed `moMBD3DPDFPublishCacheData_c` pointer at `0x10ee108`, which is null in the discovery files.
4. The part loader's next typed call at `sldmodu+0x10ee861` reads `gcXhatch_c`. Its `sldmfcu+0x114cc2` loading path reads one CString, two doubles and six version-gated dwords. The next part call at `sldmodu+0x10ee905` reads `moMaterial_c`, whose slot 5 at `0x10e2460` reads `moDensityParameter_c` with no additional material scalars in MO 19000.
5. The density routine at `sldmodu+0x1035bd0` reaches the node's lightweight serializer at `0x10389e0`. Its two name-pointer slots are null in the discovery files. Four node dwords and the framed CString lie between those slots. The density tail reads one double and a zero optional-density byte on the witnessed clear `0x80` branch. The root then reads `uoModelData_c`. Its restore method at `0x1278730` skips the legacy count at `0x12787b5` for MO generation `0x17d` and later. On the MO 19000 path, it reads a null scene pointer at `0x127881d` and a dword at `0x1278887`.

| P04 capture group | Hatch definition | Material definition | Density definition | Model-data definition | Cursor after model data |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline A | 2,816 | 2,924 | 2,942 | 3,001 | 3,026 |
| Baseline B, six edits and inch display | 2,854 | 2,962 | 2,980 | 3,039 | 3,064 |
| YZ and through-all | 2,814 | 2,922 | 2,940 | 2,999 | 3,024 |

All eleven reach 34 typed archive rows. The hatch, material, density and model-data class/object pairs are 49/50, 51/52, 53/54 and 55/56. The next part call is the inline body-visualization loader at `sldmodu+0x10eea6f`. Continue the typed root fields from that point before entering the later atom and sketch records.

# Configuration units table

The part stores the schema-1 `moUnitsTable_c` as the next owned object after its [visual properties](ConfigVisual.md). The table uses class slot 8 and object slot 9. Its 16 direct members occupy distinct objects in native initialization order. The primary length member also owns a second length object. That second object reuses the registered class, owns a null child, and precedes the other 15 members. `moUnitComponent_c` begins with next index 43 and allocates class 43 and object 44.

## Native field authority

The [pinned 34.4.1.1011 sldmfcu image](CmgrVisual.md#version-and-ownership) exposes the following preferred virtual addresses. `moUnitsTable_c::iCreateDefaultUserUnits` at `0x3c8fc210` creates missing members in the 16-class order used by the constructor. The table serializer at `0x3c8fb980` calls the object-array serializer `0x3c8dd4c0` on the modern branch, with a compact count and typed member pointers. The ordered classes and exact archive slots were also checked by the independent bounded `FindEntry` walk.

`moUserUnits_c::Serialize` at `0x3c91cd00` writes the 62-byte base body using scalar operators at `0x3c91cd3d` through `0x3c91cdd7`. Object member offsets in filed order are `0xc`, `0x10`, `0x18`, `0x20`, `0x24`, `0x30`, `0x28`, `0x6c`, `0x70`, `0x74`, `0x88`, `0x7c`, and `0x8`. The widths in the same order are `i32, i32, f64, i32, i32, f64, i32, i32, i32, i32, f64, u16, i32`. The base constructor at `0x3c917d60` initializes `+0x88` to zero. Edited saves exhibit distinct values at this member. It is passed as `PreviousLength` because in the controls it can preserve the preceding numeric edit value. Its full update rules and runtime unit interpretation remain open. In the P01 height edit the current value reaches 23 while the field stays 20. In the P03 depth edit the current value reaches 12 while the field stays 10. The inch saves carry 23 and 12 respectively. The previous numeric value is therefore an explicit caller input alongside, and independent of, the display settings.

The length serializer at `0x3c91cb30` stores the `getLengthUnit` member `+0xb0` and the `getDualUnit` pointer `+0xb8`. The dual allocator at `0x3c925ae0` passes its own format inputs to the length constructor `0x3c916330`. The measured nested record has selector 3. It is present under both the saved metric and inch profiles. The primary formatter has increment `0.1` and option `+0x20` = 4 in the controls. The fallback constructor call at `0x3c8fc2a2` passes 10 for that option. The codec validates the observed primary, dual, and common formatter shapes and supports the two measured complete display profiles. These restrictions preserve the controlled settings rather than assigning universal constructor defaults.

The shared derived serializers at `0x3c91c860` and `0x3c91cab0` store a 16-bit selector for angle, unit system, force, power, energy, and time. Density uses its own serializer at `0x3c91c8c0`, with `u16` volume and mass from `+0xc0` and `+0xc4`, zero byte for absent optional length object, `u16` legacy volume from `+0xc8` and `i32` legacy mode from `+0xcc`. The named getters at `0x3c7e9440`, `0x3c7e9f00`, `0x3c927bf0`, and `0x3c767f80` independently distinguish those members. `setUseOldVolUnit` at `0x3c7b57b0` directly sets the mode. The measured value is zero. Display profiles retain their individual selectors, including mass and volume, as the `UnitDisplay` input.

## Replay

```sh
python re/solidworks/WriterResearch/VerifyConfigUnits.py --read-only
```

Each of the six P01 and eight P03 receipt-pinned variants has a 1,487-byte table including its class tag. The typed reader ends at offset 2412, 2414 or 2452 according to the earlier root title length. Five table digests distinguish the seven shared metric baselines and controls, two P01 metric edits, P01 inch edit, three P03 metric edits, and P03 inch edit. The replay SHA-256 is `8c4195e8660da7a1751a8c1c3d5c4e35ad53b2e58bfa6e8d9137fd36b3999a37`. Its input includes each asset hash, table boundaries, archive counters, separate display settings and prior value, and the table digest in receipt order.

Hosted `CheckConfigUnit` will construct the unit table with the inherited archive namespace, compare exact bytes and remaining class allocations, and verify the same report digest. The current replay is read-only. Construction continues with the [model component and plane presentation](ConfigModelView.md). No native acceptance is claimed.

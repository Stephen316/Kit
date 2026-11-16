# Ordinary blind boss display placement tail

The generation 19000 distance display continues after the clear optional-point mask of its owned `ParallelPlaneDistanceDim_c`. The enclosing `moDisplayDim_c::Serialize` stores the next 240 bytes in mode 201 with condition one clear. `ReadParDepthMut` consumes the child and these enclosing fields. The following `ReadCache` starts at the enclosing end. The matched installed `sldmodu.dll` SHA-256 is `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. Addresses below are preferred virtual addresses. [Owned distance boundary](DisplayHandle.md#constructing-the-ordinary-owned-distance), [packaged depth reader](../../../src/convert/adapters/solidworks/Resolved/BossDepth.py)

| Offset from child end | Stored fields | Native store |
| --- | --- | --- |
| +0, +2, +4 | `u16` arrowheads and position | `0x4c82a455`, `0x4c82a4ad`, `0x4c82a505` |
| +6, +10, +14, +18 | Four empty wide CStrings for prefix, suffix and both callouts | `0x4c82a55d`, `0x4c82a5b5`, `0x4c82a60d`, `0x4c82a665` |
| +22, +46 | Three-double text direction and double text position | `0x4c82a6d5`, `0x4c82a736` |
| +54, +62, +70 | Double witness length, radius and extra leader distance | `0x4c82a78f`, `0x4c82a7e8`, `0x4c82a841` |
| +78, +102, +126, +150, +174 | Three-double reference points one, one-b, two, two-b and three | `0x4c82a8b1`, `0x4c82a909`, `0x4c82a961`, `0x4c82a9b9`, `0x4c82aa11` |
| +198 | Clear signed-long optional extra reference flag | `0x4c82aa26` |
| +202 through +214 | Seven `u16` fields for witness, leader and arrow masks, color, precision, alternate precision and SmartArrows | `0x4c82aaa1`, `0x4c82aaf9`, `0x4c82ab51`, `0x4c82aba9`, `0x4c82ac01`, `0x4c82ac59`, `0x4c82acb1` |
| +216 | Three-double reference direction | `0x4c82ad21` |

The ordinary initialization at `0x4c887f40` supplies empty labels, position 0, text position 0.5, radius 0, extra leader distance −1, empty masks, color 5 and SmartArrows 2. It clears optional reference member `+0xa50`. Its populated branch stores additional point, vector and scalar data and remains unqualified. Both arrowheads are assigned from the document detail field `+0x6c` at `0x4c888422–0x4c88842b`. Alternate precision is assigned from detail field `+0x84` at `0x4c8884e7–0x4c8884f4`. The ordinary precision branch obtains its value through the virtual call at `0x4c888516`. The encoder takes these three settings explicitly and bounds them to the witnessed combination `(0, 2, 2)`. [Research encoder](DisplayTail.py)

Reference and text directions use the supplied frame and the measured profile tangent and normal. The distance placement code reaches the handle points, forms the active vector at `0x4c8ab667`, applies its native transform at `0x4c8ab69b–0x4c8ab6b0` and assigns each duplicated reference point at `0x4c8abb26–0x4c8abb50`. The text direction setter is `0x4c896090`. In the bounded captures, the first pair and third point are local zero. The second pair is the signed reference direction times positive depth in metres. The negative Front control retains negative zeros in the reference direction and positive zeros in its point coordinates. The Right-plane control separately changes the reference axis and text direction.

The witness scalar follows annotation placement. The path at `0x4c8af25b–0x4c8af294` forms a placement delta and takes its dot product before dispatching the witness setter. The setter at `0x4c897340` stores the scalar in display member `+0x8b0`. The measurements independently report the profile and boss depth but omit the annotation point that produced this projection. The encoder therefore takes an explicit finite signed witness projection in metres. The exact initial default placement and its floating-point rounding remain open.

The native receipt SHA-256 `f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94` binds each of the eight archives and their independent measurements. A read-only walk checked the 240-byte span in all eight, verified the next cursor at the actual cache reader entrance and corroborated the source-derived fields and signed axes. The saved witness was `0.007999999999999998` on the Front controls and negative zero on the Right-plane control. [Pinned receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

| P03 controls | SHA-256 of enclosing span |
| --- | --- |
| Baselines A/B, width edit, height edit and inch display | `652000acb6cdb0b430ecb6a31186a4f0583f4344ca528cb9c739e3b823e71329` |
| Depth edit | `e333dc48ec5302ef35ecfed6a3d6d4ef3d458cdf5e1206808c2e521f7a6f60fd` |
| Right plane | `2c544ba10037553953c246fe22d14fa4bb8d73da3ba669c46d73c2c471bce56a` |
| Negative direction | `f90ea93f612853b758915afc9469c16dcaa06339f9ec7751028ca97bd8e43cef` |

Hosted verification extends the existing eight archive cases. It compares the other 232 bytes to each pinned span, checks a distinct caller-supplied witness and gives the packaged reader the generated handle, distance child and placement fields together. The cache has a separate scoped research encoder. The closing favorite, full model writing and licensed reopen remain open. [Hosted boundary](../../../tests/Research/Archives/SolidWorksDistVerify.py), [distance cache](DisplayCache.md)

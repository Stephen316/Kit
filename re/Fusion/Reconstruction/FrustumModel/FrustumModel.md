# Independent circular frustum geometry

## Scope

`GeometryCodec/Frustum` constructs one closed circular frustum directly from four semantic inputs: bottom radius, top radius, axial height and bottom-center position. All input lengths use millimetres. Both radii and height must be positive; the axis is +Z. Equal radii produce the cylinder limit. The writer does not read a source archive, native record payload, template, research fixture or CAD runtime.

The outputs are standalone ASM 23200 SMT and SMB solids. This feature does not add tapered feature history to `DocumentCodec`, author an apex, admit arbitrary cone orientations, or claim general cone/BRep import. It reuses the existing explicitly authored cylinder topology because the two positive circular rims have the same manifold adjacency.

## Evidence

The native controlled source is `re/Fusion/Study/extents-f0f33a9a605f/taper.f3d`, SHA-256 `d5e776fa897782747e699b1ed366f9bf51bf6652c19a21001676651c2cd4118f`. Its accompanying `ground_truth.json` records a 7-degree positive taper, a 17 mm axial extent and a 12.087337535349378 mm upper radius. The lower radius is 10 mm. The source history part is `FusionAssetName[Active]/Breps.BlobParts/BREP.299112e4-f409-4233-89b9-e59b88e80317.smbh`, SHA-256 `4922e923b5fc1515732922c843edb42eec2b92ba5243413027334880ce2475e1`.

[ConeEvidence.json](ConeEvidence.json) contains the selected typed native records and the ground truth. [InspectCone.py](InspectCone.py) regenerates that read-only report from the raw archive. It does not import production modules or call a CAD runtime.

An earlier version also cited static inspection of the installed ASM kernel for these fields. That material was removed. The field sequence and the evaluation below rest on the InventorLoader parser, the taper ground truth and the native acceptance results under Verification.

The independent [InventorLoader `SurfaceCone` parser](https://github.com/jmplonka/InventorLoader/blob/master/Acis.py) corroborates the ellipse, sine, cosine, length-scale and sense field sequence. Its apex construction uses the same radius and angle relationship. No upstream implementation code was copied.

## Persisted cone fields

Field indices below include the three common entity-prefix fields. Positions, dimensional vectors and the parameter scale use centimetres in the binary writer and millimetres in the text writer. Axis vectors, trigonometric values and ratios remain dimensionless.

| Index | Field | Independent authored value |
| --- | --- | --- |
| 0–2 | Attribute pointer, entity identifier, geometry-owner pointer | Null, −1, null |
| 3 | Base ellipse center | Caller bottom center |
| 4 | Ellipse axis | `(0, 0, 1)` |
| 5 | Major ellipse vector | `(bottomRadius, 0, 0)` |
| 6 | Minor/major ratio | `1` |
| 7–8 | Base ellipse optional interval limits | Both absent (`I`) |
| 9 | Signed sine of cone semi-angle | `(topRadius-bottomRadius)/slantLength` |
| 10 | Cosine of cone semi-angle | `height/slantLength` |
| 11 | Longitudinal parameter scale | `bottomRadius` |
| 12 | Surface sense | Forward |
| 13–16 | Optional surface parameter limits | All absent (`I`) |

Here `slantLength = hypot(height, topRadius-bottomRadius)`. Positive sine expands the radius along +Z, negative sine contracts it, and zero sine gives a cylinder. The authored cosine is positive.

For the circular, forward-sense profile, let `b` be the base center, `r` the base radius, `s` the parameter scale, and `a` the semi-angle. The evaluation reduces to:

```text
p(u,v) = b + (r + u*s*sin(a)) * (cos(v), sin(v), 0)
           + (0, 0, u*s*cos(a))

z = u*s*cos(a)
radius(z) = r + z*sin(a)/cos(a)
u_top = height / (s*cos(a))
```

The third scalar after the ellipse limits is a longitudinal scale, not a top radius. Its equality to the lower radius is the chosen native-compatible parameterization. The physical cone can use another positive parameter scale without changing its locus, but that parameterization is outside this writer's contract.

## Topology and orientation

The fresh graph contains 26 records: one ASM header, one body, one lump, one shell, three faces, four loops, four coedges, two edges, one cone surface, two cap planes, two vertices, two circular ellipse curves and two points. The side face has two single-edge boundary loops; each cap has one single-edge loop. Paired coedges reference the same edge and have complementary senses.

The upper cap is forward and the lower cap reversed. Both cap carrier planes have +Z normals. Both authored circular edge carriers also use +Z; their seam vertex is at angular parameter −π, with the closed edge spanning −π to +π. The side's upper coedge is reversed and its lower coedge forward. The top and bottom cap coedges take the complementary orientation.

The native tapered-extrusion source uses −Z for its upper circular carrier. That is a different valid curve parameterization with associated topology senses; copying only that axis would invalidate the authored orientation contract. The independent graph derives each rim and seam point from the requested dimensions and keeps its own coherent orientation.

## Numerical and format boundaries

The semantic model rejects nonfinite dimensions, Boolean dimensions, nonpositive radii or height, underflow to zero during millimetre-to-centimetre conversion, overflowing slant length, a zero representable cosine, a taper lost through floating-point conversion, and translated bounds whose difference from the center/height disappears at either unit scale. These checks establish representable coordinates; they do not promise native kernel tolerance acceptance for every representable positive value.

The SMT writer uses text header `23200 0 2 2` and native millimetre unit value `1`. The SMB writer uses `ASM BinaryFile8`, 64-bit record references and the existing centimetre-aware field encoder. Both create the same semantic graph and explicit terminal marker. Standalone metadata uses caller-supplied `GeometryStamp`.

## Verification

Remote integration coverage under `tests/convert/formats/FusionCodec/Geometry/Frustum` writes and reopens complete SMB files, independently decodes cone/rim geometry, verifies pointer closure and partner senses, checks the radius law and volume, checks SMT dimensional fields, rejects invalid inputs before writing a file, rejects trailing binary data, and reconstructs the native 7-degree taper dimensions without using its record payloads in the writer.

No local tests or product execution were run by the implementation agent. Scoped Black, Ruff, mypy, Pyright and repository steering checks passed. Pyright also reported three pre-existing unrecognized configuration keys; it reported no source errors or warnings. Remote integration execution is pending publication of this revision.

The parent task generated both formats directly with the production API and exercised Fusion 2706.1.17. All six outputs passed native load, solid topology, volume, surface area, center of mass and bounding-box assertions, followed by F3D save and reopen with the same measurements. Every case contained one solid, three faces, two edges and two vertices. The oracle closed all controlled documents.

| Case | Bottom/top radius and height (mm) | Base center (mm) | Expected volume (cm³) | Native acceptance |
| --- | --- | --- | --- | --- |
| Expanding | 10 / 14 / 17 | `(20, -30, 5)` | 7.761828249469183 | SMT and SMB, including save/reopen |
| Contracting | 14 / 8 / 23 | `(-12, 7, -4)` | 8.95982224803809 | SMT and SMB, including save/reopen |
| Cylinder limit | 9 / 9 / 11 | `(1, 2, 3)` | 2.799159054348505 | SMT and SMB, including save/reopen |

[Preparation.json](../../LocalOracle/Frustums/Preparation.json) binds the semantic inputs, independently calculated expected measurements and six source hashes. [NativeAcceptance.json](../../LocalOracle/Frustums/NativeAcceptance.json) records observed measurements, accepted status and saved F3D hashes. The source SHA-256 values for the expanding, contracting and equal-radius SMB files are respectively `f65b48d956ffd756e318f91f5e624fd5984b2174bbc8de290d1955d8e4e5fff3`, `d6d9c703a36839a5e916db75d4324acc9caa92eccff957e69eadcedb866ee8ef` and `3b6bee364165241e5a3a8b66820f04722c26953cfe7191dd8ed34640d8583ac2`. This establishes standalone geometry acceptance for the stated profiles, not tapered parametric history or unrestricted cone conversion.
